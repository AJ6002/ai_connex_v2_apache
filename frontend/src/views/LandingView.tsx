import React, { useState, useEffect, useRef } from 'react';
import { TasLogo } from '../components/TasLogo';

interface LandingViewProps {
  onNavigateToUpload: (prompt: string, initialInputs?: {
    targetColumn?: string;
    problemType?: string;
    timestampColumn?: string;
    entityColumn?: string;
  }) => void;
}

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  isComplete?: boolean;
  action?: string;
}

/* ─── Copy-to-clipboard helper ──────────────────────────────────────────── */
function useCopyText() {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const copy = (id: string, text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1800);
    });
  };
  return { copiedId, copy };
}

export const LandingView: React.FC<LandingViewProps> = ({ onNavigateToUpload }) => {
  const [sessionId, setSessionId]       = useState<string>('');
  const [conversationId]                = useState<string>(() => `ui_${Date.now()}`);
  const [confidence, setConfidence]     = useState<number>(0.50);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [messages, setMessages]         = useState<Message[]>([{
    id: 'init-1',
    sender: 'ai',
    text: 'Hello! I am the AI Connexx assistant. Tell me what operational task or prediction problem you would like to solve using your dataset today.'
  }]);
  const [inputText, setInputText]       = useState('');
  const [isDragging, setIsDragging]     = useState(false);
  const messagesEndRef                  = useRef<HTMLDivElement>(null);
  const abortControllerRef             = useRef<AbortController | null>(null);
  const textareaRef                     = useRef<HTMLTextAreaElement>(null);
  const { copiedId, copy }              = useCopyText();

  // Gate: conversation is complete when any AI message has isComplete===true
  const conversationComplete = messages.some(m => m.isComplete === true);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  /* ── auto-resize textarea ─────────────────────────────────────────────── */
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputText]);

  const samplePrompts = [
    { text: 'Train a Remaining Useful Life (RUL) predictor for C-MAPSS turbofan engine SCADA logs.', icon: 'speed',    color: '#C8102E', label: 'Regression · RUL' },
    { text: 'Detect anomalies and drifts in multivariate industrial sensor streams.',                icon: 'insights', color: '#1E47C8', label: 'Anomaly Detection' },
    { text: 'Build a failure classification pipeline with custom outlier thresholds.',              icon: 'warning',  color: '#d97706', label: 'Classification' },
  ];

  /* ─── HALT ────────────────────────────────────────────────────────────── */
  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
    setMessages(prev => [...prev, {
      id: `stop-${Date.now()}`,
      sender: 'ai',
      text: '⏹️ Process response generation halted by operator.'
    }]);
  };

  /* ─── SEND TEXT MESSAGE ───────────────────────────────────────────────── */
  const handleSend = async (text: string) => {
    const prompt = text.trim();
    if (!prompt || isGenerating) return;

    const userMsg: Message = { id: `user-${Date.now()}`, sender: 'user', text: prompt };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInputText('');
    setIsGenerating(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch('http://localhost:8000/api/pre_upload/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: prompt, session_id: sessionId, conversation_id: conversationId }),
        signal: controller.signal
      });
      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);

      const missing    = data.missing_information || [];
      const reqMissing = missing.filter((m: string) => m.includes('Required field')).length;
      const filled     = Math.max(0, 4 - reqMissing);
      const conf       = Math.round((0.50 + (filled / 4) * 0.45) * 100) / 100;
      setConfidence(conf);

      // Gate: exit ONLY when conversation_complete = True (not on recommended_next_action)
      // Matches terminal_runner.py line 162: "exit ONLY when conversation_complete = True"
      const isComplete = data.conversation_complete === true;
      setMessages([...updatedMessages, {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: data.reply || 'Request processed successfully.',
        isComplete,
        action: data.recommended_next_action
      }]);
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error(err);
      setMessages([...updatedMessages, {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text: 'Sorry, I encountered an error connecting to the AI Connexx backend (http://localhost:8000). Please verify the server is running.'
      }]);
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  /* ─── UPLOAD FILE ─────────────────────────────────────────────────────── */
  const handleFileUpload = async (file: File) => {
    if (isGenerating) return;
    const userMsg: Message = {
      id: `user-upload-${Date.now()}`,
      sender: 'user',
      text: `📎 Uploaded dataset file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`
    };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsGenerating(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST', body: formData, signal: controller.signal
      });
      const data = await res.json();
      setMessages([...updatedMessages, {
        id: `ai-upload-${Date.now()}`,
        sender: 'ai',
        text: data.reply || `Dataset '${file.name}' successfully uploaded and compiled by Scout Agent!`,
        isComplete: true,
        action: 'dataset_compiled'
      }]);
      setConfidence(0.95);
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      setMessages([...updatedMessages, {
        id: `err-upload-${Date.now()}`,
        sender: 'ai',
        text: `Error uploading dataset '${file.name}'. Please verify the backend is running at http://localhost:8000.`
      }]);
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  /* ─── confidence bar width ────────────────────────────────────────────── */
  const confPct   = Math.round(confidence * 100);
  const confReady = confidence >= 0.91;

  /* ─── keyboard submit (Shift+Enter = newline, Enter = send) ──────────── */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isGenerating && inputText.trim()) handleSend(inputText);
    }
  };

  /* ════════════════════════════════════════════════════════════════════════
     RENDER
  ════════════════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-[85vh] flex flex-col justify-center items-center px-4 relative select-none animate-fadeIn">

      {/* ── Background ambience ─────────────────────────────────────────── */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-tas-red/5   rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-tas-blue/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-3xl w-full space-y-5 relative z-10">

        {/* ── HEADER ──────────────────────────────────────────────────────── */}
        <div className={`flex flex-col items-center gap-2 text-center transition-all duration-500 ${messages.length > 1 ? 'scale-90 opacity-80' : ''}`}>
          <TasLogo className="h-14 animate-pulse" showSubtitle={false} />
          <h1 className="font-headline text-3xl sm:text-4xl font-black tracking-tight text-[#0F172A]">
            <span className="inline-flex items-center gap-1">
              AI&nbsp;<img src="/connexx-dark.png" alt="Connexx" className="h-8 w-auto object-contain inline-block align-middle" />
            </span>
          </h1>
          <p className="text-xs font-mono text-slate-500 max-w-xl">
            Type your operational goals or attach a dataset file — the compiler assigns topology, matches DAG schemas, and compiles training recipes.
          </p>
        </div>

        {/* ── AGENT STATUS BAR (LangUI-style) ─────────────────────────────── */}
        {messages.length > 1 && (
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white/90 px-3 py-2 shadow-sm">
            {/* Left: agent badge */}
            <div className="flex items-center gap-2.5">
              <div className="relative inline-flex shrink-0">
                {/* ping dot */}
                <span className="absolute -bottom-0.5 -right-0.5 flex h-3 w-3">
                  <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${confReady ? 'bg-emerald-400' : 'bg-blue-400'}`} />
                  <span className={`relative inline-flex h-3 w-3 rounded-full ${confReady ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                </span>
                {/* agent avatar */}
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-slate-50 text-xs font-bold">
                  AI
                </div>
              </div>
              <div>
                <p className="text-xs font-bold text-slate-800 leading-tight">AI Connexx CUC Agent</p>
                <p className="text-[10px] text-slate-400 leading-tight font-mono">
                  {confReady ? 'Intent contract complete — ready to compile' : 'Gathering intent & parameter contract…'}
                </p>
              </div>
            </div>

            {/* Right: status badges */}
            <div className="flex items-center gap-2">
              {confReady ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-600/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-700">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-600" />
                  READY
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-600/10 px-2.5 py-1 text-[10px] font-semibold text-blue-700">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse" />
                  IN PROGRESS
                </span>
              )}
              <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-1 rounded-lg">
                {confPct}% confidence
              </span>
            </div>
          </div>
        )}

        {/* ── CHAT WINDOW ────────────────────────────────────────────────── */}
        <div className="rounded-2xl border border-slate-200 bg-slate-50 shadow-xl overflow-hidden flex flex-col" style={{ minHeight: 340, maxHeight: 520 }}>

          {/* messages scroll area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-300">

            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>

                {/* Avatar */}
                {msg.sender === 'ai' ? (
                  <div className="relative inline-flex shrink-0 self-end">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-slate-50 text-xs font-bold shadow">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M11.9936 4.88745C11.9364 4.38234 11.5094 4.00052 11.001 4C10.4927 3.99948 10.0648 4.38042 10.0066 4.88542C9.73542 7.23644 9.03724 8.84929 7.94327 9.94327C6.8493 11.0372 5.23644 11.7354 2.88542 12.0066C2.38042 12.0648 1.99948 12.4927 2 13.001C2.00052 13.5094 2.38234 13.9364 2.88745 13.9936C5.19871 14.2554 6.8483 14.9535 7.97008 16.055C9.08576 17.1505 9.79718 18.761 10.0039 21.0885C10.0498 21.6049 10.4827 22.0006 11.0011 22C11.5196 21.9994 11.9516 21.6027 11.9963 21.0862C12.1943 18.7981 12.9052 17.1513 14.0282 16.0282C15.1513 14.9052 16.7981 14.1943 19.0862 13.9963C19.6027 13.9516 19.9994 13.5196 20 13.0011C20.0006 12.4827 19.6049 12.0498 19.0885 12.0039C16.761 11.7972 15.1505 11.0858 14.055 9.97008C12.9535 8.8483 12.2554 7.19871 11.9936 4.88745Z"/>
                      </svg>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700 text-slate-50 text-xs font-bold shadow shrink-0 self-end">
                    U
                  </div>
                )}

                {/* Bubble */}
                <div className={`group max-w-[80%] flex flex-col gap-1 ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-slate-800 border border-slate-200/80'
                  }`}>
                    <p className="whitespace-pre-wrap font-sans">{msg.text}</p>

                    {/* ── LangUI-style action row beneath AI messages ── */}
                    {msg.sender === 'ai' && msg.text && !msg.text.startsWith('⏹️') && (
                      <div className="mt-2 flex items-center gap-2 pt-1 border-t border-slate-100/80">
                        {/* Copy button */}
                        <button
                          type="button"
                          onClick={() => copy(msg.id, msg.text)}
                          className="text-slate-400 hover:text-blue-600 transition-colors"
                          title="Copy"
                        >
                          {copiedId === msg.id
                            ? <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 13l4 4L19 7"/></svg>
                            : <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 8m0 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2z"/><path d="M16 8v-2a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>
                          }
                        </button>
                        {/* Thumbs-up */}
                        <button type="button" className="text-slate-400 hover:text-blue-600 transition-colors" title="Helpful">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M7 11v8a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1h3a4 4 0 0 0 4-4v-1a2 2 0 0 1 4 0v5h3a2 2 0 0 1 2 2l-1 5a2 3 0 0 1-2 2H8a3 3 0 0 1-3-3"/></svg>
                        </button>
                        {/* Thumbs-down */}
                        <button type="button" className="text-slate-400 hover:text-blue-600 transition-colors" title="Not helpful">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M7 13v-8a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h3a4 4 0 0 1 4 4v1a2 2 0 0 0 4 0v-5h3a2 2 0 0 0 2-2l-1-5a2 3 0 0 0-2-2H8a3 3 0 0 0-3 3"/></svg>
                        </button>
                      </div>
                    )}

                    {/* CTA moved to bottom upload zone when conversation_complete */}
                  </div>
                </div>
              </div>
            ))}

            {/* ── Generating indicator ─────────────────────────────────── */}
            {isGenerating && (
              <div className="flex gap-3 flex-row">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-slate-50 shrink-0 self-end shadow">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M19.933 13.041a8 8 0 1 1-9.925-8.788c3.899-1 7.935 1.007 9.425 4.747"/>
                    <path d="M20 4v5h-5"/>
                  </svg>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                    <span className="inline-flex gap-0.5">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </span>
                    <span>CUC Agent processing…</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* ── BOTTOM ACTION ZONE — switches on conversation_complete ─── */}
          {conversationComplete ? (
            /* ══ UPLOAD DROP ZONE (replaces input when CUC is done) ════════ */
            <div
              className={`border-t-2 transition-all duration-300 ${
                isDragging
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-emerald-400 bg-emerald-50/60'
              }`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragEnter={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                const file = e.dataTransfer.files?.[0];
                if (file) handleFileUpload(file);
              }}
            >
              {isGenerating ? (
                /* Uploading spinner */
                <div className="flex flex-col items-center justify-center gap-3 py-6 px-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M19.933 13.041a8 8 0 1 1-9.925-8.788c3.899-1 7.935 1.007 9.425 4.747"/>
                      <path d="M20 4v5h-5"/>
                    </svg>
                  </div>
                  <p className="text-sm font-semibold text-blue-700">Scout Agent compiling dataset…</p>
                  <button
                    type="button"
                    onClick={handleStopGeneration}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 px-4 py-1.5 text-xs font-semibold text-white transition-colors animate-pulse"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
                    Halt
                  </button>
                </div>
              ) : (
                /* Drop zone */
                <label className="flex flex-col items-center justify-center gap-3 py-6 px-4 cursor-pointer">
                  <div className={`flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg transition-transform duration-200 ${
                    isDragging ? 'scale-110 bg-blue-600' : 'bg-emerald-600'
                  } text-white`}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                  </div>

                  <div className="text-center">
                    <p className="text-sm font-bold text-slate-800">
                      {isDragging ? '📂 Drop dataset file here' : '✅ Intent complete — Upload your dataset'}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Drag & drop or click to select · .csv · .zip · .parquet · .json
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 px-5 py-2 text-xs font-bold text-white shadow-md transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                      </svg>
                      Select Dataset File
                    </span>
                    <span className="text-xs text-slate-400">or</span>
                    <button
                      type="button"
                      onClick={() => onNavigateToUpload(messages[1]?.text || 'Pipeline Studio')}
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white hover:border-blue-400 hover:text-blue-600 px-4 py-2 text-xs font-semibold text-slate-600 shadow-sm transition-colors"
                    >
                      Open Compiler
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
                    </button>
                  </div>

                  <input
                    type="file"
                    accept=".csv,.zip,.parquet,.json,.gz,.tar.gz"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                    }}
                  />
                </label>
              )}
            </div>
          ) : (
            /* ══ NORMAL CHAT INPUT BAR ════════════════════════════════════ */
            <div className="border-t border-slate-200 bg-white p-3">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!inputText.trim() || isGenerating) return;
                  handleSend(inputText);
                }}
              >
                <div className="relative flex items-end gap-2">
                  {/* Attach file button */}
                  <label
                    title="Attach dataset file (.zip, .csv, .parquet, .json)"
                    className="mb-1 shrink-0 flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-500 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                    </svg>
                    <input
                      type="file"
                      accept=".csv,.zip,.parquet,.json,.gz,.tar.gz"
                      className="hidden"
                      disabled={isGenerating}
                      onChange={(e) => {
                        if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                      }}
                    />
                  </label>

                  {/* Auto-resizing textarea */}
                  <textarea
                    ref={textareaRef}
                    id="cuc-input"
                    rows={1}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isGenerating}
                    placeholder="Enter your operational goal here… (Shift+Enter for newline)"
                    className="flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 pr-4 text-xs text-slate-800 shadow-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
                    style={{ minHeight: 40, maxHeight: 120, overflow: 'auto' }}
                  />

                  {/* Send / Halt button */}
                  {isGenerating ? (
                    <button
                      type="button"
                      onClick={handleStopGeneration}
                      className="mb-1 shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 px-3.5 py-2 text-xs font-semibold text-slate-50 shadow transition-colors animate-pulse focus:outline-none"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="6" width="12" height="12" rx="2"/>
                      </svg>
                      Halt
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={!inputText.trim()}
                      className="mb-1 shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-blue-600 hover:bg-blue-800 disabled:opacity-40 px-3.5 py-2 text-xs font-semibold text-slate-50 shadow transition-colors focus:outline-none focus:ring focus:ring-blue-300"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M10 14l11-11"/><path d="M21 3l-6.5 18a.55.55 0 0 1-1 0l-3.5-7-7-3.5a.55.55 0 0 1 0-1l18-6.5"/>
                      </svg>
                      Send
                    </button>
                  )}
                </div>
                <p className="mt-1.5 text-[10px] text-slate-400 font-mono pl-10">
                  Powered by CUC Pipeline · Qwen 32B · Session: {sessionId ? sessionId.slice(0, 8) + '…' : 'initializing'}
                </p>
              </form>
            </div>
          )}
        </div>

        {/* ── STARTER PROMPT CARDS (LangUI dark slate card pattern) ─────── */}
        {messages.length === 1 && (
          <div className="space-y-2">
            <p className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 text-center">
              Or select a starter configuration
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {samplePrompts.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(sample.text)}
                  className="group flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm hover:border-blue-400 hover:shadow-md transition-all active:scale-95 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-white text-sm"
                      style={{ background: sample.color }}
                    >
                      <span className="material-symbols-outlined text-base">{sample.icon}</span>
                    </span>
                    <span className="text-[10px] font-mono font-semibold text-slate-500 bg-slate-100 group-hover:bg-blue-50 group-hover:text-blue-700 px-2 py-0.5 rounded-full transition-colors">
                      {sample.label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 font-sans leading-relaxed group-hover:text-slate-900 transition-colors">
                    {sample.text}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
