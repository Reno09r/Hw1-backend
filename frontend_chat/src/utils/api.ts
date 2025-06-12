// --- START OF FILE api.ts (ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ) ---

const API_BASE_URL = 'http://localhost:8001';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options, 
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Не удалось прочитать ошибку от сервера' }));

    const detailMessage = errorData.detail && typeof errorData.detail === 'object'
      ? JSON.stringify(errorData.detail)
      : errorData.detail;

    throw new ApiError(
      response.status,
      detailMessage || `HTTP ${response.status}`
    );
  }

  if (response.status === 204) {
    return {} as T;
  }
  
  return response.json();
}

export const authApi = {
  login: async (credentials: { username: string; password: string }) => {
    return apiRequest<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },
};

export const chatApi = {
  sendMessage: async (
    message: { content: string; session_id: string | null },
    token: string
  ) => {
    return apiRequest<{
      session_id: string;
      messages: Array<{
        id: string;
        content: string;
        sender_type: 'user' | 'agent';
        timestamp: string;
      }>;
    }>('/chat/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(message),
    });
  },
};
// --- END OF FILE api.ts ---