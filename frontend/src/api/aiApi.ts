import axios from 'axios';
import { QuizData } from './quizApi';

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
  learning_context_id?: string;
}

export interface LearningContextSnapshot {
  learning_context_id: string;
  conversation_id: string;
  intent: string;
  topic?: string | null;
  subtopic?: string | null;
  concepts: string[];
  can_create_quiz: boolean;
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

export interface StreamChatCallbacks {
  onStart?: (data: {
    conversation_id: string;
    learning_context_id: string;
    intent: string;
    topic?: string;
    quiz_available: boolean;
    subject?: string;
  }) => void;
  onToken?: (token: string) => void;
  onComplete?: (data: {
    conversation_id: string;
    learning_context_id: string;
    intent: string;
    topic?: string | null;
    subtopic?: string | null;
    concepts: string[];
    can_create_quiz: boolean;
  }) => void;
  onError?: (errorMsg: string) => void;
}

export const streamAIChat = async (
  payload: {
    message: string;
    conversation_id?: string;
    subject?: string;
    topic?: string;
    chat_history?: ChatMessage[];
  },
  callbacks: StreamChatCallbacks,
  signal?: AbortSignal
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is empty.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const block of lines) {
        if (!block.trim()) continue;

        let eventType = 'token';
        let eventData = '';

        const eventLines = block.split('\n');
        for (const line of eventLines) {
          if (line.startsWith('event: ')) {
            eventType = line.substring(7).trim();
          } else if (line.startsWith('data: ')) {
            eventData = line.substring(6).trim();
          }
        }

        if (eventData) {
          try {
            const parsed = JSON.parse(eventData);
            if (eventType === 'start') {
              callbacks.onStart?.(parsed);
            } else if (eventType === 'token') {
              if (parsed.text) {
                callbacks.onToken?.(parsed.text);
              }
            } else if (eventType === 'complete') {
              callbacks.onComplete?.(parsed);
            } else if (eventType === 'error') {
              callbacks.onError?.(parsed.detail || 'An error occurred.');
            }
          } catch {
            if (eventType === 'token') {
              callbacks.onToken?.(eventData);
            }
          }
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      return;
    }
    callbacks.onError?.(err.message || 'Failed to connect to AI Tutor.');
  }
};

export const createQuizFromChat = async (params: {
  learning_context_id?: string;
  topic?: string;
  subject?: string;
  question_count?: number;
  difficulty?: string;
  conversation_id?: string;
  chat_history?: ChatMessage[];
}): Promise<QuizData> => {
  const response = await axios.post<QuizData>(
    `${API_BASE_URL}/api/ai/chat/create-quiz`,
    {
      learning_context_id: params.learning_context_id || undefined,
      topic: params.topic || undefined,
      subject: params.subject || undefined,
      question_count: params.question_count || 5,
      difficulty: params.difficulty || 'medium',
      conversation_id: params.conversation_id || undefined,
      chat_history: params.chat_history || [],
    }
  );
  return response.data;
};
