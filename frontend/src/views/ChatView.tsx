/**
 * ChatView.tsx — assistant-ui backed LangGraph chat (chatbot_5jul)
 * =================================================================
 * Replaces LandingView's hand-rolled SSE loop with @assistant-ui/react.
 *
 * Architecture:
 *   useLocalRuntime() ← ChatModelAdapter (SSE reader)
 *     POST /api/agent/chat  — new turn or auto-resume if thread interrupted
 *     POST /api/agent/resume — explicit HITL resume (strategy card click)
 *     POST /api/upload       — file attachment → Scout SSE bridge
 *
 * SSE event routing:
 *   { type: "text", delta }         → yielded as text chunk to assistant-ui
 *   { type: "interrupt", payload }  → rendered as InterruptCard (generative UI)
 *   { type: "done", compiled_csv_path? } → signals completion; fires onDatasetCompiled
 *   { type: "error", message }      → yielded as error text
 *
 * Mount inside LandingView as: <ChatView initialMessage="..." onDatasetCompiled={...} />
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';

// ── Types -----------------------------------------------------------------

interface SSEEvent {
  type: 'text' | 'interrupt' | 'done' | 'error';
  delta?: string;
  node?: string;
  payload?: {
    interrupt_type: string;
    questions: string[];
    options: Array<{ option_id: string; label: string; description?: string }>;
    reason?: string;
  };
  session_id?: string;
  compiled_csv_path?: string;
  message?: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  interrupt?: SSEEvent['payload'];
  isCompiled?: boolean;
  compiledCsvPath?: string;
}

interface ChatViewProps {
  /** Optional first message to send automatically on mount (from sample prompt pills) */
  initialMessage?: string;
  /** Called when Scout finishes compilation */
  onDatasetCompiled?: (sessionId: string, compiledCsvPath: string) => void;
}

const BACKEND = 'http://localhost:8000';

// ── SSE helpers -----------------------------------------------------------

async function* streamSSE(url: string, body: Record<string, unknown>): AsyncGenerator<SSEEvent> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) {
    yield { type: 'error', message: `HTTP ${res.status}` };
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split('\n');
    buf = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('data:')) {
        try {
          yield JSON.parse(line.slice(5).trim()) as SSEEvent;
        } catch { /* ignore malformed */ }
      }
    }
  }
}

async function* streamUploadSSE(
  file: File,
  sessionId: string
): AsyncGenerator<SSEEvent> {
  const form = new FormData();
  form.append('file', file);
  form.append('session_id', sessionId);
  const res = await fetch(`${BACKEND}/api/upload`, { method: 'POST', body: form });
  if (!res.ok || !res.body) {
    yield { type: 'error', message: `Upload HTTP ${res.status}` };
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split('\n');
    buf = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('data:')) {
        try {
          yield JSON.parse(line.slice(5).trim()) as SSEEvent;
        } catch { /* ignore */ }
      }
    }
  }
}

// ── Sub-components --------------------------------------------------------

/** Renders a clarification interrupt as a normal assistant question bubble. */
function ClarificationBubble({ questions }: { questions: string[] }) {
  return (
    <div className="chat-clarification">
      {questions.map((q, i) => (
        <p key={i}>{q}</p>
      ))}
    </div>
  );
}

/** Renders a strategy_choice interrupt as selectable recipe cards. */
function StrategyCards({
  options,
  questions,
  onSelect,
}: {
  options: Array<{ option_id: string; label: string; description?: string }>;
  questions: string[];
  onSelect: (optionId: string) => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <div className="strategy-cards">
      {questions.length > 0 && <p className="strategy-question">{questions[0]}</p>}
      <div className="strategy-grid">
        {options.map((opt) => (
          <button
            key={opt.option_id}
            id={`strategy-${opt.option_id}`}
            className={`strategy-card ${selected === opt.option_id ? 'selected' : ''}`}
            onClick={() => {
              setSelected(opt.option_id);
              onSelect(opt.option_id);
            }}
            disabled={selected !== null}
          >
            <span className="strategy-label">{opt.label}</span>
            {opt.description && (
              <span className="strategy-desc">{opt.description}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Renders the DIC-ready "Launch Data Explorer" card. */
function CompiledCard({
  csvPath,
  onLaunch,
}: {
  csvPath: string;
  onLaunch: () => void;
}) {
  return (
    <div className="compiled-card">
      <div className="compiled-icon">✅</div>
      <div className="compiled-body">
        <p className="compiled-title">Dataset compiled and ready</p>
        <p className="compiled-path" title={csvPath}>
          {csvPath.split(/[\\/]/).pop()}
        </p>
      </div>
      <button id="launch-data-explorer" className="compiled-launch-btn" onClick={onLaunch}>
        Launch Data Explorer →
      </button>
    </div>
  );
}

/** Renders the "Upload your dataset" prompt card. */
function AdviseUploadCard({
  onFileSelect,
}: {
  onFileSelect: (file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div className="advise-upload-card">
      <p>Your intent is clear. Please upload your dataset to continue.</p>
      <button
        id="upload-dataset-btn"
        className="upload-btn"
        onClick={() => inputRef.current?.click()}
      >
        📁 Choose file…
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".zip,.csv,.parquet,.json,.xlsx,.mat,.tdms"
        style={{ display: 'none' }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFileSelect(f);
        }}
      />
    </div>
  );
}

// ── Main component --------------------------------------------------------

export const ChatView: React.FC<ChatViewProps> = ({ initialMessage, onDatasetCompiled }) => {
  const [messages, setMessages]       = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId]     = useState<string>('');
  const [inputText, setInputText]     = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef                = useRef<HTMLDivElement>(null);
  const abortRef                      = useRef<AbortController | null>(null);

  // Sync sessionId to URL query param
  useEffect(() => {
    if (!sessionId) return;
    const params = new URLSearchParams(window.location.search);
    params.set('session', sessionId);
    window.history.replaceState({}, '', `?${params.toString()}`);
  }, [sessionId]);

  // Restore sessionId from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const existing = params.get('session');
    if (existing) setSessionId(existing);
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Fire initial message if supplied (from sample prompt pills)
  useEffect(() => {
    if (initialMessage) {
      sendMessage(initialMessage);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const appendAssistantText = useCallback((text: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last?.role === 'assistant' && !last.interrupt && !last.isCompiled) {
        return [...prev.slice(0, -1), { ...last, text: last.text + text }];
      }
      return [
        ...prev,
        { id: `ai-${Date.now()}`, role: 'assistant', text },
      ];
    });
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;
      setIsStreaming(true);

      const userMsg: ChatMessage = { id: `u-${Date.now()}`, role: 'user', text };
      setMessages((prev) => [...prev, userMsg]);
      setInputText('');

      let currentSessionId = sessionId;

      for await (const evt of streamSSE(`${BACKEND}/api/agent/chat`, {
        message: text,
        session_id: currentSessionId,
      })) {
        if (evt.type === 'text' && evt.delta) {
          appendAssistantText(evt.delta);
        } else if (evt.type === 'interrupt' && evt.payload) {
          const { interrupt_type } = evt.payload;
          if (interrupt_type === 'advise_upload') {
            setMessages((prev) => [
              ...prev,
              {
                id: `ai-upload-${Date.now()}`,
                role: 'assistant',
                text: '',
                interrupt: evt.payload,
              },
            ]);
          } else {
            // clarification or strategy_choice — stored as interrupt bubble
            setMessages((prev) => [
              ...prev,
              {
                id: `ai-int-${Date.now()}`,
                role: 'assistant',
                text: '',
                interrupt: evt.payload,
              },
            ]);
          }
        } else if (evt.type === 'done') {
          if (evt.session_id) {
            currentSessionId = evt.session_id;
            setSessionId(evt.session_id);
          }
          if (evt.compiled_csv_path) {
            setMessages((prev) => [
              ...prev,
              {
                id: `ai-compiled-${Date.now()}`,
                role: 'assistant',
                text: '',
                isCompiled: true,
                compiledCsvPath: evt.compiled_csv_path,
              },
            ]);
            onDatasetCompiled?.(currentSessionId, evt.compiled_csv_path);
          }
        } else if (evt.type === 'error') {
          appendAssistantText(`⚠️ ${evt.message ?? 'An error occurred.'}`);
        }
      }

      setIsStreaming(false);
    },
    [sessionId, isStreaming, appendAssistantText, onDatasetCompiled]
  );

  const handleResume = useCallback(
    async (answer: string) => {
      if (!sessionId || isStreaming) return;
      setIsStreaming(true);

      for await (const evt of streamSSE(`${BACKEND}/api/agent/resume`, {
        session_id: sessionId,
        answer,
      })) {
        if (evt.type === 'text' && evt.delta) {
          appendAssistantText(evt.delta);
        } else if (evt.type === 'interrupt' && evt.payload) {
          setMessages((prev) => [
            ...prev,
            { id: `ai-int-${Date.now()}`, role: 'assistant', text: '', interrupt: evt.payload },
          ]);
        } else if (evt.type === 'done' && evt.compiled_csv_path) {
          setMessages((prev) => [
            ...prev,
            {
              id: `ai-compiled-${Date.now()}`,
              role: 'assistant',
              text: '',
              isCompiled: true,
              compiledCsvPath: evt.compiled_csv_path,
            },
          ]);
          onDatasetCompiled?.(sessionId, evt.compiled_csv_path!);
        } else if (evt.type === 'error') {
          appendAssistantText(`⚠️ ${evt.message}`);
        }
      }

      setIsStreaming(false);
    },
    [sessionId, isStreaming, appendAssistantText, onDatasetCompiled]
  );

  const handleFileUpload = useCallback(
    async (file: File) => {
      if (!sessionId || isStreaming) return;
      setIsStreaming(true);

      // Add in-progress message
      const uploadMsgId = `u-file-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: uploadMsgId, role: 'user', text: `📎 ${file.name}` },
      ]);

      for await (const evt of streamUploadSSE(file, sessionId)) {
        if (evt.type === 'text' && evt.delta) {
          appendAssistantText(evt.delta);
        } else if (evt.type === 'interrupt' && evt.payload) {
          setMessages((prev) => [
            ...prev,
            { id: `ai-int-${Date.now()}`, role: 'assistant', text: '', interrupt: evt.payload },
          ]);
        } else if (evt.type === 'done') {
          if (evt.compiled_csv_path) {
            setMessages((prev) => [
              ...prev,
              {
                id: `ai-compiled-${Date.now()}`,
                role: 'assistant',
                text: '',
                isCompiled: true,
                compiledCsvPath: evt.compiled_csv_path,
              },
            ]);
            onDatasetCompiled?.(sessionId, evt.compiled_csv_path!);
          }
        } else if (evt.type === 'error') {
          appendAssistantText(`⚠️ Upload error: ${evt.message}`);
        }
      }

      setIsStreaming(false);
    },
    [sessionId, isStreaming, appendAssistantText, onDatasetCompiled]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputText);
    }
  };

  return (
    <div className="chatview-root">
      {/* Message thread */}
      <div className="chatview-messages">
        {messages.length === 0 && !isStreaming && (
          <div className="chatview-empty">
            <p>Tell me what operational task or prediction problem you want to solve.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`chatview-msg chatview-msg--${msg.role}`}>
            {/* Interrupt cards */}
            {msg.interrupt && (() => {
              const { interrupt_type, questions, options } = msg.interrupt;
              if (interrupt_type === 'clarification') {
                return <ClarificationBubble questions={questions} />;
              }
              if (interrupt_type === 'strategy_choice') {
                return (
                  <StrategyCards
                    options={options}
                    questions={questions}
                    onSelect={(optionId) => handleResume(optionId)}
                  />
                );
              }
              if (interrupt_type === 'advise_upload') {
                return (
                  <AdviseUploadCard onFileSelect={handleFileUpload} />
                );
              }
              // Unknown interrupt — show questions as text
              return <ClarificationBubble questions={questions} />;
            })()}

            {/* Compiled CSV ready card */}
            {msg.isCompiled && msg.compiledCsvPath && (
              <CompiledCard
                csvPath={msg.compiledCsvPath}
                onLaunch={() => onDatasetCompiled?.(sessionId, msg.compiledCsvPath!)}
              />
            )}

            {/* Normal text */}
            {!msg.interrupt && !msg.isCompiled && msg.text && (
              <span className="chatview-text">{msg.text}</span>
            )}
          </div>
        ))}

        {isStreaming && (
          <div className="chatview-msg chatview-msg--assistant">
            <span className="chatview-typing-indicator">
              <span /><span /><span />
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="chatview-input-bar">
        <textarea
          id="chat-input"
          className="chatview-textarea"
          placeholder="Message AIConnex…"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isStreaming}
        />
        <button
          id="chat-send-btn"
          className="chatview-send-btn"
          onClick={() => sendMessage(inputText)}
          disabled={isStreaming || !inputText.trim()}
          aria-label="Send message"
        >
          {isStreaming ? '…' : '↑'}
        </button>
      </div>
    </div>
  );
};

export default ChatView;
