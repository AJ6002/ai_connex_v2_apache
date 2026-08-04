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

export const LandingView: React.FC<LandingViewProps> = ({ onNavigateToUpload }) => {
  const [sessionId, setSessionId] = useState<string>('');
  const [conversationId] = useState<string>(() => `ui_${Date.now()}`);
  const [confidence, setConfidence] = useState<number>(0.50);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      sender: 'ai',
      text: 'Hello! I am the AI Connexx assistant. Tell me what operational task or prediction problem you would like to solve using your dataset today.'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  const samplePrompts = [
    { text: "Train a Remaining Useful Life (RUL) predictor for C-MAPSS turbofan engine SCADA logs.", icon: "speed", color: "#C8102E" },
    { text: "Detect anomalies and drifts in multivariate industrial sensor streams.", icon: "insights", color: "#1E47C8" },
    { text: "Build a failure classification pipeline with custom outlier thresholds.", icon: "warning", color: "#eab308" }
  ];

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
    setMessages((prev) => [
      ...prev,
      {
        id: `stop-${Date.now()}`,
        sender: 'ai',
        text: '⏹️ Process response generation halted by operator.'
      }
    ]);
  };

  const handleSend = async (text: string) => {
    const prompt = text.trim();
    if (!prompt || isGenerating) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: prompt
    };

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
        body: JSON.stringify({
          message: prompt,
          session_id: sessionId,
          conversation_id: conversationId
        }),
        signal: controller.signal
      });

      const data = await res.json();
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // Compute confidence score matching terminal_runner.py logic
      const missing = data.missing_information || [];
      const reqMissing = missing.filter((m: string) => m.includes('Required field')).length;
      const filled = Math.max(0, 4 - reqMissing);
      const conf = Math.round((0.50 + (filled / 4) * 0.45) * 100) / 100;
      setConfidence(conf);

      const isComplete = data.conversation_complete === true || data.recommended_next_action === 'prompt_for_upload';

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: data.reply || 'Request processed successfully.',
        isComplete,
        action: data.recommended_next_action
      };

      setMessages([...updatedMessages, aiMsg]);
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error(err);
      setMessages([
        ...updatedMessages,
        {
          id: `err-${Date.now()}`,
          sender: 'ai',
          text: 'Sorry, I encountered an error connecting to the AI Connexx backend (http://localhost:8000). Please verify the server is running.'
        }
      ]);
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

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
        method: 'POST',
        body: formData,
        signal: controller.signal
      });

      const data = await res.json();
      const replyText = data.reply || `Dataset '${file.name}' successfully uploaded and compiled by Scout Agent!`;

      const aiMsg: Message = {
        id: `ai-upload-${Date.now()}`,
        sender: 'ai',
        text: replyText,
        isComplete: true,
        action: 'dataset_compiled'
      };

      setMessages([...updatedMessages, aiMsg]);
      setConfidence(0.95);
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error(err);
      setMessages([
        ...updatedMessages,
        {
          id: `err-upload-${Date.now()}`,
          sender: 'ai',
          text: `Error uploading dataset '${file.name}'. Please verify the backend is running at http://localhost:8000.`
        }
      ]);
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };


  return (
    <div className="min-h-[85vh] flex flex-col justify-center items-center px-4 relative select-none animate-fadeIn">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-tas-red/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-tas-blue/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="max-w-3xl w-full text-center space-y-6 relative z-10">
        {/* Dynamic header */}
        <div className={`flex flex-col items-center gap-3 transition-all duration-500 ${messages.length > 1 ? 'scale-90 opacity-90' : ''}`}>
          <TasLogo className="h-16 animate-pulse" showSubtitle={false} />
          <h1 className="font-headline text-3xl sm:text-4xl font-black tracking-tight text-[#0F172A]">
            <span className="inline-flex items-center gap-1">AI <img src="/connexx-dark.png" alt="Connexx" className="h-8 w-auto object-contain inline-block align-middle" /></span>
          </h1>
          <p className="text-sm font-mono text-slate-500 max-w-xl">
            Type your operational maintenance goals below or attach your dataset file. Our compiler will automatically assign optimal data topology, match DAG schemas, and compile training recipes.
          </p>
        </div>

        {/* Confidence Indicator Bar (Terminal Runner Style) */}
        {messages.length > 1 && (
          <div className="max-w-3xl mx-auto px-2 flex items-center justify-between text-xs font-mono text-slate-500 bg-slate-100/80 rounded-xl p-2 border border-slate-200">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
              <span>CUC Pipeline Status:</span>
              <strong className={confidence >= 0.91 ? 'text-emerald-600 font-bold' : 'text-blue-600'}>
                {confidence >= 0.91 ? 'THRESHOLD REACHED (READY)' : 'GATHERING INTENT CONTRACT'}
              </strong>
            </span>
            <span>Confidence: <strong className="text-slate-800">{Math.round(confidence * 100)}%</strong></span>
          </div>
        )}

        {/* Interactive Chat Window Container */}
        <div className="glass-panel rounded-3xl border border-slate-200/80 shadow-2xl p-5 text-left bg-white/95 flex flex-col gap-4 overflow-hidden min-h-[320px] max-h-[520px]">
          {/* Messages log */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-slate-300">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white font-sans' 
                    : 'bg-slate-100 text-slate-800 font-mono border border-slate-200'
                }`}>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                  
                  {/* Inline Upload Trigger when Conversation is Complete */}
                  {msg.sender === 'ai' && msg.isComplete && (
                    <div className="mt-3 pt-2 border-t border-slate-200/80">
                      <button
                        onClick={() => onNavigateToUpload(messages[1]?.text || 'Pipeline Studio configuration')}
                        className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-sans text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-2 border-none cursor-pointer active:scale-95"
                      >
                        <span>Open Compiler & Run Pipeline</span>
                        <span className="material-symbols-outlined text-sm">arrow_forward</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isGenerating && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-100 text-xs font-mono text-slate-500 animate-pulse border border-slate-200 w-fit">
                <span className="material-symbols-outlined text-base animate-spin text-blue-600">sync</span>
                <span>AI Connexx Scout Agent compiling dataset & extracting intent...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Action Row — ALWAYS VISIBLE WITH FILE ATTACHMENT */}
          <div className="border-t border-slate-100 pt-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!inputText.trim() || isGenerating) return;
                handleSend(inputText);
              }}
              className="flex items-center gap-2 p-1 border border-slate-200 focus-within:border-blue-500 rounded-2xl bg-slate-50 transition-all"
            >
              {/* Direct Dataset File Attachment Button (acts like CLI -upload_file) */}
              <label
                title="Attach dataset file (.zip, .csv, .parquet, .json)"
                className="p-1.5 hover:bg-slate-200/60 text-slate-500 hover:text-blue-600 rounded-xl cursor-pointer transition-colors flex items-center justify-center shrink-0"
              >
                <span className="material-symbols-outlined text-lg select-none">attach_file</span>
                <input
                  type="file"
                  accept=".csv,.zip,.parquet,.json,.gz,.tar.gz"
                  className="hidden"
                  disabled={isGenerating}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileUpload(e.target.files[0]);
                    }
                  }}
                />
              </label>

              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isGenerating}
                placeholder="Type your goal or click 📎 to attach dataset file..."
                className="flex-1 bg-transparent border-none text-slate-800 placeholder-slate-400 focus:outline-none text-xs font-sans py-2.5 px-1"
              />

              {isGenerating ? (
                <button
                  type="button"
                  onClick={handleStopGeneration}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-mono font-bold rounded-xl shadow-md transition-all flex items-center gap-1.5 border-none cursor-pointer shrink-0 animate-pulse"
                >
                  <span className="material-symbols-outlined text-sm">stop_circle</span>
                  <span>Halt</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!inputText.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-mono font-bold rounded-xl shadow-md transition-all flex items-center gap-1 border-none cursor-pointer shrink-0"
                >
                  <span>Send</span>
                  <span className="material-symbols-outlined text-xs">send</span>
                </button>
              )}

            </form>
          </div>
        </div>


        {/* Quick Sample Config Selection Cards (Only shown if chat has not started) */}
        {messages.length === 1 && (
          <div className="space-y-3 pt-2">
            <h3 className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              Or select a starter configuration
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {samplePrompts.map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(sample.text)}
                  className="p-4 rounded-xl border hover:border-slate-300 text-left transition-all hover:scale-102 flex flex-col gap-2 bg-white/70 shadow-xs cursor-pointer"
                  style={{ border: '1px solid rgba(13,21,51,0.06)' }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white"
                    style={{ background: sample.color }}>
                    <span className="material-symbols-outlined text-base">{sample.icon}</span>
                  </div>
                  <p className="text-xs text-slate-600 font-sans font-medium leading-relaxed">
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
