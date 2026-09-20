import React, { useState, useEffect } from 'react';
import { Sparkles, Activity, FileJson, GraduationCap, Bot, FileText, Sun, Moon } from 'lucide-react';
import { Dashboard } from './components/Dashboard';
import { QuizGeneratorChat } from './components/QuizGeneratorChat';
import { QuizPlayer } from './components/QuizPlayer';
import { QuizData } from './api/quizApi';
import { QuestionBankImport } from './components/QuestionBankImport';
import { AITutorChat } from './components/AITutorChat';
import { PDFQuizStudio } from './components/PDFQuizStudio';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tutor' | 'pdf' | 'quiz' | 'import' | 'dashboard'>('tutor');
  const [activeQuiz, setActiveQuiz] = useState<QuizData | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('eduai_theme') as 'light' | 'dark') || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('eduai_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const handleQuizGenerated = (quiz: QuizData) => {
    setActiveQuiz(quiz);
    setActiveTab('quiz');
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
            <span className="brand-name">EduAI Studio</span>
            <span className="brand-tag">NVIDIA NIM • PostgreSQL • DocuQuiz AI</span>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            className={`nav-tab-btn ${activeTab === 'tutor' ? 'active' : ''}`}
            onClick={() => setActiveTab('tutor')}
          >
            <Bot size={16} /> AI Tutor Chat
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'pdf' ? 'active' : ''}`}
            onClick={() => setActiveTab('pdf')}
          >
            <FileText size={16} /> DocuQuiz AI (PDF)
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
            onClick={() => setActiveTab('quiz')}
          >
            <Sparkles size={16} /> AI Quiz Studio
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'import' ? 'active' : ''}`}
            onClick={() => setActiveTab('import')}
          >
            <FileJson size={16} /> Question Bank
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={16} /> Infrastructure
          </button>
        </nav>

        <div className="nav-actions">
          <button
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
            aria-label="Toggle theme"
          >
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
            <span className="theme-toggle-label">{theme === 'light' ? 'Dark' : 'Light'}</span>
          </button>
        </div>
      </header>

      {/* Main View Area */}
      <main className="main-content">
        {activeTab === 'tutor' ? (
          <AITutorChat onStartQuiz={handleQuizGenerated} />
        ) : activeTab === 'pdf' ? (
          <PDFQuizStudio onStartQuiz={handleQuizGenerated} />
        ) : activeTab === 'quiz' ? (
          <div className="quiz-view-container">
            {activeQuiz ? (
              <QuizPlayer quiz={activeQuiz} onReset={handleResetQuiz} />
            ) : (
              <QuizGeneratorChat onQuizGenerated={handleQuizGenerated} />
            )}
          </div>
        ) : activeTab === 'import' ? (
          <QuestionBankImport />
        ) : (
          <Dashboard />
        )}
      </main>
    </div>
  );
};

export default App;
