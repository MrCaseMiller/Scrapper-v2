/**
 * API client utilities
 */

import axios from 'axios';

// Use relative URLs in production (Next.js API routes), localhost in development
const API_URL = process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? '' // Use relative URLs in production
    : 'http://localhost:8000' // Use localhost in development
  );

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  signup: async (email: string, password: string) => {
    const response = await api.post('/api/auth/signup', { email, password });
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  getMe: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

// Portfolio API
export const portfolioAPI = {
  getPortfolio: async () => {
    const response = await api.get('/api/portfolio');
    return response.data;
  },

  getPositions: async () => {
    const response = await api.get('/api/positions');
    return response.data;
  },

  getFills: async (limit = 10) => {
    const response = await api.get(`/api/fills?limit=${limit}`);
    return response.data;
  },

  getOrders: async () => {
    const response = await api.get('/api/orders');
    return response.data;
  },
};

// Bot API
export const botAPI = {
  start: async (config: {
    strategy: string;
    max_markets?: number;
    update_interval?: number;
    slippage_factor?: number;
    fee_rate?: number;
    order_ttl_hours?: number;
    strategy_params?: any;
  }) => {
    const response = await api.post('/api/bot/start', config);
    return response.data;
  },

  stop: async () => {
    const response = await api.post('/api/bot/stop');
    return response.data;
  },

  getStatus: async () => {
    const response = await api.get('/api/bot/status');
    return response.data;
  },
};

// Markets API
export const marketsAPI = {
  getMarkets: async (limit = 20) => {
    const response = await api.get(`/api/markets?limit=${limit}`);
    return response.data;
  },
};
