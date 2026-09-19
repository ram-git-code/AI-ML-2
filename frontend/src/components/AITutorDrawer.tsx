import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, X, Sparkles } from 'lucide-react';
import { QuizQuestion, getQuestionSubjects } from '../api/quizApi';
import { sendTutorMessage, ChatMessage } from '../api/aiApi';

interface AITutorDrawerProps {
  question: QuizQuestion | null;
  userAnswer?: any;
  isOpen: boolean;
  onClose: () => void;
}

export const AITutorDrawer: React.FC<AITutorDrawerProps> = ({
  question,
  userAnswer,
  isOpen,
  onClose,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize tutor welcome message when question changes
  useEffect(() => {
    getQuestionSubjects().then(setSubjects).catch(() => setSubjects([]));
  }, []);

  useEffect(() => {
    if (question) {
      setSelectedSubject(question.subject);
      setMessages([
        {
          role: 'assistant',
          content: `👋 Hi! I'm your AI Quiz Tutor. Have any doubts or questions regarding **${question.subject}** (*"${question.question_text.slice(0, 60)}..."*)? Ask me anything!`,
        },
      ]);
    }
  }, [question?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const quickQuestions = [
    'Why is this answer correct?',
    'Explain this concept in simple words',
    'Give me a mnemonic or memory trick',
    'Give a real-world example',
  ];

  const handleSendMessage = async (textToSend?: string) => {
    const messageText = textToSend !== undefined ? textToSend : inputMessage;
    if (!messageText.trim() || loading) return;

    const newHistory: ChatMessage[] = [...messages, { role: 'user', content: messageText }];
    setMessages(newHistory);
    setInputMessage('');
    setLoading(true);

    try {
      const res = await sendTutorMessage(question ? question.id : null, selectedSubject || null, messageText, newHistory);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            '⚠️ I encountered a temporary issue connecting to the AI Tutor. Please verify your connection or try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="tutor-drawer-overlay">
      <div className="tutor-drawer">
        <div className="tutor-header">
          <div className="tutor-header-title">
            <div className="tutor-bot-icon">
              <Bot size={20} />
            </div>
            <div>
              <h3>AI Tutor • Doubt Resolver</h3>
              <p className="tutor-sub">
                {question ? `${question.subject} • ${question.topic}` : 'General Academic Doubt Chat'}
              </p>
            </div>
          </div>
          <button className="tutor-close-btn" onClick={onClose} aria-label="Close AI Tutor">
            <X size={20} />
          </button>
        </div>
        <select
          className="tutor-subject-select"
          value={selectedSubject}
          onChange={(event) => setSelectedSubject(event.target.value)}
          aria-label="Tutor subject"
        >
          <option value="">All question-bank subjects</option>
          {subjects.map((subject) => <option key={subject} value={subject}>{subject}</option>)}
        </select>

        {/* Current Question Context Strip */}
        {question && (
          <div className="tutor-context-strip">
            <span className="context-label">Active Question:</span>
            <span className="context-text">{question.question_text}</span>
          </div>
        )}

        {/* Quick Suggestion Chips */}
        <div className="tutor-quick-chips">
          {quickQuestions.map((q, idx) => (
            <button
              key={idx}
              className="quick-chip-btn"
              onClick={() => handleSendMessage(q)}
              disabled={loading}
            >
              <Sparkles size={12} /> {q}
            </button>
          ))}
        </div>

        {/* Messages List */}
        <div className="tutor-messages-container">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message-row ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className="message-bubble">
                {msg.role === 'assistant' && (
                  <div className="bubble-author">
                    <Sparkles size={12} className="inline-sparkle" /> AI Academic Tutor
                  </div>
                )}
                <div className="message-text" style={{ whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble loading-bubble">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="tutor-input-area">
          <input
            type="text"
            className="tutor-chat-input"
            placeholder="Type your doubt or question here..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={loading}
          />
          <button
            className="tutor-send-btn"
            onClick={() => handleSendMessage()}
            disabled={loading || !inputMessage.trim()}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
