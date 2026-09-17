import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Sparkles,
  HelpCircle,
  Trophy,
  BookOpen,
  Award,
  MessageSquare
} from 'lucide-react';
import {
  QuizData,
  QuizQuestion,
  submitQuizAnswer,
  AnswerSubmissionResult
} from '../api/quizApi';
import { getAIExplanation, AIExplanation } from '../api/aiApi';
import { AITutorDrawer } from './AITutorDrawer';

interface QuizPlayerProps {
  quiz: QuizData;
  onReset: () => void;
}

export const QuizPlayer: React.FC<QuizPlayerProps> = ({ quiz, onReset }) => {
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, AnswerSubmissionResult>>({});
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [aiExplanations, setAiExplanations] = useState<Record<string, AIExplanation>>({});
  const [loadingAi, setLoadingAi] = useState<boolean>(false);
  const [isTutorOpen, setIsTutorOpen] = useState<boolean>(false);
  const [showSummaryModal, setShowSummaryModal] = useState<boolean>(false);

  const currentQ: QuizQuestion | undefined = quiz.questions[currentIndex];
  const currentAnswer: AnswerSubmissionResult | undefined = currentQ ? answers[currentQ.id] : undefined;
  const currentAiExp: AIExplanation | undefined = currentQ ? aiExplanations[currentQ.id] : undefined;

  // Normalized option helper
  const parseOption = (opt: any, index: number): { label: string; text: string; full: string } => {
    if (typeof opt === 'string') {
      const match = opt.match(/^([A-D])[\.\:\)]\s*(.*)$/i);
      if (match) {
        return { label: match[1].toUpperCase(), text: match[2], full: opt };
      }
      const labels = ['A', 'B', 'C', 'D', 'E'];
      return { label: labels[index] || `O${index + 1}`, text: opt, full: opt };
    } else if (opt && typeof opt === 'object') {
      const key = opt.Key || opt.key || opt.label || String.fromCharCode(65 + index);
      const text = opt.Text || opt.text || opt.value || JSON.stringify(opt);
      return { label: key, text: text, full: `${key}. ${text}` };
    }
    return { label: `${index + 1}`, text: String(opt), full: String(opt) };
  };

  const handleSelectOption = async (optionRaw: any, parsedLabel: string) => {
    if (!currentQ || currentAnswer || evaluating) return;

    setEvaluating(true);
    try {
      const result = await submitQuizAnswer(quiz.id, currentQ.id, optionRaw);
      setAnswers((prev) => ({ ...prev, [currentQ.id]: result }));

      // Automatically request AI explanation if answer is wrong
      if (!result.is_correct && !aiExplanations[currentQ.id]) {
        fetchAiExplanation(currentQ.id, parsedLabel);
      }
    } catch (err) {
      console.error('Failed to submit answer:', err);
    } finally {
      setEvaluating(false);
    }
  };

  const fetchAiExplanation = async (qId: string, userAns: string) => {
    setLoadingAi(true);
    try {
      const exp = await getAIExplanation(qId, userAns);
      setAiExplanations((prev) => ({ ...prev, [qId]: exp }));
    } catch (err) {
      console.error('Failed to fetch AI explanation:', err);
    } finally {
      setLoadingAi(false);
    }
  };

  const calculateScore = () => {
    return Object.values(answers).filter((a) => a.is_correct).length;
  };

  const isOptionSelected = (parsedLabel: string, parsedText: string) => {
    if (!currentAnswer) return false;
    const sel = currentAnswer.selected_answer;
    if (typeof sel === 'string') {
      return sel.toLowerCase().includes(parsedLabel.toLowerCase()) || sel.toLowerCase() === parsedText.toLowerCase();
    } else if (sel && typeof sel === 'object') {
      return (sel.Key === parsedLabel || sel.Text === parsedText);
    }
    return false;
  };

  const isOptionCorrect = (parsedLabel: string, parsedText: string) => {
    if (!currentAnswer || !currentAnswer.correct_answer) return false;
    const corr = currentAnswer.correct_answer.toLowerCase();
    return (
      corr === parsedLabel.toLowerCase() ||
      corr.startsWith(`${parsedLabel.toLowerCase()}.`) ||
      corr.includes(parsedText.toLowerCase()) ||
      parsedText.toLowerCase().includes(corr)
    );
  };

  const answeredCount = Object.keys(answers).length;
  const progressPercent = Math.round(((currentIndex + 1) / quiz.total_questions) * 100);

  if (!currentQ) {
    return (
      <div className="quiz-empty-card">
        <p>No questions available for this quiz.</p>
        <button className="btn-primary" onClick={onReset}>
          Create New Quiz
        </button>
      </div>
    );
  }

  const rawOptions: any[] = Array.isArray(currentQ.options) ? currentQ.options : [];

  return (
    <div className="quiz-player-container">
      {/* Top Navigation & Score Bar */}
      <div className="quiz-top-bar">
        <div className="quiz-meta-info">
          <button className="btn-back-quiz" onClick={onReset} title="Exit Quiz">
            <RotateCcw size={16} /> New Quiz
          </button>
          <span className="quiz-title-badge">{quiz.title}</span>
        </div>

        <div className="quiz-score-badge">
          <Trophy size={16} className="score-icon" />
          <span>
            Score: <strong>{calculateScore()}</strong> / {answeredCount}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-container">
        <div className="progress-label-row">
          <span>
            Question <strong>{currentIndex + 1}</strong> of {quiz.total_questions}
          </span>
          <span>{progressPercent}% Complete</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
        </div>
      </div>

      {/* Main Single Question Card */}
      <div className="question-card">
        {/* Meta tags header */}
        <div className="question-meta-tags">
          <span className="meta-tag subject">{currentQ.subject}</span>
          <span className="meta-tag topic">{currentQ.topic}</span>
          <span className={`meta-tag difficulty ${currentQ.difficulty.toLowerCase()}`}>
            {currentQ.difficulty}
          </span>
          {currentQ.is_pyq && (
            <span className="meta-tag pyq">
              🏛️ PYQ {currentQ.exam_name ? `• ${currentQ.exam_name}` : ''} {currentQ.exam_year || ''}
            </span>
          )}
        </div>

        {/* Question Text */}
        <div className="question-body">
          <h2 className="question-text">{currentQ.question_text}</h2>
        </div>

        {/* Options List */}
        <div className="options-grid">
          {rawOptions.map((optRaw, idx) => {
            const parsed = parseOption(optRaw, idx);
            const isSelected = isOptionSelected(parsed.label, parsed.text);
            const isCorrect = isOptionCorrect(parsed.label, parsed.text);
            const isAnswered = !!currentAnswer;

            let optionClass = 'option-btn';
            if (isAnswered) {
              if (isSelected && currentAnswer.is_correct) {
                optionClass += ' correct-selected'; // GREEN
              } else if (isSelected && !currentAnswer.is_correct) {
                optionClass += ' wrong-selected'; // RED
              } else if (!isSelected && isCorrect) {
                optionClass += ' correct-revealed'; // GREEN
              } else {
                optionClass += ' disabled-other';
              }
            }

            return (
              <button
                key={idx}
                className={optionClass}
                onClick={() => handleSelectOption(optRaw, parsed.label)}
                disabled={isAnswered || evaluating}
              >
                <span className="option-label-circle">{parsed.label}</span>
                <span className="option-text">{parsed.text}</span>

                {isAnswered && isSelected && currentAnswer.is_correct && (
                  <CheckCircle2 className="feedback-icon correct" size={20} />
                )}
                {isAnswered && isSelected && !currentAnswer.is_correct && (
                  <XCircle className="feedback-icon wrong" size={20} />
                )}
                {isAnswered && !isSelected && isCorrect && (
                  <span className="correct-answer-pill">Correct Answer</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Immediate Feedback & Explanation Section */}
        {currentAnswer && (
          <div className={`answer-feedback-box ${currentAnswer.is_correct ? 'success' : 'failure'}`}>
            <div className="feedback-title-row">
              {currentAnswer.is_correct ? (
                <div className="feedback-status-title success">
                  <CheckCircle2 size={20} /> Correct Answer! Great job.
                </div>
              ) : (
                <div className="feedback-status-title failure">
                  <XCircle size={20} /> Incorrect. The correct answer is{' '}
                  <span className="highlight-correct">{currentAnswer.correct_answer}</span>.
                </div>
              )}
            </div>

            {/* Official DB Explanation */}
            {currentAnswer.explanation && (
              <div className="explanation-content">
                <strong>Explanation:</strong>
                <p>{currentAnswer.explanation}</p>
              </div>
            )}

            {/* AI Deep Explanation Section */}
            {currentAiExp ? (
              <div className="ai-deep-explanation-card">
                <div className="ai-exp-header">
                  <Sparkles size={16} className="sparkle-icon" />
                  <span>AI Tutor Deep Analysis</span>
                </div>
                <div className="ai-exp-sections">
                  {!currentAnswer.is_correct && (
                    <div className="ai-exp-row">
                      <span className="ai-exp-label red">Why Your Choice was Incorrect:</span>
                      <p>{currentAiExp.why_wrong}</p>
                    </div>
                  )}
                  <div className="ai-exp-row">
                    <span className="ai-exp-label green">Why the Right Answer is Correct:</span>
                    <p>{currentAiExp.why_correct}</p>
                  </div>
                  <div className="ai-exp-row takeaway">
                    <span className="ai-exp-label purple">💡 Key Exam Takeaway:</span>
                    <p>{currentAiExp.key_takeaway}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="ai-action-bar">
                <button
                  className="btn-ask-ai-deep"
                  onClick={() =>
                    fetchAiExplanation(
                      currentQ.id,
                      typeof currentAnswer.selected_answer === 'string'
                        ? currentAnswer.selected_answer
                        : 'Option'
                    )
                  }
                  disabled={loadingAi}
                >
                  {loadingAi ? (
                    'Analyzing with AI...'
                  ) : (
                    <>
                      <Sparkles size={16} /> Ask AI Deep Explanation
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* AI Tutor Doubt Resolver Floating Trigger Bar */}
        <div className="tutor-callout-row">
          <div className="callout-text">
            <HelpCircle size={16} /> Have doubts about this question or topic?
          </div>
          <button className="btn-open-tutor" onClick={() => setIsTutorOpen(true)}>
            <MessageSquare size={16} /> Ask AI Tutor Doubt
          </button>
        </div>
      </div>

      {/* Navigation Controls: Prev, Question Dots, Next */}
      <div className="quiz-controls-bar">
        <button
          className="nav-btn prev"
          onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
          disabled={currentIndex === 0}
        >
          <ChevronLeft size={20} /> Previous
        </button>

        {/* Question Dot Navigator */}
        <div className="question-dots-nav">
          {quiz.questions.map((q, idx) => {
            const ans = answers[q.id];
            let dotClass = 'q-dot';
            if (idx === currentIndex) dotClass += ' active';
            if (ans) {
              dotClass += ans.is_correct ? ' correct' : ' wrong';
            }
            return (
              <button
                key={idx}
                className={dotClass}
                onClick={() => setCurrentIndex(idx)}
                title={`Question ${idx + 1}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>

        {currentIndex < quiz.total_questions - 1 ? (
          <button
            className="nav-btn next"
            onClick={() => setCurrentIndex((prev) => Math.min(quiz.total_questions - 1, prev + 1))}
          >
            Next <ChevronRight size={20} />
          </button>
        ) : (
          <button
            className="nav-btn finish"
            onClick={() => setShowSummaryModal(true)}
          >
            <Trophy size={18} /> Finish Quiz
          </button>
        )}
      </div>

      {/* AI Tutor Chatbot Drawer */}
      <AITutorDrawer
        question={currentQ}
        userAnswer={currentAnswer?.selected_answer}
        isOpen={isTutorOpen}
        onClose={() => setIsTutorOpen(false)}
      />

      {/* Summary / Result Modal */}
      {showSummaryModal && (
        <div className="modal-overlay">
          <div className="summary-modal-card">
            <div className="modal-trophy">
              <Award size={48} />
            </div>
            <h2>Quiz Completed!</h2>
            <p className="summary-sub">{quiz.title}</p>

            <div className="score-circle">
              <div className="score-num">{calculateScore()}</div>
              <div className="score-den">out of {quiz.total_questions}</div>
            </div>

            <p className="summary-feedback">
              {calculateScore() === quiz.total_questions
                ? '🏆 Outstanding! Perfect score!'
                : calculateScore() >= quiz.total_questions / 2
                ? '👍 Good job! Review your mistakes with the AI Tutor.'
                : '📚 Keep practicing! You can chat with the AI Tutor on missed questions.'}
            </p>

            <div className="modal-actions">
              <button
                className="btn-modal-review"
                onClick={() => setShowSummaryModal(false)}
              >
                Review Questions
              </button>
              <button className="btn-modal-restart" onClick={onReset}>
                Generate Another Quiz
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
