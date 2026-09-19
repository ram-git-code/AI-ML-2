import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface AIExplanation {
  question_id: string;
  user_answer: string;
  correct_answer: string;
  why_wrong: string;
  why_correct: string;
  key_takeaway: string;
  full_explanation: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AITutorResponse {
  reply: string;
  question_id?: string;
}

export const getAIExplanation = async (
  questionId: string,
  userAnswer: string
): Promise<AIExplanation> => {
  const response = await axios.post<AIExplanation>(`${API_BASE_URL}/api/ai/explain`, {
    question_id: questionId,
    user_answer: userAnswer,
  });
  return response.data;
};

export const sendTutorMessage = async (
  questionId: string | null,
  subject: string | null,
  userMessage: string,
  chatHistory: ChatMessage[]
): Promise<AITutorResponse> => {
  const response = await axios.post<AITutorResponse>(`${API_BASE_URL}/api/ai/tutor`, {
    question_id: questionId || undefined,
    subject: subject || undefined,
    user_message: userMessage,
    chat_history: chatHistory,
  });
  return response.data;
};
