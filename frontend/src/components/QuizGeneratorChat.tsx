import React, { useState } from 'react';
import { Sparkles, Send, BookOpen, Layers, HelpCircle, AlertCircle } from 'lucide-react';
import { generateQuiz, getQuestionSubjects, QuizData } from '../api/quizApi';

interface QuizGeneratorChatProps {
  onQuizGenerated: (quiz: QuizData) => void;
}

export const QuizGeneratorChat: React.FC<QuizGeneratorChatProps> = ({ onQuizGenerated }) => {
  const [prompt, setPrompt] = useState('');
  const [numQuestions, setNumQuestions] = useState<number>(5);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');

  React.useEffect(() => {
    getQuestionSubjects().then(setSubjects).catch(() => setSubjects([]));
  }, []);

  const presetChips = [
    { label: '🏛️ Rajasthan GK PYQs', query: 'Give me 5 Rajasthan GK PYQs', count: 5 },
    { label: '⚡ Physics Core', query: '5 Physics questions', count: 5 },
    { label: '💻 Computer Science', query: '5 Computer Science questions', count: 5 },
    { label: '🧪 Chemistry MCQs', query: 'Chemistry exam questions', count: 4 },
    { label: '📐 Mathematics', query: 'Mathematics practice questions', count: 4 },
  ];

  const handleGenerate = async (customPrompt?: string, customCount?: number) => {
    const textToUse = customPrompt !== undefined ? customPrompt : prompt;
    const countToUse = customCount !== undefined ? customCount : numQuestions;

    if (!textToUse.trim()) {
      setError('Please type a subject, topic, or request to generate a quiz.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const quiz = await generateQuiz(textToUse, countToUse, selectedSubject || undefined);
      onQuizGenerated(quiz);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to generate quiz. Please try a different query.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="quiz-generator-card">
      <div className="generator-header">
        <div className="bot-avatar">
          <Sparkles className="icon-pulse" size={24} />
        </div>
        <div>
          <h2 className="generator-title">AI Quiz Generator Chatbot</h2>
          <p className="generator-subtitle">
            Tell the AI what you want to practice (e.g. <em>"Give me 5 Rajasthan GK PYQ questions"</em>)
          </p>
        </div>
      </div>

      {error && (
        <div className="alert-box error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Preset Suggestion Chips */}
      <div className="preset-chips-container">
        <span className="chips-label">Quick Presets:</span>
        <div className="chips-list">
          {presetChips.map((chip, idx) => (
            <button
              key={idx}
              className="preset-chip"
              onClick={() => {
                setPrompt(chip.query);
                setNumQuestions(chip.count);
                handleGenerate(chip.query, chip.count);
              }}
              disabled={loading}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Prompt Input */}
      <div className="chat-input-bar">
        <input
          type="text"
          className="chat-prompt-input"
          placeholder="Ask AI: e.g., 'Generate 5 medium difficulty questions on Rajasthan GK with PYQs'..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleGenerate();
            }
          }}
          disabled={loading}
        />
        <div className="input-options">
          <label className="count-selector-label">
            Subject:
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              className="count-select"
              disabled={loading}
            >
              <option value="">All subjects</option>
              {subjects.map((subject) => <option key={subject} value={subject}>{subject}</option>)}
            </select>
          </label>
          <label className="count-selector-label">
            Questions:
            <select
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="count-select"
              disabled={loading}
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
            </select>
          </label>
          <button
            className="btn-generate"
            onClick={() => handleGenerate()}
            disabled={loading || !prompt.trim()}
          >
            {loading ? (
              <span className="btn-loading-content">
                <span className="spinner"></span> Generating...
              </span>
            ) : (
              <>
                <Send size={16} /> Generate Quiz
              </>
            )}
          </button>
        </div>
      </div>

      <div className="generator-footer-tips">
        <div className="tip-item">
            <BookOpen size={14} /> <span>Questions selected from the verified question bank</span>
        </div>
        <div className="tip-item">
          <Layers size={14} /> <span>1 question shown at a time with instant green/red evaluation</span>
        </div>
        <div className="tip-item">
          <HelpCircle size={14} /> <span>AI Tutor doubt resolver chatbot available on every question</span>
        </div>
      </div>
    </div>
  );
};
