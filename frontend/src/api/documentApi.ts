import axios from 'axios';
import { QuizData } from './quizApi';

const API_BASE_URL = 'http://localhost:8000/api';

export interface DocumentChunk {
  id: string;
  page_number: number;
  chunk_index: number;
  chunk_text: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  title: string;
  file_size_bytes: number;
  page_count: number;
  summary: string | null;
  topics: string[];
  key_insights: string[];
  estimated_difficulty: string;
  status: string;
  created_at: string;
  chunk_count: number;
}

export interface DocumentDetail extends DocumentInfo {
  chunks: DocumentChunk[];
}

export interface DocumentQuizRequest {
  question_count: number;
  difficulty: string;
  focus_topic?: string;
}

export const documentApi = {
  uploadDocument: async (file: File): Promise<DocumentInfo> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post<DocumentInfo>(`${API_BASE_URL}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  listDocuments: async (): Promise<DocumentInfo[]> => {
    const response = await axios.get<DocumentInfo[]>(`${API_BASE_URL}/documents`);
    return response.data;
  },

  getDocument: async (documentId: string): Promise<DocumentDetail> => {
    const response = await axios.get<DocumentDetail>(`${API_BASE_URL}/documents/${documentId}`);
    return response.data;
  },

  generateDocumentQuiz: async (documentId: string, payload: DocumentQuizRequest): Promise<QuizData> => {
    const response = await axios.post<QuizData>(`${API_BASE_URL}/documents/${documentId}/quiz`, payload);
    return response.data;
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/documents/${documentId}`);
  },
};
