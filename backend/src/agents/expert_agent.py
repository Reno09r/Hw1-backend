import os
import click
import uvicorn
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI 

from pydantic import BaseModel 
from pydantic_ai import Agent as PydanticAIAgent 

from a2a.types import (
    AgentCard, AgentCapabilities, AgentSkill, TaskState, TextPart
)
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please check your .env file.")


COMPANY_DATA = """
Our company 'AI Solutions Corp' specialises in developing advanced AI solutions for businesses.

The main products are:
1. Document Analyzer - Automated document and invoice processing system
   - Uses OCR and NLP for data extraction
   - Integrates with ERP systems
   - 99.7% recognition accuracy
   - Price: from $5,000/month for basic version
   - Supports formats: PDF, JPG, PNG, TIFF
   - Processing time: up to 1000 documents per hour

2. Vision AI - warehouse monitoring and inventory solution
   - Computer vision for tracking goods
   - Automatic inventory update
   - Anomaly and shortage detection
   - Price: from $8,000/month
   - Camera support: IP cameras, USB cameras
   - Detection accuracy: 98.5%

Founded in 2020, over 500 successful implementations, offices in 15 countries.
24/7 technical support, 30 days money back guarantee.
"""

def calculate(expression: str) -> str:
    # ... (код без изменений)
    try:
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in expression):
            return "Calculation error: invalid characters in expression."
        
        if "__" in expression:
             return "Calculation error: potentially unsafe expression."

        result = eval(expression, {"__builtins__": {}}, {}) 
        return f"Calculation result for '{expression}': {result}"
    except Exception as e:
        return f"Calculation error for '{expression}': {e}"

class ExpertResponse(BaseModel):
    information: str

simple_expert_llm_agent = PydanticAIAgent(
    model='openai:gpt-4o-mini', 
    result_type=ExpertResponse, 
    system_prompt=f"""You are an AI expert for 'AI Solutions Corp'. You will receive a CHRONOLOGICAL conversation transcript between a sales manager and a customer.
Your role is to provide CONCISE, FACTUAL information to the sales manager to help them answer the LATEST customer message in the transcript.

COMPANY_DATA (Your sole source of product truth):
{COMPANY_DATA}

Instructions:
1.  Analyze the LATEST customer message within the context of the entire transcript.
2.  If the LATEST customer message explicitly asks for product details (e.g., "Tell me more about Vision AI", "What are Document Analyzer's features?") or implies a need for clarification on specific product features, provide relevant information extracted ONLY from COMPANY_DATA. Focus on the product(s) mentioned or implied by the LATEST query.
3.  If the LATEST customer message is about scheduling, a simple confirmation (e.g., "Yes, please"), a greeting, or anything not requiring detailed product data, your response to the manager should be something like: "The user's latest message is [briefly describe, e.g., 'confirming demo interest for Vision AI', 'asking to schedule for Aug 15th', 'a simple greeting']. No specific product details from COMPANY_DATA seem necessary for the manager's next turn. The manager should proceed with [e.g., 'confirming demo time', 'acknowledging the scheduling request', 'a greeting']."
4.  Your output is for the SALES MANAGER, not the end customer. It should be brief and direct.
5.  If calculations are needed and requested in relation to the latest query, use the 'calculate' tool.
""",
    tools=[calculate] 
)


class CompanyExpertExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        print("Expert Agent: Received message")
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        
        try:
            if event_queue.is_closed():
                print("Expert Agent Warning: Event queue is closed, reopening...")
                event_queue = EventQueue()
                task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            
            await task_updater.submit()
            await task_updater.start_work()
            
            conversation_transcript_from_manager = context.message.parts[0].root.text
            print(f"Expert Agent: Received conversation transcript from manager (last 250 chars): ...{conversation_transcript_from_manager[-250:]}")
            
            final_text_response = ""
            try:
                print("Expert Agent: Requesting response from Pydantic AI Agent...")
                llm_response = await simple_expert_llm_agent.run(conversation_transcript_from_manager)
                final_text_response = llm_response.output.information
                print(f"Expert Agent: Pydantic AI Agent responded: {final_text_response[:100]}...")

            except Exception as agent_error:
                print(f"Expert Agent: Error from Pydantic AI Agent: {agent_error}")
                final_text_response = f"An error occurred while processing the request with context. Basic product info: Document Analyzer, Vision AI. Details in COMPANY_DATA."
                print(f"Expert Agent: Using fallback response: {final_text_response[:100]}...")

            print(f"Expert Agent: Sending final response to manager: {final_text_response[:200]}...")
            await task_updater.update_status(
                TaskState.completed,
                message=task_updater.new_agent_message(
                    parts=[TextPart(text=final_text_response)]
                ),
            )
            
        # ... (обработка ошибок остается без изменений) ...
        except Exception as e:
            print(f"Expert Agent: Error in CompanyExpertExecutor: {e}")
            import traceback
            traceback.print_exc()
            try:
                if event_queue.is_closed():
                    event_queue = EventQueue()
                task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
                await task_updater.update_status( 
                    TaskState.failed,
                    message=task_updater.new_agent_message(
                        parts=[TextPart(text=f"Error processing request for expert: {str(e)}")]
                    ),
                )
            except Exception as update_error:
                print(f"Expert Agent: Critical error when updating task status to failed: {update_error}")
        
    # ... (метод cancel и main без изменений) ...
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        print(f"Expert Agent: Received cancellation request for task {context.task_id}")
        try:
            task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await task_updater.update_status(TaskState.canceled) 
            print(f"Expert Agent: Task {context.task_id} cancelled.")
        except Exception as e:
            print(f"Expert Agent: Error cancelling task {context.task_id}: {e}")

@click.command()
@click.option('--host', default='0.0.0.0', help='Host for Uvicorn server (usually 0.0.0.0 in Docker)')
@click.option('--port', default=10007, help='Port for Uvicorn server')
def main(host: str, port: int):
    agent_executor = CompanyExpertExecutor()
    public_agent_url = os.getenv("PUBLIC_AGENT_URL")
    if not public_agent_url:
        if host == '0.0.0.0':
            print("WARNING (Expert Agent): Uvicorn is running on 0.0.0.0, but PUBLIC_AGENT_URL is not set.")
            print(f"AgentCard will use http://expert-agent:{port}/ as a fallback, but it's better to set PUBLIC_AGENT_URL explicitly.")
            public_agent_url = f'http://expert-agent:{port}/' 
        else:
            public_agent_url = f'http://{host}:{port}/'
    print(f"Public URL for AgentCard (Expert Agent): {public_agent_url}")
    agent_card = AgentCard(
        name='Company Information Expert Agent (Context-Aware)', 
        description='Expert on AI Solutions Corp products and services (based on COMPANY_DATA). Can perform calculations. Understands conversation context.',
        url=public_agent_url,
        version='1.2.1', # Increment version
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        authentication={"schemes": ["basic"]},
        skills=[
            AgentSkill(
                id='company_contextual_data_expertise', 
                name='Company Contextual Data Expertise',
                description='Expert knowledge about AI Solutions Corp products and services based on provided data (COMPANY_DATA), considering conversation context.',
                tags=['company', 'products', 'expertise', 'static-data', 'context-aware'],
            ),
            AgentSkill(
                id='contextual_calculations', 
                name='Contextual Calculations',
                description='Performing mathematical calculations, considering conversation context if relevant.',
                tags=['math', 'calculations', 'context-aware'],
            )
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
    print(f"Starting Company Expert Agent (Context-Aware) on {host}:{port}")
    uvicorn.run(a2a_app.build(), host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()