// api/client.js
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api';

class ApiClient {
  constructor() {
    this.baseUrl = API_URL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...this.defaultHeaders,
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });
      
      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.message || 'Request failed');
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

  patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // WebSocket连接方法
  connectWebSocket(clientId, onMessage, onError, onClose) {
    const wsUrl = this.baseUrl.replace('http', 'ws') + `/ws/${clientId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connection established');
    };
    
    ws.onmessage = (event) => {
      if (onMessage && typeof onMessage === 'function') {
        onMessage(event.data);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError && typeof onError === 'function') {
        onError(error);
      }
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket connection closed', event.code, event.reason);
      if (onClose && typeof onClose === 'function') {
        onClose(event);
      }
    };
    
    return ws;
  }
}

export const api = new ApiClient();