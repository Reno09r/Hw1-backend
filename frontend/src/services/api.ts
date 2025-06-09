const API_BASE_URL = 'http://localhost:8001';

class ApiService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('access_token');
    console.log('Current token in localStorage:', token);
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    console.log('Generated auth headers:', headers);
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP error! status: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    return response.text() as any;
  }

  async login(username: string, password: string) {
    console.log('Attempting login for user:', username);
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await this.handleResponse<{ access_token: string; token_type: string }>(response);
    console.log('Login successful, received token:', data.access_token);
    localStorage.setItem('access_token', data.access_token);
    console.log('Token saved to localStorage');
    return data;
  }

  async register(userData: { username: string; password: string }) {
    const response = await fetch(`${API_BASE_URL}/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    return this.handleResponse<{ id: number; username: string }>(response);
  }

  async getCurrentUser() {
    console.log('Fetching current user...');
    const token = localStorage.getItem('access_token');
    console.log('Token from localStorage:', token);
    
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
    console.log('Request headers:', headers);

    const response = await fetch(`${API_BASE_URL}/users/me`, {
      headers
    });

    console.log('Response status:', response.status);
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response:', errorText);
      throw new Error(errorText || `HTTP error! status: ${response.status}`);
    }

    return this.handleResponse<{ id: number; username: string }>(response);
  }

  async updateUser(userData: { username?: string; password?: string }) {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(userData),
    });

    return this.handleResponse<{ id: number; username: string }>(response);
  }

  async deleteUser() {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'DELETE',
      headers: {
        ...this.getAuthHeader(),
      },
    });

    if (!response.ok) {
      throw new Error('Failed to delete user');
    }
  }

  async getTasks() {
    const response = await fetch(`${API_BASE_URL}/tasks/`, {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader(),
      },
    });

    return this.handleResponse<Array<{
      id: number;
      title: string;
      description: string;
      completed: boolean;
      deadline?: string;
    }>>(response);
  }

  async createTask(taskData: { title: string; description: string; deadline?: string }) {
    const response = await fetch(`${API_BASE_URL}/tasks/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(taskData),
    });

    return this.handleResponse<{
      id: number;
      title: string;
      description: string;
      completed: boolean;
      deadline?: string;
    }>(response);
  }

  async updateTask(id: number, taskData: {
    title: string;
    description: string;
    completed: boolean;
    deadline?: string;
  }) {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader(),
      },
      body: JSON.stringify(taskData),
    });

    return this.handleResponse<{
      id: number;
      title: string;
      description: string;
      completed: boolean;
      deadline?: string;
    }>(response);
  }

  async deleteTask(id: number) {
    const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
      method: 'DELETE',
      headers: {
        ...this.getAuthHeader(),
      },
    });

    if (!response.ok) {
      throw new Error('Failed to delete task');
    }
  }

  logout() {
    localStorage.removeItem('access_token');
  }
}

export const apiService = new ApiService();