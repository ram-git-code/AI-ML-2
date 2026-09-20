import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Sparkles,
  Layers,
  BookOpen,
  CheckCircle2,
  Trash2,
  AlertCircle,
  Clock,
  HelpCircle,
  FileCheck,
  ChevronRight,
  ChevronLeft,
  ListFilter,
  BrainCircuit,
  Zap,
  Search,
  Download,
  Copy,
  Check,
  RotateCw,
  Eye,
  Sliders,
  Sparkle
} from 'lucide-react';
import { documentApi, DocumentInfo, DocumentDetail } from '../api/documentApi';
import { QuizData } from '../api/quizApi';

interface PDFQuizStudioProps {
  onStartQuiz: (quiz: QuizData) => void;
}

export const PDFQuizStudio: React.FC<PDFQuizStudioProps> = ({ onStartQuiz }) => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedDocDetail, setSelectedDocDetail] = useState<DocumentDetail | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [questionCount, setQuestionCount] = useState<number>(5);
  const [difficulty, setDifficulty] = useState<string>('medium');
  const [focusTopic, setFocusTopic] = useState<string>('');
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [quizError, setQuizError] = useState<string | null>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'insights' | 'flashcards' | 'chunks'>('summary');
  const [chunkSearchQuery, setChunkSearchQuery] = useState('');
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [activeFlashcardIndex, setActiveFlashcardIndex] = useState(0);
  const [isCardFlipped, setIsCardFlipped] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const list = await documentApi.listDocuments();
      setDocuments(list);
      if (list.length > 0 && !selectedDocId) {
        selectDocument(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const selectDocument = async (id: string) => {
    setSelectedDocId(id);
    setSelectedDocDetail(null);
    setQuizError(null);
    setActiveFlashcardIndex(0);
    setIsCardFlipped(false);
    try {
      const detail = await documentApi.getDocument(id);
      setSelectedDocDetail(detail);
      if (detail.topics && detail.topics.length > 0) {
        setFocusTopic(detail.topics[0]);
      } else {
        setFocusTopic('');
      }
    } catch (err) {
      console.error('Failed to get document detail:', err);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF files (.pdf) are supported.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadProgress('Uploading and extracting PDF text...');

    try {
      setUploadProgress('Chunking text & computing NVIDIA vector embeddings...');
      const newDoc = await documentApi.uploadDocument(file);
      setUploadProgress('AI Document Analysis complete!');
      await loadDocuments();
      await selectDocument(newDoc.id);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to upload and analyze PDF.';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
      setUploadProgress('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this document and its embeddings?')) return;
    try {
      await documentApi.deleteDocument(docId);
      const remaining = documents.filter((d) => d.id !== docId);
      setDocuments(remaining);
      if (selectedDocId === docId) {
        if (remaining.length > 0) {
          selectDocument(remaining[0].id);
        } else {
          setSelectedDocId(null);
          setSelectedDocDetail(null);
        }
      }
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const handleGenerateQuiz = async () => {
    if (!selectedDocId) return;
    setIsGeneratingQuiz(true);
    setQuizError(null);

    try {
      const effectiveTopic = focusTopic.trim()
        ? customInstructions.trim()
          ? `${focusTopic.trim()} (Special note: ${customInstructions.trim()})`
          : focusTopic.trim()
        : customInstructions.trim() || undefined;

      const quiz = await documentApi.generateDocumentQuiz(selectedDocId, {
        question_count: questionCount,
        difficulty: difficulty,
        focus_topic: effectiveTopic,
      });
      onStartQuiz(quiz);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to generate quiz from PDF.';
      setQuizError(msg);
    } finally {
      setIsGeneratingQuiz(false);
    }
  };

  const handleCopySummary = () => {
    if (!selectedDocDetail) return;
    const textToCopy = `# ${selectedDocDetail.title}\n\n## Executive Summary\n${selectedDocDetail.summary}\n\n## Core Topics\n${selectedDocDetail.topics?.map(t => `- ${t}`).join('\n')}\n\n## Key Insights & Formulas\n${selectedDocDetail.key_insights?.map((ins, i) => `${i+1}. ${ins}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
  };

  const handleDownloadStudyNotes = () => {
    if (!selectedDocDetail) return;
    const content = `# Study Guide: ${selectedDocDetail.title}
Generated by EduAI Studio (NVIDIA NIM AI)
Date: ${new Date().toLocaleDateString()}

---

## 📌 Document Overview
- **Filename**: ${selectedDocDetail.filename}
- **Pages**: ${selectedDocDetail.page_count}
- **Semantic Chunks**: ${selectedDocDetail.chunk_count}
- **Difficulty**: ${selectedDocDetail.estimated_difficulty}

---

## 📖 Executive Summary
${selectedDocDetail.summary || 'Summary not available.'}

---

## 🎯 Core Topics
${selectedDocDetail.topics?.map(t => `- **${t}**`).join('\n') || '- General Academic Knowledge'}

---

## 💡 Key High-Yield Formulas & Insights
${selectedDocDetail.key_insights?.map((ins, idx) => `### ${idx + 1}. Concept ${idx + 1}\n${ins}\n`).join('\n') || 'No specific insights recorded.'}

---
*Ready to test yourself? Use EduAI Studio to generate dynamic interactive practice quizzes based on these notes.*
`;

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedDocDetail.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_study_guide.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const filteredChunks = selectedDocDetail?.chunks.filter((c) =>
    c.chunk_text.toLowerCase().includes(chunkSearchQuery.toLowerCase())
  ) || [];

  // Prepare Flashcards from insights & topics
  const flashcards = selectedDocDetail
    ? [
        ...(selectedDocDetail.key_insights || []).map((ins, idx) => ({
          title: `Key Insight #${idx + 1}`,
          category: selectedDocDetail.topics?.[idx % (selectedDocDetail.topics.length || 1)] || 'Core Concept',
          front: ins.length > 80 ? `${ins.slice(0, 75)}...?` : `Explain: "${ins}"`,
          back: ins,
        })),
        ...(selectedDocDetail.topics || []).map((t, idx) => ({
          title: `Topic Breakdown #${idx + 1}`,
          category: 'Curriculum Topic',
          front: `What are the key principles of "${t}" according to this document?`,
          back: `This document explores ${t} with practical applications and core definitions outlined in the executive summary.`,
        })),
      ]
    : [];

  return (
    <div className="pdf-studio-container">
      {/* Sidebar / Document Library */}
      <aside className="pdf-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title-row">
            <BookOpen size={18} className="icon-glow-cyan" />
            <h3>Document Library</h3>
          </div>
          <span className="badge-count">{documents.length} Files</span>
        </div>

        {/* Upload Trigger Area */}
        <div
          className={`dropzone-card-mini ${isDragging ? 'drag-over' : ''}`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".pdf"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
              }
            }}
          />
          <UploadCloud size={24} className="dropzone-icon-pulse" />
          <div className="dropzone-mini-text">
            <strong>Upload PDF Study Note</strong>
            <span>Drag & drop or browse</span>
          </div>
        </div>

        {uploadError && (
          <div className="alert-banner error-banner-mini">
            <AlertCircle size={14} />
            <span>{uploadError}</span>
          </div>
        )}

        {isUploading && (
          <div className="upload-progress-box">
            <div className="progress-spinner" />
            <span>{uploadProgress || 'Processing document...'}</span>
          </div>
        )}

        {/* Document List */}
        <div className="doc-list-scroll">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`doc-item-card ${selectedDocId === doc.id ? 'active' : ''}`}
              onClick={() => selectDocument(doc.id)}
            >
              <div className="doc-item-icon">
                <FileText size={18} />
              </div>
              <div className="doc-item-meta">
                <span className="doc-item-title" title={doc.title}>
                  {doc.title}
                </span>
                <div className="doc-item-sub">
                  <span>{doc.page_count} pgs</span>
                  <span>•</span>
                  <span>{formatBytes(doc.file_size_bytes)}</span>
                  <span>•</span>
                  <span>{doc.chunk_count} vectors</span>
                </div>
              </div>
              <button
                className="doc-delete-btn"
                title="Delete document"
                onClick={(e) => handleDelete(doc.id, e)}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}

          {documents.length === 0 && !isUploading && (
            <div className="empty-docs-placeholder">
              <Layers size={32} />
              <p>No PDFs uploaded yet.</p>
              <small>Upload syllabus notes, research papers, or chapter PDFs.</small>
            </div>
          )}
        </div>
      </aside>

      {/* Main Analysis & Quiz Generation Area */}
      <main className="pdf-main-panel">
        {selectedDocDetail ? (
          <div className="doc-workspace">
            {/* Document Header Card */}
            <div className="glass-card doc-hero-card">
              <div className="doc-hero-top">
                <div className="doc-badge-row">
                  <span className="tag-badge tag-cyan">
                    <FileCheck size={12} /> {selectedDocDetail.page_count} Pages
                  </span>
                  <span className="tag-badge tag-indigo">
                    <Layers size={12} /> {selectedDocDetail.chunk_count} Semantic Chunks
                  </span>
                  <span className="tag-badge tag-emerald">
                    <BrainCircuit size={12} /> NVIDIA NIM Embeddings
                  </span>
                  <span className="tag-badge tag-amber">
                    <Zap size={12} /> {selectedDocDetail.estimated_difficulty} Difficulty
                  </span>
                </div>
                
                <div className="doc-header-actions">
                  <button
                    className="btn-doc-action"
                    onClick={handleCopySummary}
                    title="Copy Study Guide Summary"
                  >
                    {copiedSummary ? <Check size={14} className="text-emerald" /> : <Copy size={14} />}
                    <span>{copiedSummary ? 'Copied!' : 'Copy Summary'}</span>
                  </button>

                  <button
                    className="btn-doc-action"
                    onClick={handleDownloadStudyNotes}
                    title="Download Structured Study Notes"
                  >
                    <Download size={14} />
                    <span>Download Notes</span>
                  </button>
                </div>
              </div>

              <h2 className="doc-hero-title">{selectedDocDetail.title}</h2>
              <span className="doc-filename-sub">{selectedDocDetail.filename} ({formatBytes(selectedDocDetail.file_size_bytes)})</span>

              {/* Navigation Tabs */}
              <div className="doc-tabs-bar">
                <button
                  className={`doc-tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
                  onClick={() => setActiveTab('summary')}
                >
                  <Sparkles size={14} /> Executive Summary & Topics
                </button>
                <button
                  className={`doc-tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
                  onClick={() => setActiveTab('insights')}
                >
                  <BrainCircuit size={14} /> Key Formulas & Insights
                </button>
                <button
                  className={`doc-tab-btn ${activeTab === 'flashcards' ? 'active' : ''}`}
                  onClick={() => setActiveTab('flashcards')}
                >
                  <Sparkle size={14} /> 🎴 Flashcards Study Mode ({flashcards.length})
                </button>
                <button
                  className={`doc-tab-btn ${activeTab === 'chunks' ? 'active' : ''}`}
                  onClick={() => setActiveTab('chunks')}
                >
                  <ListFilter size={14} /> Semantic Vector Chunks ({selectedDocDetail.chunks.length})
                </button>
              </div>
            </div>

            {/* Tab Contents */}
            <div className="doc-tab-body">
              {activeTab === 'summary' && (
                <div className="tab-pane-content">
                  <div className="glass-card summary-card">
                    <div className="section-title-row">
                      <h4 className="section-label">
                        <Sparkles size={16} className="icon-glow-indigo" /> AI Document Summary
                      </h4>
                    </div>
                    <p className="summary-paragraph">
                      {selectedDocDetail.summary || 'Summary not available.'}
                    </p>

                    <h4 className="section-label mt-4">
                      <Layers size={16} className="icon-glow-cyan" /> Core Topics Covered
                    </h4>
                    <p className="topics-hint-text">Click any topic to focus your AI Quiz on that specific area:</p>
                    <div className="topics-cloud">
                      {selectedDocDetail.topics && selectedDocDetail.topics.length > 0 ? (
                        selectedDocDetail.topics.map((t, i) => (
                          <button
                            key={i}
                            className={`topic-pill ${focusTopic === t ? 'selected' : ''}`}
                            onClick={() => setFocusTopic(t)}
                            title="Click to select as focus topic for quiz"
                          >
                            {t}
                          </button>
                        ))
                      ) : (
                        <span className="text-muted">General Topic</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'insights' && (
                <div className="tab-pane-content">
                  <div className="glass-card insights-card">
                    <h4 className="section-label">
                      <Zap size={16} className="icon-glow-emerald" /> High-Yield Concepts & Takeaways
                    </h4>
                    <div className="insights-grid">
                      {selectedDocDetail.key_insights && selectedDocDetail.key_insights.length > 0 ? (
                        selectedDocDetail.key_insights.map((insight, idx) => (
                          <div key={idx} className="insight-item">
                            <div className="insight-number">{idx + 1}</div>
                            <div className="insight-text">{insight}</div>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted">No specific formulas or insights extracted.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'flashcards' && (
                <div className="tab-pane-content">
                  <div className="glass-card flashcard-studio-card">
                    <div className="flashcard-header">
                      <div>
                        <h4 className="section-label">Interactive Flashcards Studio</h4>
                        <p className="flashcard-sub">Flip cards to test your memory on definitions and formulas before taking the quiz.</p>
                      </div>
                      <span className="flashcard-counter-badge">
                        Card {flashcards.length > 0 ? activeFlashcardIndex + 1 : 0} of {flashcards.length}
                      </span>
                    </div>

                    {flashcards.length > 0 ? (
                      <div className="flashcard-interactive-area">
                        <div
                          className={`flashcard-3d-box ${isCardFlipped ? 'flipped' : ''}`}
                          onClick={() => setIsCardFlipped(!isCardFlipped)}
                        >
                          <div className="flashcard-inner">
                            {/* Front */}
                            <div className="flashcard-face flashcard-front">
                              <span className="flashcard-tag">{flashcards[activeFlashcardIndex].category}</span>
                              <h3 className="flashcard-question">{flashcards[activeFlashcardIndex].front}</h3>
                              <span className="flashcard-flip-prompt">
                                <RotateCw size={14} /> Click card to flip and reveal answer
                              </span>
                            </div>

                            {/* Back */}
                            <div className="flashcard-face flashcard-back">
                              <span className="flashcard-tag-back">Authoritative Solution</span>
                              <p className="flashcard-answer-text">{flashcards[activeFlashcardIndex].back}</p>
                              <span className="flashcard-flip-prompt">
                                <RotateCw size={14} /> Click card to flip back
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Flashcard Navigation */}
                        <div className="flashcard-controls">
                          <button
                            className="btn-flash-nav"
                            disabled={activeFlashcardIndex === 0}
                            onClick={() => {
                              setIsCardFlipped(false);
                              setActiveFlashcardIndex((prev) => Math.max(0, prev - 1));
                            }}
                          >
                            <ChevronLeft size={16} /> Previous Card
                          </button>

                          <button
                            className="btn-flash-flip"
                            onClick={() => setIsCardFlipped(!isCardFlipped)}
                          >
                            <RotateCw size={16} /> Flip ({isCardFlipped ? 'Front' : 'Back'})
                          </button>

                          <button
                            className="btn-flash-nav"
                            disabled={activeFlashcardIndex === flashcards.length - 1}
                            onClick={() => {
                              setIsCardFlipped(false);
                              setActiveFlashcardIndex((prev) => Math.min(flashcards.length - 1, prev + 1));
                            }}
                          >
                            Next Card <ChevronRight size={16} />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-muted">No flashcard data available for this document.</p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'chunks' && (
                <div className="tab-pane-content">
                  <div className="chunks-search-bar">
                    <Search size={16} className="text-muted" />
                    <input
                      type="text"
                      className="chunk-search-input"
                      placeholder="Search semantic chunks by keywords (e.g. formula, definition, page number)..."
                      value={chunkSearchQuery}
                      onChange={(e) => setChunkSearchQuery(e.target.value)}
                    />
                    {chunkSearchQuery && (
                      <span className="chunk-match-count">{filteredChunks.length} matches</span>
                    )}
                  </div>

                  <div className="chunks-list-grid">
                    {filteredChunks.map((chunk) => (
                      <div key={chunk.id} className="glass-card chunk-card">
                        <div className="chunk-header">
                          <span className="chunk-page-tag">Page {chunk.page_number}</span>
                          <span className="chunk-index-tag">Chunk #{chunk.chunk_index + 1}</span>
                        </div>
                        <p className="chunk-text-body">{chunk.chunk_text}</p>
                      </div>
                    ))}
                    {filteredChunks.length === 0 && (
                      <p className="text-muted col-span-2">No chunks matching "{chunkSearchQuery}"</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Quiz Generator Footer Panel */}
            <div className="glass-card quiz-generator-card">
              <div className="quiz-generator-header">
                <div className="qg-title-group">
                  <Sparkles size={20} className="icon-glow-indigo" />
                  <div>
                    <h3>Create Interactive Quiz from this PDF</h3>
                    <p>NVIDIA NIM will generate MCQs with authoritative citations grounded directly in this document.</p>
                  </div>
                </div>
              </div>

              {quizError && (
                <div className="alert-banner error-banner">
                  <AlertCircle size={16} />
                  <span>{quizError}</span>
                </div>
              )}

              <div className="quiz-controls-row">
                <div className="control-group">
                  <label>Question Count ({questionCount})</label>
                  <div className="count-selector-buttons">
                    {[3, 5, 8, 10, 15].map((cnt) => (
                      <button
                        key={cnt}
                        type="button"
                        className={`count-btn ${questionCount === cnt ? 'active' : ''}`}
                        onClick={() => setQuestionCount(cnt)}
                      >
                        {cnt}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="control-group">
                  <label>Difficulty</label>
                  <div className="difficulty-pill-group">
                    {['easy', 'medium', 'hard'].map((diff) => (
                      <button
                        key={diff}
                        type="button"
                        className={`diff-btn ${diff} ${difficulty === diff ? 'active' : ''}`}
                        onClick={() => setDifficulty(diff)}
                      >
                        {diff.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="control-group flex-1">
                  <label>Focus Topic / Chapter</label>
                  <input
                    type="text"
                    className="cyber-input"
                    placeholder="e.g., Mock Exam Schedule or Key Concepts"
                    value={focusTopic}
                    onChange={(e) => setFocusTopic(e.target.value)}
                  />
                </div>

                <div className="control-group flex-1">
                  <label>Custom Focus (Optional)</label>
                  <input
                    type="text"
                    className="cyber-input"
                    placeholder="e.g. Numerical problems only"
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                  />
                </div>

                <div className="action-button-wrapper">
                  <button
                    className="btn-cyber-primary"
                    disabled={isGeneratingQuiz}
                    onClick={handleGenerateQuiz}
                  >
                    {isGeneratingQuiz ? (
                      <span className="btn-loading-content">
                        <span className="spinner"></span> Building Quiz...
                      </span>
                    ) : (
                      <>
                        <Sparkles size={16} /> Start PDF Quiz <ChevronRight size={16} />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-card empty-workspace">
            <FileText size={48} className="text-muted icon-pulse" />
            <h3>Select or Upload a PDF Study Note</h3>
            <p>Upload lecture notes, textbook chapters, or question papers to analyze concepts and generate targeted quizzes.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default PDFQuizStudio;
