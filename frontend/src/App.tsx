import React, { useState } from 'react';
import { Sparkles, Activity, BookOpen, GraduationCap } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { QuizGeneratorChat } from './components/QuizGeneratorChat';
import { QuizPlayer } from './components/QuizPlayer';
import { QuizData } from './api/quizApi';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'quiz' | 'dashboard'>('quiz');
  const [activeQuiz, setActiveQuiz] = useState<QuizData | null>(null);

  const handleQuizGenerated = (quiz: QuizData) => {
    setActiveQuiz(quiz);
  };

  const handleResetQuiz = () => {
    setActiveQuiz(null);
  };

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-icon">
            <GraduationCap size={24} />
          </div>
          <div className="brand-text">
            <span className="brand-name">EduAI Quiz Tutor</span>
            <span className="brand-tag">PostgreSQL • NVIDIA AI • RAG</span>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            className={`nav-tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
            onClick={() => setActiveTab('quiz')}
          >
            <Sparkles size={16} /> AI Quiz Studio
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={16} /> Infrastructure
          </button>
        </nav>
      </header>

      {/* Main View Area */}
      <main className="main-content">
        {activeTab === 'quiz' ? (
          <div className="quiz-view-container">
            {activeQuiz ? (
              <QuizPlayer quiz={activeQuiz} onReset={handleResetQuiz} />
            ) : (
              <QuizGeneratorChat onQuizGenerated={handleQuizGenerated} />
            )}
          </div>
        ) : (
          <Dashboard />
        )}
      </main>
    </div>
  );
};

export default App;
