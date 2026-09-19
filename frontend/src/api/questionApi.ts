import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface QuestionImportResult {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  total: number;
  imported: number;
  embedded: number;
  collection: string;
  message: string;
}

export const importQuestions = async (file: File): Promise<QuestionImportResult> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post<QuestionImportResult>(`${API_BASE_URL}/api/questions/import`, formData);
  return response.data;
};

export const getImportStatus = async (jobId: string): Promise<QuestionImportResult> => {
  const response = await axios.get<QuestionImportResult>(`${API_BASE_URL}/api/questions/import/${jobId}`);
  return response.data;
};