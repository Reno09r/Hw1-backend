export interface User {
  id: string;
  email: string;
}

export interface Message {
  id: string;
  content: string;
  sender_type: 'user' | 'agent';
  timestamp: string;
}

export interface ChatResponse {
  session_id: string;
  messages: Message[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface ChatRequest {
  content: string;
  session_id?: string;
}