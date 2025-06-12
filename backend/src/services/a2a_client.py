import asyncio
import httpx
import uuid
from typing import List, Optional
from a2a.client import A2AClient, A2AClientError 
from a2a.types import (
    SendMessageRequest, MessageSendParams, GetTaskRequest, 
    TaskQueryParams, TaskState, GetTaskSuccessResponse
)
from src.config import settings

MANAGER_AGENT_URL = settings.MANAGER_AGENT_URL

class A2AClientService:
    def __init__(self):
        self.httpx_client = httpx.AsyncClient(
            timeout=90.0, 
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        ) 
        print("A2AClientService initialized with httpx.AsyncClient")

    async def close(self):
        print("Closing A2AClientService's httpx.AsyncClient...")
        await self.httpx_client.aclose()
        print("httpx.AsyncClient closed.")

    async def send_message_to_manager(self, conversation_text: str) -> str: # Изменен параметр
        """Sends the full conversation text to the manager agent and waits for a response."""
        try:
            print(f"send_message_to_manager: Attempting to connect to Manager Agent at: {MANAGER_AGENT_URL}")
            a2a_sdk_client = await A2AClient.get_client_from_agent_card_url(
                self.httpx_client, MANAGER_AGENT_URL
            )
            print(f"send_message_to_manager: Successfully got A2A SDK client for manager. Agent URL: {a2a_sdk_client.url}")

            request_id = f"send-req-chat-{uuid.uuid4()}"
            send_request_params = MessageSendParams(
                message={
                    'messageId': f"msg-chat-{uuid.uuid4()}",
                    'role': 'user', 
                    'parts': [{'type': 'text', 'text': conversation_text}], # Передаем весь текст диалога
                }
            )
            send_request_obj = SendMessageRequest(id=request_id, params=send_request_params)
            
            print(f"send_message_to_manager: Preparing to send conversation to manager. Request ID: {request_id}, Conversation (first 150 chars): {conversation_text[:150]}...")
            
            response_from_send_message = await a2a_sdk_client.send_message(send_request_obj)
            print("send_message_to_manager: a2a_sdk_client.send_message call completed.")
            
            # ... остальная часть метода без изменений ...
            if not hasattr(response_from_send_message.root, "result"):
                error_msg = f"Error: Failed to create task for manager agent. Response: {response_from_send_message.root}"
                print(f"send_message_to_manager: {error_msg}")
                return error_msg

            manager_task = response_from_send_message.root.result
            print(f"send_message_to_manager: Task for manager created: {manager_task.id}, status: {manager_task.status.state}")
            
            max_attempts = 120
            for attempt in range(max_attempts):
                await asyncio.sleep(0.5)
                get_task_request_id = f"get-task-req-{uuid.uuid4()}" 
                get_task_resp = await a2a_sdk_client.get_task(
                    GetTaskRequest(id=get_task_request_id, params=TaskQueryParams(id=manager_task.id)) 
                )
                if isinstance(get_task_resp.root, GetTaskSuccessResponse):
                    manager_task = get_task_resp.root.result
                    if manager_task.status.state in (TaskState.completed, TaskState.failed, TaskState.canceled):
                        break
                else:
                    error_msg = f"Error getting manager task status: {get_task_resp.root}"
                    print(f"send_message_to_manager: {error_msg}")
                    return error_msg
            
            if manager_task.status.state == TaskState.completed and manager_task.status.message and manager_task.status.message.parts:
                final_text = manager_task.status.message.parts[0].root.text
                print(f"send_message_to_manager: Manager task completed. Response: {final_text[:100]}...")
                return final_text
            elif manager_task.status.state == TaskState.completed:
                msg = f"Error: Manager agent completed the task but returned no message. Status: {manager_task.status.state}"
                print(f"send_message_to_manager: {msg}")
                return msg
            else:
                msg = f"Error: Manager agent could not process the request. Status: {manager_task.status.state}, Message: {manager_task.status.message}"
                print(f"send_message_to_manager: {msg}")
                return msg

        # ... (обработка ошибок остается без изменений) ...
        except httpx.ConnectError as e:
            request_url = e.request.url if e.request else "N/A"
            print(f"Critical error (httpx.ConnectError) in A2A client (manager): {e}. URL: {request_url}")
            return f"Connection error with manager agent service (ConnectError): {str(e)}"
        except httpx.RequestError as e:
            request_url = e.request.url if e.request else "N/A"
            print(f"Critical error (httpx.RequestError) in A2A client (manager): {e}. URL: {request_url}")
            return f"Request error with manager agent service (RequestError): {str(e)}"
        except A2AClientError as e:
            print(f"Critical error (A2AClientError) in A2A client (manager): {e}")
            return f"Error with A2A protocol for manager agent: {str(e)}"
        except Exception as e:
            print(f"Unexpected critical error in A2A client (manager): {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return f"An internal error occurred while communicating with the manager agent: {str(e)}"


a2a_client_service_instance = A2AClientService()

async def get_a2a_client_service() -> A2AClientService:
    return a2a_client_service_instance