import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  RotateCcw,
  BookOpen,
  Bot,
  User,
  GraduationCap,
  ArrowRight,
  Loader2,
  HelpCircle,
  CheckCircle2,
  Atom,
  Flame,
  Lightbulb,
  AlertCircle,
  HelpCircle as QuestionIcon,
  Zap
} from 'lucide-react';
import {
  streamAIChat,
  createQuizFromChat,
  ChatMessage,
  LearningContextSnapshot
} from '../api/aiApi';
import { QuizData } from '../api/quizApi';

interface UIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  learningContext?: LearningContextSnapshot;
  isStreaming?: boolean;
  error?: boolean;
}

interface AITutorChatProps {
  onStartQuiz: (quiz: QuizData) => void;
}

export const AITutorChat: React.FC<AITutorChatProps> = ({ onStartQuiz }) => {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [generatingQuizId, setGeneratingQuizId] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>(undefined);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const starterSuggestions = [
    {
      label: "Newton's Second Law",
      prompt: "Explain Newton's second law of motion in simple terms with examples.",
      subject: "Physics",
      icon: Atom
    },
    {
      label: "Photosynthesis Reactions",
      prompt: "Explain the light-dependent and dark reactions of photosynthesis step by step.",
      subject: "Biology",
      icon: Flame
    },
    {
      label: "Ohm's Law & Resistance",
      prompt: "Why does resistance decrease current in a circuit? Explain Ohm's Law (V = IR).",
      subject: "Physics",
      icon: Lightbulb
    },
    {
      label: "Chemical Bonding",
      prompt: "What is the difference between ionic and covalent bonds? Give clear real-world examples.",
      subject: "Chemistry",
      icon: Atom
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || isStreaming) return;

    setInputMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `ai-${Date.now()}`;

    const userMessage: UIMessage = {
      id: userMsgId,
      role: 'user',
      content: query,
    };

    const initialAssistantMessage: UIMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsStreaming(true);

    // Build chat history with attached learning context IDs
    const chatHistory: ChatMessage[] = messages
      .filter((m) => !m.error && m.content.trim())
      .map((m) => ({
        role: m.role,
        content: m.content,
        learning_context_id: m.learningContext?.learning_context_id,
      }));

    abortControllerRef.current = new AbortController();

    let accumulatedText = '';

    await streamAIChat(
      {
        message: query,
        conversation_id: conversationId || undefined,
        subject: selectedSubject,
        chat_history: chatHistory,
      },
      {
        onStart: (data) => {
          if (data.conversation_id) setConversationId(data.conversation_id);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    learningContext: {
                      learning_context_id: data.learning_context_id,
                      conversation_id: data.conversation_id,
                      intent: data.intent,
                      topic: data.topic,
                      concepts: [],
                      can_create_quiz: data.quiz_available,
                    },
                  }
                : msg
            )
          );
        },
        onToken: (token) => {
          accumulatedText += token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: accumulatedText }
                : msg
            )
          );
        },
        onComplete: (data) => {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedText,
                    isStreaming: false,
                    learningContext: {
                      learning_context_id: data.learning_context_id,
                      conversation_id: data.conversation_id,
                      intent: data.intent,
                      topic: data.topic,
                      subtopic: data.subtopic,
                      concepts: data.concepts,
                      can_create_quiz: data.can_create_quiz,
                    },
                  }
                : msg
            )
          );
        },
        onError: (errorMsg) => {
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content:
                      accumulatedText ||
                      `⚠️ **Connection Issue**: ${errorMsg}\n\nPlease verify your backend connection or click Retry below.`,
                    isStreaming: false,
                    error: true,
                  }
                : msg
            )
          );
        },
      },
      abortControllerRef.current.signal
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
    setConversationId('');
    setIsStreaming(false);
  };

  const handleCreateQuiz = async (msg: UIMessage) => {
    const ctx = msg.learningContext;
    const targetTopic = ctx?.topic || 'General Topic';
    const contextId = ctx?.learning_context_id;

    setGeneratingQuizId(msg.id);

    try {
      const history: ChatMessage[] = messages
        .filter((m) => !m.error && m.content.trim())
        .map((m) => ({
          role: m.role,
          content: m.content,
          learning_context_id: m.learningContext?.learning_context_id,
        }));

      const quiz = await createQuizFromChat({
        learning_context_id: contextId,
        topic: targetTopic,
        subject: selectedSubject,
        question_count: 5,
        difficulty: 'medium',
        conversation_id: conversationId,
        chat_history: history,
      });

      setGeneratingQuizId(null);
      onStartQuiz(quiz);
    } catch (err) {
      console.error('Failed to create quiz:', err);
      setGeneratingQuizId(null);
      alert('Could not generate quiz for this topic. Please try again.');
    }
  };

  const handleExplainSimpler = (topic?: string | null) => {
    const prompt = topic
      ? `Can you explain ${topic} in simpler terms using an intuitive real-world analogy?`
      : 'Can you explain this more simply with an easy analogy?';
    handleSendMessage(prompt);
  };

  const handleGiveExample = (topic?: string | null) => {
    const prompt = topic
      ? `Can you give me another practical, real-world example of ${topic}?`
      : 'Can you give me another practical example of this?';
    handleSendMessage(prompt);
  };

  // Find latest active learning topic for the header chip
  const latestLearningTopic = [...messages]
    .reverse()
    .find((m) => m.learningContext?.topic && m.learningContext?.can_create_quiz)
    ?.learningContext?.topic;

  // Basic Markdown Renderer for Educational Tutoring
  const renderMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];

    let inCodeBlock = false;
    let codeBuffer: string[] = [];

    lines.forEach((line, index) => {
      // Code blocks
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          elements.push(
            <pre key={`code-${index}`} className="tutor-code-block">
              <code>{codeBuffer.join('\n')}</code>
            </pre>
          );
          codeBuffer = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        return;
      }

      if (inCodeBlock) {
        codeBuffer.push(line);
        return;
      }

      // Headings
      if (line.startsWith('## ')) {
        elements.push(
          <h3 key={`h2-${index}`} className="tutor-heading-2">
            {line.substring(3).trim()}
          </h3>
        );
        return;
      }
      if (line.startsWith('### ')) {
        elements.push(
          <h4 key={`h3-${index}`} className="tutor-heading-3">
            {line.substring(4).trim()}
          </h4>
        );
        return;
      }

      // Lists
      if (line.trim().startsWith('• ') || line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        const itemText = line.trim().substring(2);
        elements.push(
          <li key={`li-${index}`} className="tutor-bullet-item">
            {renderInlineMarkdown(itemText)}
          </li>
        );
        return;
      }

      const numMatch = line.trim().match(/^(\d+)\.\s+(.*)$/);
      if (numMatch) {
        elements.push(
          <div key={`num-${index}`} className="tutor-num-item">
            <span className="tutor-num-badge">{numMatch[1]}</span>
            <span>{renderInlineMarkdown(numMatch[2])}</span>
          </div>
        );
        return;
      }

      // Empty line
      if (!line.trim()) {
        elements.push(<div key={`sp-${index}`} className="tutor-line-space" />);
        return;
      }

      // Regular paragraph
      elements.push(
        <p key={`p-${index}`} className="tutor-paragraph">
          {renderInlineMarkdown(line)}
        </p>
      );
    });

    if (inCodeBlock && codeBuffer.length > 0) {
      elements.push(
        <pre key="code-dangling" className="tutor-code-block">
          <code>{codeBuffer.join('\n')}</code>
        </pre>
      );
    }

    return elements;
  };

  const renderInlineMarkdown = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|\`.*?\`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="tutor-bold">{part.substring(2, part.length - 2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="tutor-inline-code">{part.substring(1, part.length - 1)}</code>;
      }
      return part;
    });
  };

  return (
    <div className="tutor-chat-container">
      {/* Top Header */}
      <div className="tutor-chat-header">
        <div className="tutor-header-info">
          <div className="tutor-avatar-icon">
            <GraduationCap size={22} />
          </div>
          <div>
            <div className="tutor-title-row">
              <h2 className="tutor-title">AI Master Tutor</h2>
              <span className="tutor-live-badge">
                <span className="live-dot" /> Context-Aware RAG
              </span>
            </div>
            <p className="tutor-subtitle">
              Ask academic questions, explore concepts step by step, and test mastery with targeted quizzes.
            </p>
          </div>
        </div>

        <div className="tutor-header-actions">
          {latestLearningTopic && (
            <div className="tutor-active-topic-chip" title="Current Active Topic">
              <BookOpen size={14} />
              <span>{latestLearningTopic}</span>
            </div>
          )}
          {messages.length > 0 && (
            <button className="tutor-clear-btn" onClick={handleClearChat} title="Start a fresh conversation">
              <RotateCcw size={15} /> New Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages Viewport */}
      <div className="tutor-messages-viewport">
        {messages.length === 0 ? (
          <div className="tutor-empty-state">
            <div className="tutor-empty-icon">
              <Bot size={44} />
            </div>
            <h3>What concept would you like to master today?</h3>
            <p>
              Ask any question or academic doubt. The AI Tutor retrieves curriculum context from the Question Bank and provides step-by-step intuitive explanations.
            </p>

            <div className="tutor-starter-grid">
              {starterSuggestions.map((item, index) => {
                const Icon = item.icon;
                return (
                  <button
                    key={index}
                    className="tutor-starter-card"
                    onClick={() => {
                      setSelectedSubject(item.subject);
                      handleSendMessage(item.prompt);
                    }}
                  >
                    <div className="starter-card-top">
                      <div className="starter-icon-badge">
                        <Icon size={16} />
                      </div>
                      <span className="starter-subject-tag">{item.subject}</span>
                    </div>
                    <span className="starter-card-label">{item.label}</span>
                    <span className="starter-card-prompt">{item.prompt}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="tutor-messages-list">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`tutor-msg-wrapper ${msg.role === 'user' ? 'user-msg-wrapper' : 'assistant-msg-wrapper'}`}
              >
                <div className="tutor-msg-avatar">
                  {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>

                <div className="tutor-msg-bubble">
                  <div className="tutor-msg-header">
                    <span className="tutor-msg-sender">
                      {msg.role === 'user' ? 'You' : 'AI Educational Tutor'}
                    </span>
                    {msg.learningContext?.topic && msg.role === 'assistant' && msg.learningContext.can_create_quiz && (
                      <span className="tutor-topic-tag">
                        <BookOpen size={12} /> {msg.learningContext.topic}
                      </span>
                    )}
                  </div>

                  <div className="tutor-msg-content">
                    {msg.content ? (
                      renderMarkdown(msg.content)
                    ) : msg.isStreaming ? (
                      <div className="tutor-thinking-row">
                        <span className="tutor-thinking-dot" />
                        <span className="tutor-thinking-dot" />
                        <span className="tutor-thinking-dot" />
                        <span className="tutor-thinking-text">Synthesizing educational explanation...</span>
                      </div>
                    ) : null}

                    {msg.isStreaming && msg.content && (
                      <span className="tutor-cursor-blink">▍</span>
                    )}
                  </div>

                  {/* Context-Aware Action Card for Learning Responses */}
                  {msg.role === 'assistant' && msg.learningContext?.can_create_quiz && !msg.isStreaming && (
                    <div className="tutor-quiz-cta-container">
                      <div className="tutor-quiz-cta-card">
                        <div className="quiz-cta-info">
                          <div className="quiz-cta-icon">
                            <Sparkles size={18} />
                          </div>
                          <div>
                            <span className="quiz-cta-title">
                              Verify Mastery: {msg.learningContext.topic}
                            </span>
                            <span className="quiz-cta-desc">
                              Generate a custom 5-question practice quiz based specifically on this explanation.
                            </span>
                          </div>
                        </div>

                        <button
                          className="tutor-create-quiz-btn"
                          disabled={generatingQuizId !== null}
                          onClick={() => handleCreateQuiz(msg)}
                        >
                          {generatingQuizId === msg.id ? (
                            <>
                              <Loader2 size={16} className="spin-animate" />
                              Building Quiz...
                            </>
                          ) : (
                            <>
                              <Sparkles size={16} />
                              Practice {msg.learningContext.topic ? `"${msg.learningContext.topic.length > 25 ? msg.learningContext.topic.slice(0, 22) + '...' : msg.learningContext.topic}"` : 'Quiz'}
                              <ArrowRight size={16} />
                            </>
                          )}
                        </button>
                      </div>

                      {/* Auxiliary learning actions */}
                      <div className="tutor-aux-actions">
                        <button
                          className="tutor-aux-btn"
                          disabled={isStreaming}
                          onClick={() => handleExplainSimpler(msg.learningContext?.topic)}
                        >
                          <Zap size={14} /> Explain Simpler
                        </button>
                        <button
                          className="tutor-aux-btn"
                          disabled={isStreaming}
                          onClick={() => handleGiveExample(msg.learningContext?.topic)}
                        >
                          <Lightbulb size={14} /> Give Example
                        </button>
                      </div>
                    </div>
                  )}

                  {msg.error && (
                    <div className="tutor-msg-error-row">
                      <button
                        className="tutor-retry-btn"
                        onClick={() => {
                          const lastUser = [...messages].reverse().find((m) => m.role === 'user');
                          if (lastUser) handleSendMessage(lastUser.content);
                        }}
                      >
                        <RotateCcw size={14} /> Retry Question
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="tutor-input-container">
        <div className="tutor-input-box">
          <textarea
            ref={textareaRef}
            className="tutor-textarea"
            placeholder="Ask your doubt... (e.g., 'Explain Newton's second law in simple terms')"
            value={inputMessage}
            rows={1}
            disabled={isStreaming}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
          />

          <button
            className={`tutor-send-btn ${inputMessage.trim() && !isStreaming ? 'active' : ''}`}
            disabled={!inputMessage.trim() || isStreaming}
            onClick={() => handleSendMessage()}
            title="Send (Enter)"
          >
            {isStreaming ? (
              <Loader2 size={18} className="spin-animate" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
        <div className="tutor-input-footer">
          <span>Press <strong>Enter</strong> to send • <strong>Shift + Enter</strong> for new line</span>
          <span>Context-Aware AI Tutor • RAG Question Bank & Gemini Integration</span>
        </div>
      </div>
    </div>
  );
};
