export interface User {
  id: number;
  username: string;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  completed: boolean;
  deadline?: string;
}

export interface TaskCreate {
  title: string;
  description: string;
  deadline?: string;
}

export interface TaskUpdate {
  title: string;
  description: string;
  completed: boolean;
  deadline?: string;
}

export interface UserCreate {
  username: string;
  password: string;
}

export interface UserUpdate {
  username?: string;
  password?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}