import asyncio
import os
import uuid
import httpx
import click
import uvicorn
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic import BaseModel, Field

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
from a2a.client import A2AClient # Убедимся, что A2AClient импортирован
from a2a.types import GetTaskSuccessResponse # Убедимся, что GetTaskSuccessResponse импортирован

load_dotenv()

if not os.getenv("MISTRAL_API_KEY"):
    raise ValueError("MISTRAL_API_KEY not found. Please check your .env file.")

EXPERT_AGENT_URL = os.getenv("EXPERT_AGENT_URL", "http://localhost:10007/")


class ManagerChatResponse(BaseModel):
    chat_reply: str = Field(description="The direct, conversational reply to the user's message.")


manager_agent = Agent(
    model='mistral:mistral-large-latest',
    result_type=ManagerChatResponse,
    system_prompt="""You are a friendly and professional sales manager for AI solutions.
    Your goal is to understand the customer's needs based on their message, provide relevant information
    (possibly after consulting an expert), and guide them towards a product demonstration.
    Respond in a conversational, helpful, and concise chat style.
    Avoid email formalities like salutations or signatures. Just provide the chat message.
    If the user asks something unrelated to AI solutions, politely steer the conversation back or state you can only help with AI solutions."""
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

            await task_updater.submit() # Добавляем await
            await task_updater.start_work() # Добавляем await

            user_query_text = context.message.parts[0].root.text
            print(f"Manager Agent: Received query from user: {user_query_text[:100]}...")

            expert_info = await self._consult_expert(user_query_text)

            manager_prompt = f"""
            A customer has sent the following chat message:
            "{user_query_text}"

            Information from our company expert (use this to enhance your response if relevant, otherwise rely on your general knowledge):
            "{expert_info}"

            Your task is to craft a helpful and concise chat response:
            1. Acknowledge the customer's query.
            2. If expert information is provided and relevant, integrate it naturally into your response to explain how our AI solutions (like Document Analyzer or Vision AI) can address their needs.
            3. If appropriate, enthusiastically suggest scheduling a demonstration of our products.
            4. Keep your response conversational, friendly, and directly address the user's message.
            5. Do NOT use any email formatting, salutations (like "Dear User"), or closing signatures (like "Best regards"). Just provide the direct chat message.
            """

            final_response_text = ""
            try:
                print("Manager Agent: Requesting response from Pydantic AI...")
                manager_result = await manager_agent.run(manager_prompt)
                final_response_text = manager_result.output.chat_reply
                print(f"Manager Agent: Pydantic AI responded: {final_response_text[:100]}...")

            except Exception as ai_error:
                print(f"Manager Agent: Error from Pydantic AI: {ai_error}")
                fallback_message = f"Thank you for your question: \"{user_query_text[:50]}...\". "
                if "Expert is temporarily unavailable" not in expert_info and "Error communicating with expert" not in expert_info and expert_info and "Could not get a detailed response" not in expert_info and "Error creating task for expert" not in expert_info:
                    fallback_message += f"Our expert suggested: \"{expert_info[:70]}...\". "
                
                fallback_message += "Our AI solutions, like Document Analyzer for document processing and Vision AI for monitoring, might be helpful for you. Would you like to learn more or schedule a demo?"
                final_response_text = fallback_message
                print(f"Manager Agent: Using fallback response: {final_response_text[:100]}...")
            
            print(f"Manager Agent: Sending final response to client: {final_response_text[:200]}...")
            # Добавляем await для асинхронной функции
            await task_updater.update_status(
                TaskState.completed,
                message=task_updater.new_agent_message(
                    parts=[TextPart(text=final_response_text)]
                ),
            )

        except Exception as e:
            print(f"Manager Agent: Error in ManagerAgentExecutor: {e}")
            import traceback
            traceback.print_exc()
            try:
                if event_queue.is_closed():
                    event_queue = EventQueue() 
                task_updater = TaskUpdater( 
                    event_queue, context.task_id, context.context_id)
                # Добавляем await для асинхронной функции
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

    async def _consult_expert(self, user_query_text: str) -> str:
        """Consults the company expert via A2A to get information for the chat."""
        try:
            expert_query = f"""
            A customer asked in chat:
            "{user_query_text}"

            Please provide brief information about our products (especially Document Analyzer and Vision AI, if relevant)
            that will help me answer the customer. I need the essence: features, benefits.
            The response should be in the form of facts/theses that I can use in the chat.
            Do not write a full reply to the customer, just the information for me.
            """
            print(f"Manager Agent: Sending request to expert with text: {expert_query[:100]}...")

            async with httpx.AsyncClient(timeout=60.0) as client: 
                try:
                    expert_agent_client = await A2AClient.get_client_from_agent_card_url(
                        client, EXPERT_AGENT_URL
                    )
                    print(f"Manager Agent: Successfully got A2A SDK client for expert. Agent URL: {expert_agent_client.url}")

                    send_request_id = f"send-req-manager-to-expert-{uuid.uuid4()}"
                    send_request = SendMessageRequest(
                        id=send_request_id, # Добавили id
                        params=MessageSendParams(
                            message={
                                'messageId': f"msg-manager-to-expert-{uuid.uuid4()}",
                                'role': 'user',
                                'parts': [{'type': 'text', 'text': expert_query}],
                            }
                        )
                    )
                    response = await expert_agent_client.send_message(send_request)
                    print("Manager Agent: expert_agent_client.send_message call completed.")

                    if hasattr(response.root, "result"):
                        expert_task = response.root.result
                        print(f"Manager Agent: Task created for expert: {expert_task.id}, status: {expert_task.status.state}")

                        max_attempts = 40 
                        for attempt in range(max_attempts):
                            await asyncio.sleep(0.5)
                            get_task_request_id = f"get-task-req-expert-{uuid.uuid4()}" # <--- ID для GetTaskRequest
                            get_resp = await expert_agent_client.get_task(
                                GetTaskRequest(id=get_task_request_id, params=TaskQueryParams(id=expert_task.id)) # <--- Добавлен id
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
                            print(f"Manager Agent: Failed to get a detailed response from expert. {error_detail}")
                            return f"Could not get a detailed response from the expert. {error_detail}"
                    else:
                        error_detail = f"response: {response.root}"
                        print(f"Manager Agent: Error creating task for expert. {error_detail}")
                        return f"Error creating task for expert. {error_detail}"

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

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        print(f"Manager Agent: Received cancellation request for task {context.task_id}")
        try:
            task_updater = TaskUpdater(
                event_queue, context.task_id, context.context_id)
            # Добавляем await для асинхронной функции
            await task_updater.update_status(TaskState.canceled)
            print(f"Manager Agent: Task {context.task_id} cancelled.")
        except Exception as e:
            print(f"Manager Agent: Error cancelling task {context.task_id}: {e}")

# ... (остальная часть main функции без изменений)
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
        name='Sales Manager Chat Agent',
        description='Friendly sales manager for AI solutions. Chats with clients, answers questions, and helps choose products.',
        url=public_agent_url, 
        version='1.0.1', 
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        authentication={"schemes": ["basic"]},
        skills=[
            AgentSkill(
                id='client_chat_communication',
                name='Client Chat Communication',
                description='Conducting dialogue with clients in chat, providing information about AI Solutions Corp. products.',
                tags=['sales', 'chat', 'communication'],
            ),
            AgentSkill(
                id='expert_info_query',
                name='Expert Information Query',
                description='Requesting additional information from the company\'s internal expert for more accurate answers.',
                tags=['consultation', 'expertise', 'internal'],
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
    print(f"Starting Uvicorn for Sales Manager Chat Agent on {host}:{port}") 
    print(f"Expecting company expert at {EXPERT_AGENT_URL}")
    uvicorn.run(a2a_app.build(), host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()