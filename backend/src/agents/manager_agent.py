import asyncio
import os
import uuid
import httpx
import click
import uvicorn
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List 

from a2a.types import (
    AgentCard, AgentCapabilities, AgentSkill, TaskState, TextPart,
    SendMessageRequest, MessageSendParams, GetTaskRequest, TaskQueryParams
)
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.client import A2AClient 
from a2a.types import GetTaskSuccessResponse 

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found. Please check your .env file.")

EXPERT_AGENT_URL = os.getenv("EXPERT_AGENT_URL", "http://localhost:10007/")


class ManagerChatResponse(BaseModel):
    chat_reply: str = Field(description="The direct, conversational reply to the user's latest message, considering the chat history.")


manager_agent = Agent(
    model='mistral:mistral-large-latest',
    result_type=ManagerChatResponse,
    system_prompt="""You are a friendly and highly capable sales manager for AI solutions.
    You will receive a CHRONOLOGICAL conversation transcript.
    Your primary goal is to respond to the LATEST user message (at the end of the transcript), using prior messages for crucial context.
    - If the user asks for product information, provide it concisely (consult expert if needed).
    - If the user expresses interest in a specific product, focus on that product.
    - If you have previously offered a demo and the user responds positively (e.g., "Yes", "Okay", "Sounds good"), DO NOT re-offer the demo or generic product info. Instead, proceed to confirm demo details (product, date, time).
    - If the user provides scheduling information (e.g., "Vision AI demo please, 15 august"), acknowledge the product and date, and ask for any missing information (like time) or confirm. For example: "Great! Vision AI demo for August 15th. What time would work for you?"
    - If the user asks a question you answered previously in a similar way, try to provide a more specific or slightly different angle, or ask clarifying questions if their intent isn't clear from the history.
    - Maintain a conversational, helpful, and concise chat style. Avoid email formalities.
    - If the LATEST user message is unclear or very short (e.g. "ok", "yes"), refer to your PREVIOUS message to understand the context of their affirmation.
    """
)


class ManagerAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        print("Manager Agent: Received message")
        task_updater = TaskUpdater(
            event_queue, context.task_id, context.context_id)

        try:
            if event_queue.is_closed():
                print("Manager Agent Warning: Event queue is closed, creating new one...")
                event_queue = EventQueue()
                task_updater = TaskUpdater(
                    event_queue, context.task_id, context.context_id)

            await task_updater.submit() 
            await task_updater.start_work() 

            conversation_transcript = context.message.parts[0].root.text # Теперь это полный транскрипт
            print(f"Manager Agent: Received conversation transcript (last 250 chars): ...{conversation_transcript[-250:]}")

            expert_info = await self._consult_expert(conversation_transcript)

            manager_prompt = f"""
            Here is the conversation transcript (chronological, ending with the latest user message):
            <transcript>
            {conversation_transcript}
            </transcript>

            Here is information from our company expert, if relevant to the latest user message:
            <expert_information>
            {expert_info}
            </expert_information>

            Your task: Based on the SYSTEM PROMPT and the information above, craft a helpful and concise chat response to the LATEST user message in the transcript.
            Pay close attention to the LATEST user message and your own previous message if the user's reply is short.
            If the user is trying to schedule a demo (e.g., mentioned a date or product for demo), focus on confirming the details.
            """

            final_response_text = ""
            try:
                print("Manager Agent: Requesting response from Pydantic AI...")
                manager_result = await manager_agent.run(manager_prompt)
                final_response_text = manager_result.output.chat_reply
                print(f"Manager Agent: Pydantic AI responded: {final_response_text[:100]}...")

            except Exception as ai_error:
                print(f"Manager Agent: Error from Pydantic AI: {ai_error}")
                fallback_message = "I'm having a little trouble processing that. Could you please rephrase or try again? "
                if "Expert is temporarily unavailable" not in expert_info and "Error communicating with expert" not in expert_info and expert_info and "Could not get a detailed response" not in expert_info and "Error creating task for expert" not in expert_info:
                    fallback_message += f"Our expert provided some notes: \"{expert_info[:50]}...\". "
                final_response_text = fallback_message
                print(f"Manager Agent: Using fallback response: {final_response_text[:100]}...")
            
            print(f"Manager Agent: Sending final response to client: {final_response_text[:200]}...")
            await task_updater.update_status(
                TaskState.completed,
                message=task_updater.new_agent_message(
                    parts=[TextPart(text=final_response_text)]
                ),
            )

        # ... (обработка ошибок остается без изменений) ...
        except Exception as e:
            print(f"Manager Agent: Error in ManagerAgentExecutor: {e}")
            import traceback
            traceback.print_exc()
            try:
                if event_queue.is_closed():
                    event_queue = EventQueue() 
                task_updater = TaskUpdater( 
                    event_queue, context.task_id, context.context_id)
                await task_updater.update_status(
                    TaskState.failed,
                    message=task_updater.new_agent_message(
                        parts=[
                            TextPart(text=f"Unfortunately, an error occurred while processing your request: {str(e)}")]
                    ),
                )
            except Exception as update_error:
                print(
                    f"Manager Agent: Critical error when updating task status to failed: {update_error}")


    async def _consult_expert(self, conversation_transcript: str) -> str:
        """Consults the company expert via A2A, providing the conversation transcript."""
        try:
            expert_query = f"""
            The sales manager is in a conversation. Here is the CHRONOLOGICAL transcript:
            <transcript>
            {conversation_transcript}
            </transcript>

            Based on the LATEST user message in this transcript, please provide CONCISE, factual information
            about our products (especially Document Analyzer and Vision AI) IF AND ONLY IF the latest user message
            explicitly asks for product details or implies a need for clarification on product features.
            If the latest user message is about scheduling, confirmation, or something not requiring deep product data,
            simply state: "User is [scheduling/confirming/etc.]. No detailed product information seems immediately necessary for this turn."
            Focus on providing information useful for the MANAGER to answer the LATEST user query.
            Do not write a reply for the end customer.
            """
            print(f"Manager Agent: Sending request to expert with transcript (last 150 chars): ...{expert_query[-250:]}")

            async with httpx.AsyncClient(timeout=60.0) as client: 
                try:
                    expert_agent_client = await A2AClient.get_client_from_agent_card_url(
                        client, EXPERT_AGENT_URL
                    )
                    # print(f"Manager Agent: Successfully got A2A SDK client for expert. Agent URL: {expert_agent_client.url}")

                    send_request_id = f"send-req-manager-to-expert-{uuid.uuid4()}"
                    send_request = SendMessageRequest(
                        id=send_request_id, 
                        params=MessageSendParams(
                            message={
                                'messageId': f"msg-manager-to-expert-{uuid.uuid4()}",
                                'role': 'user',
                                'parts': [{'type': 'text', 'text': expert_query}],
                            }
                        )
                    )
                    response = await expert_agent_client.send_message(send_request)
                    # print("Manager Agent: expert_agent_client.send_message call completed.")

                    # ... (остальная часть метода _consult_expert без значительных изменений, кроме логов) ...
                    if hasattr(response.root, "result"):
                        expert_task = response.root.result
                        # print(f"Manager Agent: Task created for expert: {expert_task.id}, status: {expert_task.status.state}")

                        max_attempts = 40 
                        for attempt in range(max_attempts):
                            await asyncio.sleep(0.5)
                            get_task_request_id = f"get-task-req-expert-{uuid.uuid4()}" 
                            get_resp = await expert_agent_client.get_task(
                                GetTaskRequest(id=get_task_request_id, params=TaskQueryParams(id=expert_task.id)) 
                            )
                            if isinstance(get_resp.root, GetTaskSuccessResponse):
                                expert_task = get_resp.root.result
                                if expert_task.status.state in (TaskState.completed, TaskState.failed, TaskState.canceled, TaskState.rejected):
                                    break
                            else:
                                print(f"Manager Agent: Error getting expert task status: {get_resp.root}")
                                break 

                        if expert_task.status.state == TaskState.completed and expert_task.status.message and expert_task.status.message.parts:
                            expert_response_text = expert_task.status.message.parts[0].root.text
                            print(f"Manager Agent: Received response from expert: {expert_response_text[:100]}...")
                            return expert_response_text
                        else:
                            error_detail = f"status: {expert_task.status.state}, message: {expert_task.status.message}"
                            # print(f"Manager Agent: Failed to get a detailed response from expert. {error_detail}")
                            return f"Expert did not provide a detailed response. {error_detail}" # Более нейтрально
                    else:
                        error_detail = f"response: {response.root}"
                        # print(f"Manager Agent: Error creating task for expert. {error_detail}")
                        return f"Could not create task for expert. {error_detail}" # Более нейтрально

                # ... (обработка ошибок в _consult_expert без изменений) ...
                except httpx.ConnectError as conn_error:
                    print(f"Manager Agent: Connection error with expert: {conn_error}")
                    return "Expert is temporarily unavailable. Using basic product information."
                except Exception as task_error: 
                    print(f"Manager Agent: Error during expert task operation: {task_error}")
                    import traceback
                    traceback.print_exc()
                    return f"Error getting information from expert: {str(task_error)}. Using basic information."
        except Exception as e:
            print(f"Manager Agent: Error during consultation with expert: {e}")
            import traceback
            traceback.print_exc()
            return f"Error communicating with expert: {str(e)}. Using basic information."
            
    # ... (метод cancel и main без изменений) ...
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        print(f"Manager Agent: Received cancellation request for task {context.task_id}")
        try:
            task_updater = TaskUpdater(
                event_queue, context.task_id, context.context_id)
            await task_updater.update_status(TaskState.canceled)
            print(f"Manager Agent: Task {context.task_id} cancelled.")
        except Exception as e:
            print(f"Manager Agent: Error cancelling task {context.task_id}: {e}")

@click.command()
@click.option('--host', default='0.0.0.0', help='Host for Uvicorn server (usually 0.0.0.0 in Docker)') 
@click.option('--port', default=10008, help='Port for Uvicorn server')
def main(host: str, port: int):
    agent_executor = ManagerAgentExecutor()
    public_agent_url = os.getenv("PUBLIC_AGENT_URL")
    if not public_agent_url:
        if host == '0.0.0.0':
            print("WARNING (Manager Agent): Uvicorn is running on 0.0.0.0, but PUBLIC_AGENT_URL is not set.")
            print(f"AgentCard will use http://manager-agent:{port}/ as a fallback, but it's better to set PUBLIC_AGENT_URL explicitly.")
            public_agent_url = f'http://manager-agent:{port}/' 
        else:
            public_agent_url = f'http://{host}:{port}/'
    print(f"Public URL for AgentCard (Manager Agent): {public_agent_url}")
    agent_card = AgentCard(
        name='Sales Manager Chat Agent (Context-Aware)', 
        description='Friendly sales manager for AI solutions. Chats with clients, answers questions, and helps choose products, considering conversation history.',
        url=public_agent_url, 
        version='1.1.1', # Increment version
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        authentication={"schemes": ["basic"]},
        skills=[
            AgentSkill(
                id='client_contextual_chat', 
                name='Client Contextual Chat Communication',
                description='Conducting dialogue with clients in chat, providing information about AI Solutions Corp. products, considering conversation history.',
                tags=['sales', 'chat', 'communication', 'context-aware'],
            ),
            AgentSkill(
                id='expert_contextual_query', 
                name='Expert Contextual Information Query',
                description='Requesting additional information from the company\'s internal expert for more accurate answers, providing conversation context.',
                tags=['consultation', 'expertise', 'internal', 'context-aware'],
            ),
        ],
    )
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore()
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    print(f"Starting Uvicorn for Sales Manager Chat Agent (Context-Aware) on {host}:{port}") 
    print(f"Expecting company expert at {EXPERT_AGENT_URL}")
    uvicorn.run(a2a_app.build(), host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()