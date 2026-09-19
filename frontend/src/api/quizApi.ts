import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const getQuestionSubjects = async (): Promise<string[]> => {
  const response = await axios.get<string[]>(`${API_BASE_URL}/api/questions/subjects`);
  return response.data;
};

export interface QuizQuestion {
  id: string;
  question_type: string;
  question_text: string;
  options: any; // Can be string[] or {Key: string, Text: string}[]
  subject: string;
  chapter: string;
  topic: string;
  difficulty: string;
  is_pyq: boolean;
  exam_name?: string;
  exam_year?: number;
}

export interface QuizData {
  id: string;
  title: string;
  total_questions: number;
  questions: QuizQuestion[];
}

export interface AnswerSubmissionResult {
  question_id: string;
  selected_answer: any;
  is_correct: boolean;
  correct_answer: string;
  explanation?: string;
  score: number;
  total_answered: number;
  total_questions: number;
  quiz_completed: boolean;
}

export interface QuizSummary {
  id: string;
  title: string;
  total_questions: number;
  score: number;
  completed: boolean;
  answers: Record<string, { selected_answer: any; is_correct: boolean }>;
}

export const generateQuiz = async (
  query?: string,
  numberOfQuestions: number = 5,
  subject?: string,
  difficulty?: string,
  isPyq?: boolean
): Promise<QuizData> => {
  const response = await axios.post<QuizData>(`${API_BASE_URL}/api/quizzes/generate`, {
    query: query?.trim() || undefined,
    number_of_questions: numberOfQuestions,
    subject: subject || undefined,
    difficulty: difficulty || undefined,
    is_pyq: isPyq !== undefined ? isPyq : undefined,
  });
  return response.data;
};

export const getQuiz = async (quizId: string): Promise<QuizData> => {
  const response = await axios.get<QuizData>(`${API_BASE_URL}/api/quizzes/${quizId}`);
  return response.data;
};

export const submitQuizAnswer = async (
  quizId: string,
  questionId: string,
  selectedAnswer: any
): Promise<AnswerSubmissionResult> => {
  const response = await axios.post<AnswerSubmissionResult>(
    `${API_BASE_URL}/api/quizzes/${quizId}/answers`,
    {
      question_id: questionId,
      selected_answer: selectedAnswer,
    }
  );
  return response.data;
};

export const getQuizSummary = async (quizId: string): Promise<QuizSummary> => {
  const response = await axios.get<QuizSummary>(`${API_BASE_URL}/api/quizzes/${quizId}/summary`);
  return response.data;
};
