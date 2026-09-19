import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Database, FileJson, LoaderCircle, UploadCloud, XCircle } from 'lucide-react';
import { getImportStatus, importQuestions, QuestionImportResult } from '../api/questionApi';

export const QuestionBankImport: React.FC = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QuestionImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!result || (result.status !== 'queued' && result.status !== 'processing')) return;
    const timer = window.setInterval(async () => {
      try {
        const next = await getImportStatus(result.job_id);
        setResult(next);
        if (next.status === 'completed' || next.status === 'failed') {
          setLoading(false);
          window.clearInterval(timer);
          if (next.status === 'failed') setError(next.message);
        }
      } catch (err: any) {
        setLoading(false);
        setError(err.response?.data?.detail || 'Could not read import progress.');
        window.clearInterval(timer);
      }
    }, 1500);
    return () => window.clearInterval(timer);
  }, [result]);

  const handleFile = async (file?: File) => {
    if (!file) return;
    setFileName(file.name);
    setResult(null);
    setError(null);
    setLoading(true);
    try {
      setResult(await importQuestions(file));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed. Check the JSON structure and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="import-view">
      <div className="import-hero">
        <div className="import-icon"><FileJson size={28} /></div>
        <div>
          <p className="eyebrow">Question bank</p>
          <h1>Load a new question set</h1>
          <p>Upload a JSON file using the same <strong>Questions</strong>, translations, options, and metadata structure as the current question bank.</p>
        </div>
      </div>

      <div className="import-grid">
        <button className="upload-zone" onClick={() => inputRef.current?.click()} disabled={loading}>
          {loading ? <LoaderCircle className="spin" size={34} /> : <UploadCloud size={34} />}
          <span>{loading ? 'Indexing questions...' : 'Choose JSON file'}</span>
          <small>{fileName || 'The file will be stored with embeddings in PostgreSQL'}</small>
          <input ref={inputRef} type="file" accept=".json,application/json" hidden onChange={(event) => handleFile(event.target.files?.[0])} />
        </button>

        <div className="import-steps">
          <div><Database size={18} /><span><strong>Validate</strong><small>Checks the Questions array and English translations.</small></span></div>
          <div><Database size={18} /><span><strong>Store</strong><small>Upserts normalized questions in PostgreSQL.</small></span></div>
          <div><Database size={18} /><span><strong>Embed</strong><small>Creates Google embeddings in PostgreSQL.</small></span></div>
        </div>
      </div>

      {result && result.status !== 'failed' && <div className={`import-result ${result.status === 'completed' ? 'success' : 'progress'}`}><CheckCircle2 size={20} /><div><strong>{result.message || `Import ${result.status}...`}</strong><span>{result.imported}/{result.total} questions stored and {result.embedded}/{result.total} embeddings indexed in <code>{result.collection}</code>.</span></div></div>}
      {error && <div className="import-result failure"><XCircle size={20} /><span>{error}</span></div>}
    </section>
  );
};