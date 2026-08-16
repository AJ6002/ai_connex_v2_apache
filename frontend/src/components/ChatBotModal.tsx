import React, { useState, useEffect, useRef } from 'react';

interface ChatBotModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: string;
  onNavigateView?: (viewId: string) => void;
}

interface Message {
  sender: 'user' | 'bot';
  text: string;
  intent?: string;
  time: string;
  quickAction?: { label: string; viewId: string };
}

export const ChatBotModal: React.FC<ChatBotModalProps> = ({
  isOpen,
  onClose,
  userId: initialUserId = '1223',
  onNavigateView,
}) => {
  const [userId, setUserId] = useState(initialUserId);
  const [isMinimized, setIsMinimized] = useState(false);
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      text: "Hi there! I'm Jane, Lead Machine Learning Solutions Architect at AIConnex. I'd love to help you build and launch your custom AutoML project! What prediction goal or dataset are you working with today?",
      intent: 'Jane — Lead ML Architect',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim() || isLoading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: Message = { sender: 'user', text: query, time: timeStr };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputText('');
    setIsLoading(true);

    try {
      // Send request to Jane Chatbot API gateway (port 5000) or fallback
      let response: Response | null = null;
      try {
        response = await fetch('http://localhost:5000/api/v1/jane/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ userId, message: query, query }),
        });
      } catch {
        try {
          response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId, message: query }),
          });
        } catch {
          // offline
        }
      }

      if (response && response.ok) {
        const data = await response.json();
        const botMsg: Message = {
          sender: 'bot',
          text: data.response || data.botResponse || data.answer || "I have received your message and logged it to the intent pipeline.",
          intent: data.intent ? `Intent: ${data.intent}` : 'Jane • AI Assistant',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, botMsg]);
      } else {
        throw new Error('API offline');
      }
    } catch {
      // Fallback assistant response
      setTimeout(() => {
        let reply = 'I have processed your industrial telemetry query and logged it to the intent pipeline.';
        let intentLabel = 'INTENT_CLASSIFIED';
        let suggested: { label: string; viewId: string } | undefined;

        const lower = query.toLowerCase();
        if (lower.includes('upload') || lower.includes('dataset') || lower.includes('s3') || lower.includes('cloud') || lower.includes('csv') || lower.includes('zip') || lower.includes('parquet')) {
          reply = 'I have initialized the **Universal Upload Controller** for your project. You can ingest files (.csv, .parquet, .json, .zip), AWS S3 buckets, cloud databases, or industrial telemetry streams.';
          intentLabel = 'LAUNCH_UPLOAD_CONTROLLER';
          suggested = { label: '🚀 Launch Upload Controller', viewId: 'compiler' };
        } else if (lower.includes('rul') || lower.includes('predict') || lower.includes('remaining')) {
          reply = 'Predictive Maintenance RUL Engine calculated Remaining Useful Life: 1,420 operating hours across Turbine Asset #4.';
          intentLabel = 'PREDICT_RUL';
          suggested = { label: 'View Data Explorer & Telemetry', viewId: 'data_explorer' };
        } else if (lower.includes('train') || lower.includes('automl') || lower.includes('model')) {
          reply = 'AutoML Training job triggered. Hyperparameter tuning active across XGBoost and LightGBM models on GPU Cluster 1.';
          intentLabel = 'TRAIN_AUTOML_MODEL';
          suggested = { label: 'Open ML Studio & Pipelines', viewId: 'pipeline_studio' };
        } else if (lower.includes('telemetry') || lower.includes('opc') || lower.includes('mqtt')) {
          reply = 'OPC UA & MQTT Telemetry stream normal. Ingestion rate: 45,000 events/sec with zero dropped packets.';
          intentLabel = 'CHECK_TELEMETRY';
          suggested = { label: 'Open Master Data & Telemetry', viewId: 'master_data' };
        }

        setMessages((prev) => [
          ...prev,
          {
            sender: 'bot',
            text: reply,
            intent: intentLabel,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            quickAction: suggested,
          },
        ]);
      }, 600);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className={`transition-all duration-300 pointer-events-auto z-[100] ${
        isMinimized
          ? 'fixed bottom-6 right-6'
          : 'fixed inset-0 flex items-center justify-center p-4 sm:p-6'
      }`}
    >
      {/* Frosted/Wet Glass Backdrop (only shown when expanded in center) */}
      {!isMinimized && (
        <div
          className="absolute inset-0 bg-slate-900/20 backdrop-blur-[4px] transition-all duration-300"
          onClick={onClose}
        />
      )}

      {/* Floating Chatbot Window */}
      <div
        className={`relative bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-3xl shadow-[0_24px_60px_rgba(13,21,51,0.28)] transition-all duration-300 flex flex-col overflow-hidden z-10 ${
          isMinimized
            ? 'w-[360px] h-[415px] rounded-2xl shadow-2xl border-2 border-[#0D1533]/20'
            : 'w-full max-w-lg h-[600px]'
        }`}
      >
        {/* Header (Deep Indigo #2B0063) */}
        <div className="bg-[#2B0063] px-4 py-3 flex justify-between items-center text-white shadow-md flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-[#E86326]/20 flex items-center justify-center text-[#E86326] border border-[#E86326]/40 shadow-sm flex-shrink-0">
              <span className="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                smart_toy
              </span>
            </div>
            <div className="min-w-0">
              <h3 className="font-bold text-xs sm:text-sm leading-tight text-white truncate flex items-center gap-1.5">
                <span>Jane — AI Assistant & Copilot</span>
              </h3>
              <span className="text-[10px] text-slate-300 block font-mono truncate">
                Logging: user-intent-{userId}.json
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {!isMinimized && (
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                title="User ID"
                className="w-11 bg-white/10 text-white border border-white/20 rounded px-1 py-0.5 text-[10px] font-mono text-center focus:outline-none focus:border-[#E86326]"
                placeholder="ID"
              />
            )}

            {/* Minimize / Expand Toggle */}
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              title={isMinimized ? 'Expand to full size' : 'Minimize to bottom-right'}
              className="w-7 h-7 rounded-full hover:bg-white/10 flex items-center justify-center text-slate-300 hover:text-white transition-colors"
            >
              <span className="material-symbols-outlined text-base">
                {isMinimized ? 'open_in_full' : 'remove'}
              </span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              title="Close chat"
              className="w-7 h-7 rounded-full hover:bg-red-500/20 hover:text-red-300 flex items-center justify-center text-slate-300 transition-colors"
            >
              <span className="material-symbols-outlined text-base">close</span>
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 flex flex-col justify-between overflow-hidden bg-slate-50">
          {/* Messages Thread */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[88%] p-3 rounded-2xl shadow-xs text-xs space-y-1.5 relative ${
                    msg.sender === 'user'
                      ? 'bg-[#E86326] text-white rounded-br-none'
                      : 'bg-white border border-slate-200 text-[#333333] rounded-bl-none'
                  }`}
                >
                  {msg.sender === 'bot' && (
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-[#E86326] animate-pulse"></span>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-600">
                        {msg.intent || 'RAG Active'}
                      </span>
                    </div>
                  )}
                  <p className="leading-relaxed">{msg.text}</p>

                  {msg.quickAction && (
                    <button
                      onClick={() => {
                        if (onNavigateView && msg.quickAction) {
                          onNavigateView(msg.quickAction.viewId);
                          onClose();
                        }
                      }}
                      className="mt-1.5 px-2.5 py-1 bg-[#E86326] hover:bg-[#D5521B] text-white font-bold text-[11px] rounded-full shadow-xs flex items-center gap-1 transition-all"
                    >
                      <span>{msg.quickAction.label}</span>
                      <span className="material-symbols-outlined text-xs">arrow_forward</span>
                    </button>
                  )}
                </div>
                <span className="text-[9px] text-slate-400 font-mono mt-0.5 px-1">{msg.time}</span>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-slate-400 text-xs font-mono p-1.5">
                <span className="w-2 h-2 rounded-full bg-[#0D1533] animate-ping"></span>
                <span>Jane is processing query...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompt Chips */}
          <div className="px-3 py-1.5 bg-white border-t border-slate-200 flex gap-1.5 overflow-x-auto no-scrollbar">
            <button
              onClick={() => handleSendMessage('Predict RUL for Turbine Asset')}
              className="px-2.5 py-1 bg-slate-100 hover:bg-[#E86326] hover:text-white text-slate-700 font-medium text-[11px] rounded-full transition-all border border-slate-200 whitespace-nowrap"
            >
              Predict RUL
            </button>
            <button
              onClick={() => handleSendMessage('Train AutoML Model on Cluster 1')}
              className="px-2.5 py-1 bg-slate-100 hover:bg-[#E86326] hover:text-white text-slate-700 font-medium text-[11px] rounded-full transition-all border border-slate-200 whitespace-nowrap"
            >
              Train AutoML
            </button>
            <button
              onClick={() => handleSendMessage('Check Telemetry Status')}
              className="px-2.5 py-1 bg-slate-100 hover:bg-[#E86326] hover:text-white text-slate-700 font-medium text-[11px] rounded-full transition-all border border-slate-200 whitespace-nowrap"
            >
              Telemetry Status
            </button>
          </div>

          {/* Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-2.5 bg-white border-t border-slate-200 flex items-center gap-2"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask AI Copilot or type a command..."
                className="w-full pl-3.5 pr-9 py-2 bg-slate-50 border border-slate-300 rounded-full text-xs text-[#333333] focus:outline-none focus:border-[#2B0063] focus:ring-1 focus:ring-[#2B0063]"
              />
              <button
                type="submit"
                disabled={!inputText.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-[#E86326] text-white hover:bg-[#D5521B] disabled:opacity-30 flex items-center justify-center transition-all"
              >
                <span className="material-symbols-outlined text-xs font-bold">send</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
