import React, { useState, useRef, useEffect } from 'react';
import { TASLogo } from './TASLogo';
import { Send, MessageSquare, Sparkles, Cpu, Layers, Zap, Activity, Check, RefreshCw, FileUp, Upload } from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'assistant' | 'user';
  text: string;
  timestamp: string;
  topologyAssigned?: boolean;
  dagMatched?: boolean;
  recipeCompiled?: boolean;
  showUploadCard?: boolean;
}

interface MainChatViewProps {
  darkMode: boolean;
  onSelectStarter: (prompt: string) => void;
}

export const MainChatView: React.FC<MainChatViewProps> = ({ darkMode, onSelectStarter }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'initial-greeting',
      sender: 'assistant',
      text: 'Hello! I am the AI Connexx assistant. What calculation or prediction task would you like to solve using your dataset today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [sessionId, setSessionId] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  const handleSend = async (textToSend?: string) => {
    const prompt = (textToSend || inputMessage).trim();
    if (!prompt || isGenerating) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsGenerating(true);

    try {
      const res = await fetch('/api/pre_upload/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: prompt, session_id: sessionId }),
      });

      const data = await res.json();
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // Check if conversation is complete or prompt_for_upload is requested
      const isUploadPrompt =
        data.conversation_complete === true ||
        data.recommended_next_action === 'prompt_for_upload';

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: data.reply || 'No response from server.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        topologyAssigned: data.topologyAssigned,
        dagMatched: data.dagMatched,
        recipeCompiled: data.recipeCompiled,
        showUploadCard: isUploadPrompt,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      const errorMsg: ChatMessage = {
        id: `assistant-error-${Date.now()}`,
        sender: 'assistant',
        text: 'Sorry, I encountered an error connecting to the server. Please make sure the backend is running.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileUpload = async (file: File, msgId: string) => {
    setIsGenerating(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      const assistantMsg: ChatMessage = {
        id: `assistant-upload-${Date.now()}`,
        sender: 'assistant',
        text: data.reply || `Dataset '${file.name}' uploaded and compiled successfully!`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        topologyAssigned: data.topologyAssigned ?? true,
        dagMatched: data.dagMatched ?? true,
        recipeCompiled: data.recipeCompiled ?? true,
      };

      setMessages((prev) =>
        prev
          .map((m) => (m.id === msgId ? { ...m, showUploadCard: false } : m))
          .concat(assistantMsg)
      );
    } catch (err) {
      console.error(err);
      const errorMsg: ChatMessage = {
        id: `assistant-upload-error-${Date.now()}`,
        sender: 'assistant',
        text: `Error uploading file '${file.name}'. Please verify the backend is running on port 5000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  const starterConfigurations = [
    {
      title: 'Predictive Anomaly Detection',
      borderAccent: 'border-t-4 border-t-red-600',
      tagColor: 'bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300',
      prompt: 'Forecast equipment failure windows using real-time vibration, pressure & temperature telemetry streams.',
      icon: Activity,
    },
    {
      title: 'Topology DAG & Sensor Routing',
      borderAccent: 'border-t-4 border-t-blue-600',
      tagColor: 'bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300',
      prompt: 'Map multi-sensor stream topologies directly to Directed Acyclic Graph (DAG) execution schemas.',
      icon: Layers,
    },
    {
      title: 'Recipe Training Optimization',
      borderAccent: 'border-t-4 border-t-amber-500',
      tagColor: 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
      prompt: 'Compile automated hyperparameter training recipes to optimize throughput and energy consumption.',
      icon: Zap,
    },
    {
      title: 'Automated Goal Planner',
      borderAccent: 'border-t-4 border-t-emerald-600',
      tagColor: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
      prompt: 'Synthesize preventive operational maintenance schedules aligned with industrial throughput targets.',
      icon: Cpu,
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-7rem)] py-8 px-4 pl-16 sm:pl-20 max-w-5xl mx-auto">
      {/* Top Header Identity */}
      <div className="flex flex-col items-center text-center mb-6 animate-in fade-in slide-in-from-top-4 duration-500">
        <TASLogo size="lg" className="mb-4 shadow-md" />

        <h1
          className={`text-3xl sm:text-4xl font-extrabold tracking-tight mb-3 font-sans ${
            darkMode ? 'text-white' : 'text-slate-900'
          }`}
        >
          AI Connexx
        </h1>

        <p
          className={`font-mono text-xs sm:text-sm max-w-2xl leading-relaxed ${
            darkMode ? 'text-slate-400' : 'text-slate-600'
          }`}
        >
          Type your operational maintenance goals below. Our compiler will automatically assign optimal data topology, match DAG schemas, and compile training recipes.
        </p>
      </div>

      {/* Main Chat Card */}
      <div
        className={`w-full max-w-3xl rounded-3xl p-5 sm:p-7 shadow-xl border transition-colors relative mb-8 ${
          darkMode
            ? 'bg-slate-900/90 border-slate-800 text-slate-100 shadow-black/50'
            : 'bg-white border-slate-200/90 text-slate-800 shadow-slate-200/70'
        }`}
      >
        {/* Messages Container */}
        <div className="space-y-4 max-h-[420px] overflow-y-auto pr-2 mb-6 custom-scrollbar">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-in fade-in duration-300`}
              >
                <div className="flex items-center gap-2 mb-1 px-1">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                    {isUser ? 'Operational Operator' : 'AI Connexx Assistant'}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{msg.timestamp}</span>
                </div>

                <div
                  className={`p-4 rounded-2xl max-w-[92%] sm:max-w-[88%] text-xs sm:text-sm font-mono leading-relaxed shadow-sm border ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-tr-xs border-blue-500'
                      : darkMode
                      ? 'bg-slate-800 text-slate-200 rounded-tl-xs border-slate-700/80'
                      : 'bg-[#F1F5F9] text-slate-800 rounded-tl-xs border-slate-200/80'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Interactive Dataset Upload Card */}
                  {!isUser && msg.showUploadCard && (
                    <div className="mt-4 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-blue-500/30 shadow-md">
                      <div className="flex items-center gap-2 mb-3">
                        <FileUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        <span className="font-sans font-bold text-xs sm:text-sm text-slate-800 dark:text-slate-100">
                          Import Operational Dataset (.zip, .csv, .parquet, .json)
                        </span>
                      </div>

                      <div
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault();
                          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                            handleFileUpload(e.dataTransfer.files[0], msg.id);
                          }
                        }}
                        className="border-2 border-dashed border-blue-400/50 hover:border-blue-500 dark:border-blue-500/40 rounded-xl p-6 text-center bg-blue-500/5 dark:bg-blue-500/10 transition-colors cursor-pointer"
                      >
                        <Upload className="w-8 h-8 text-blue-500 mx-auto mb-2 animate-bounce" />
                        <p className="font-mono text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">
                          Drag & Drop your dataset archive (.zip, .tar.gz, .csv)
                        </p>
                        <p className="font-mono text-[10px] text-slate-400 mb-3">
                          Supported formats: .zip, .csv, .parquet, .json (Max 500MB)
                        </p>

                        <label className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-sans text-xs px-4 py-2 rounded-lg cursor-pointer shadow transition-all active:scale-95">
                          <span>Choose File</span>
                          <input
                            type="file"
                            accept=".zip,.csv,.parquet,.json,.gz,.tar.gz"
                            className="hidden"
                            onChange={(e) => {
                              if (e.target.files && e.target.files[0]) {
                                handleFileUpload(e.target.files[0], msg.id);
                              }
                            }}
                          />
                        </label>
                      </div>
                    </div>
                  )}

                  {/* Operational Badges from backend response */}
                  {!isUser && (msg.topologyAssigned || msg.dagMatched || msg.recipeCompiled) && (
                    <div className="mt-3 pt-2 border-t border-slate-300/40 dark:border-slate-700/60 flex flex-wrap gap-2 text-[10px]">
                      {msg.topologyAssigned && (
                        <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold px-2 py-0.5 rounded-full border border-emerald-500/20">
                          <Check className="w-3 h-3" /> Topology Assigned
                        </span>
                      )}
                      {msg.dagMatched && (
                        <span className="inline-flex items-center gap-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 font-semibold px-2 py-0.5 rounded-full border border-blue-500/20">
                          <Layers className="w-3 h-3" /> DAG Matched
                        </span>
                      )}
                      {msg.recipeCompiled && (
                        <span className="inline-flex items-center gap-1 bg-purple-500/10 text-purple-600 dark:text-purple-400 font-semibold px-2 py-0.5 rounded-full border border-purple-500/20">
                          <Zap className="w-3 h-3" /> Recipe Compiled
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isGenerating && (
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-slate-100 dark:bg-slate-800/80 w-fit text-xs font-mono text-slate-600 dark:text-slate-300 animate-pulse border border-slate-200 dark:border-slate-700">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
              <span>AI Connexx compiler processing dataset & training recipes...</span>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Chat Input Field Container */}
        <div
          className={`rounded-2xl border p-2 pl-4 flex items-center gap-3 shadow-inner transition-colors ${
            darkMode
              ? 'bg-slate-950/80 border-slate-800 focus-within:border-blue-500/80'
              : 'bg-[#F8FAFC] border-slate-200 focus-within:border-blue-500 focus-within:bg-white'
          }`}
        >
          <MessageSquare className="w-4 h-4 text-slate-400 shrink-0" />

          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="What operational task would you like to solve?..."
            className="w-full bg-transparent text-xs sm:text-sm font-sans focus:outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
            disabled={isGenerating}
          />

          <button
            onClick={() => handleSend()}
            disabled={!inputMessage.trim() || isGenerating}
            className="bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-xs px-4 py-2.5 rounded-xl flex items-center gap-1.5 transition-all shadow-md active:scale-95 shrink-0 cursor-pointer"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5 fill-current" />
          </button>
        </div>
      </div>

      {/* Center Label */}
      <div className="text-center mb-6">
        <span className="font-mono text-[11px] font-semibold text-slate-400 dark:text-slate-500 tracking-widest uppercase">
          OR SELECT A STARTER CONFIGURATION
        </span>
      </div>

      {/* Starter Configurations Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-4xl">
        {starterConfigurations.map((card, idx) => {
          const Icon = card.icon;
          return (
            <button
              key={idx}
              onClick={() => {
                onSelectStarter(card.prompt);
                handleSend(card.prompt);
              }}
              className={`text-left p-4 rounded-2xl shadow-md border transition-all duration-200 hover:-translate-y-1 cursor-pointer flex flex-col justify-between ${card.borderAccent} ${
                darkMode
                  ? 'bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:bg-slate-800/90'
                  : 'bg-white border-slate-200/90 hover:border-slate-300 hover:shadow-lg'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${card.tagColor}`}>
                    Starter #{idx + 1}
                  </span>
                  <Icon className="w-4 h-4 text-slate-400" />
                </div>
                <h3 className="font-semibold text-xs sm:text-sm mb-1.5 line-clamp-1">{card.title}</h3>
                <p className="text-[11px] font-mono text-slate-500 dark:text-slate-400 line-clamp-3 leading-relaxed">
                  {card.prompt}
                </p>
              </div>

              <div className="mt-3 text-[10px] font-mono font-medium text-blue-600 dark:text-blue-400 flex items-center gap-1 group-hover:underline">
                Run Configuration →
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
