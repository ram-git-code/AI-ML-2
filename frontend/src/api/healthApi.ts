import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
});

export interface HealthResponse {
  status: string;
  app_name?: string;
  version?: string;
  error?: string;
  url?: string;
  details?: string;
  target_collection?: string;
  collection_exists?: boolean;
  existing_collections?: string[];
}

export const getBackendHealth = async (): Promise<HealthResponse> => {
  try {
    const res = await client.get<HealthResponse>('/health');
    return res.data;
  } catch (err: any) {
    return {
      status: 'DISCONNECTED',
      error: err.message || 'Failed to connect to FastAPI backend',
    };
  }
};

export const getPostgresHealth = async (): Promise<HealthResponse> => {
  try {
    const res = await client.get<HealthResponse>('/health/postgres');
    return res.data;
  } catch (err: any) {
    return {
      status: 'DISCONNECTED',
      error: err.response?.data?.error || err.message || 'PostgreSQL connection failed',
    };
  }
};

