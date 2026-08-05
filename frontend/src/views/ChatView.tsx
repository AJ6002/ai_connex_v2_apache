/**
 * ChatView.tsx — @assistant-ui/react backed LangGraph chat (chatbot_5jul)
 * =======================================================================
 * Real assistant-ui integration (v0.7.x):
 *   useLocalRuntime(adapter)  — adapter.run() streams our SSE endpoint and
 *                               yields assistant content parts (text + tool-calls).
 *   ThreadPrimitive / MessagePrimitive / ComposerPrimitive — headless chat UI
 *                               (streaming, auto-scroll, composer) styled w/ Tailwind.
 *   makeAssistantToolUI(...)  — generative UI cards for the HITL interrupts:
 *                               advise_upload · strategy_choice · dataset_compiled.
 *
 * Backend SSE contract (chatbot/backend/app.py):
 *   { type: "text",      delta }
 *   { type: "interrupt", payload: { interrupt_type, questions, options } }
 *   { type: "compiled",  compiled_csv_path }
 *   { type: "done",      session_id }
 *   { type: "error",     message }
 *
 * Endpoints:
 *   POST /api/agent/chat   — new turn; backend auto-resumes if thread is parked
 *   POST /api/agent/resume — explicit HITL resume (strategy card click)
 *   POST /api/upload       — dataset upload → Scout SSE bridge
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  makeAssistantToolUI,
  useThreadRuntime,
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  type ChatModelAdapter,
} from '@assistant-ui/react';

const BACKEND = 'http://localhost:8000';

// ── SSE event contract ----------------------------------------------------

interface SSEEvent {
  type: 'text' | 'interrupt' | 'compiled' | 'done' | 'error';
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

/** Parse a fetch Response body as a stream of our SSE JSON frames. */
async function* streamSSE(
  url: string,
  init: RequestInit
): AsyncGenerator<SSEEvent> {
  const res = await fetch(url, init);
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
        } catch {
          /* ignore malformed frame */
        }
      }
    }
  }
}

// ── Shared config context (session id + completion callback) --------------

interface ChatConfig {
  sessionRef: React.MutableRefObject<string>;
  onDatasetCompiled?: (sessionId: string, compiledCsvPath: string) => void;
}

const ChatConfigContext = createContext<ChatConfig | null>(null);
const useChatConfig = () => {
  const ctx = useContext(ChatConfigContext);
  if (!ctx) throw new Error('ChatConfigContext missing');
  return ctx;
};

// ── Tool-call content part helpers ----------------------------------------

let _toolSeq = 0;
const nextToolCallId = () => `tc_${Date.now()}_${_toolSeq++}`;

type ToolPart = {
  type: 'tool-call';
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  argsText: string;
};

const toolPart = (toolName: string, args: Record<string, unknown>): ToolPart => ({
  type: 'tool-call',
  toolCallId: nextToolCallId(),
  toolName,
  args,
  argsText: JSON.stringify(args),
});

// ── ChatModelAdapter: streams /api/agent/chat -----------------------------

function useAgentAdapter(): ChatModelAdapter {
  const { sessionRef, onDatasetCompiled } = useChatConfig();

  return useMemo<ChatModelAdapter>(
    () => ({
      async *run({ messages, abortSignal }) {
        // Latest user message text
        const last = messages[messages.length - 1];
        const userText =
          last?.content
            ?.map((p) => (p.type === 'text' ? p.text : ''))
            .join('')
            .trim() ?? '';

        let text = '';
        const tools: ToolPart[] = [];
        const build = () => {
          const content: Array<
            { type: 'text'; text: string } | ToolPart
          > = [];
          if (text) content.push({ type: 'text', text });
          content.push(...tools);
          return { content };
        };

        for await (const evt of streamSSE(`${BACKEND}/api/agent/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userText,
            session_id: sessionRef.current,
          }),
          signal: abortSignal,
        })) {
          switch (evt.type) {
            case 'text':
              if (evt.delta) {
                text += evt.delta;
                yield build();
              }
              break;
            case 'interrupt': {
              const p = evt.payload;
              if (!p) break;
              if (p.interrupt_type === 'clarification') {
                // Natural chat: render the question as assistant text
                text += (text ? '\n\n' : '') + (p.questions ?? []).join('\n');
              } else if (p.interrupt_type === 'advise_upload') {
                tools.push(toolPart('advise_upload', { questions: p.questions }));
              } else if (p.interrupt_type === 'strategy_choice') {
                tools.push(
                  toolPart('strategy_choice', {
                    questions: p.questions,
                    options: p.options,
                  })
                );
              } else {
                // compile_failure or unknown → show questions as text
                text += (text ? '\n\n' : '') + (p.questions ?? []).join('\n');
              }
              yield build();
              break;
            }
            case 'compiled':
              if (evt.compiled_csv_path) {
                tools.push(
                  toolPart('dataset_compiled', {
                    compiled_csv_path: evt.compiled_csv_path,
                  })
                );
                onDatasetCompiled?.(sessionRef.current, evt.compiled_csv_path);
                yield build();
              }
              break;
            case 'done':
              if (evt.session_id) sessionRef.current = evt.session_id;
              break;
            case 'error':
              text += (text ? '\n\n' : '') + `⚠️ ${evt.message ?? 'An error occurred.'}`;
              yield build();
              break;
          }
        }

        yield build();
      },
    }),
    [sessionRef, onDatasetCompiled]
  );
}

// ── Generative UI: advise_upload card -------------------------------------

type UploadState =
  | { kind: 'idle' }
  | { kind: 'uploading'; note: string }
  | {
      kind: 'strategy';
      questions: string[];
      options: Array<{ option_id: string; label: string; description?: string }>;
    }
  | { kind: 'compiled'; path: string }
  | { kind: 'error'; message: string };

/** Consume an SSE generator, driving an upload/resume sub-flow to a terminal state. */
async function consumeToTerminal(
  gen: AsyncGenerator<SSEEvent>,
  onNote: (note: string) => void,
  onStrategy: (
    questions: string[],
    options: Array<{ option_id: string; label: string; description?: string }>
  ) => void,
  onCompiled: (path: string) => void,
  onError: (msg: string) => void
): Promise<void> {
  for await (const evt of gen) {
    if (evt.type === 'text' && evt.delta) onNote(evt.delta);
    else if (evt.type === 'interrupt' && evt.payload?.interrupt_type === 'strategy_choice') {
      onStrategy(evt.payload.questions ?? [], evt.payload.options ?? []);
      return;
    } else if (evt.type === 'interrupt' && evt.payload) {
      // compile_failure / re-upload prompt
      onNote((evt.payload.questions ?? []).join('\n'));
    } else if (evt.type === 'compiled' && evt.compiled_csv_path) {
      onCompiled(evt.compiled_csv_path);
      return;
    } else if (evt.type === 'error') {
      onError(evt.message ?? 'error');
      return;
    }
  }
}

const AdviseUploadToolUI = makeAssistantToolUI<
  { questions?: string[] },
  unknown
>({
  toolName: 'advise_upload',
  render: ({ args }) => {
    const { sessionRef, onDatasetCompiled } = useChatConfig();
    const [state, setState] = useState<UploadState>({ kind: 'idle' });
    const inputRef = useRef<HTMLInputElement>(null);

    const handleFile = async (file: File) => {
      setState({ kind: 'uploading', note: `Uploading ${file.name}…` });
      const form = new FormData();
      form.append('file', file);
      form.append('session_id', sessionRef.current);
      await consumeToTerminal(
        streamSSE(`${BACKEND}/api/upload`, { method: 'POST', body: form }),
        (note) => setState({ kind: 'uploading', note }),
        (questions, options) => setState({ kind: 'strategy', questions, options }),
        (path) => {
          setState({ kind: 'compiled', path });
          onDatasetCompiled?.(sessionRef.current, path);
        },
        (message) => setState({ kind: 'error', message })
      );
    };

    const handleStrategy = async (optionId: string) => {
      setState({ kind: 'uploading', note: 'Compiling with selected strategy…' });
      await consumeToTerminal(
        streamSSE(`${BACKEND}/api/agent/resume`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionRef.current, answer: optionId }),
        }),
        (note) => setState({ kind: 'uploading', note }),
        (questions, options) => setState({ kind: 'strategy', questions, options }),
        (path) => {
          setState({ kind: 'compiled', path });
          onDatasetCompiled?.(sessionRef.current, path);
        },
        (message) => setState({ kind: 'error', message })
      );
    };

    if (state.kind === 'compiled') {
      return <CompiledCardInner path={state.path} />;
    }
    if (state.kind === 'strategy') {
      return (
        <StrategyCardsInner
          questions={state.questions}
          options={state.options}
          onSelect={handleStrategy}
        />
      );
    }

    return (
      <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/5 p-4 my-2">
        <p className="text-sm text-slate-200 mb-3">
          {args.questions?.[0] ?? 'Your intent is clear. Please upload your dataset to continue.'}
        </p>
        {state.kind === 'uploading' ? (
          <p className="text-xs font-mono text-emerald-300 animate-pulse">{state.note}</p>
        ) : (
          <button
            id="upload-dataset-btn"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-bold text-white transition-colors"
            onClick={() => inputRef.current?.click()}
          >
            📁 Choose dataset file…
          </button>
        )}
        {state.kind === 'error' && (
          <p className="text-xs text-rose-400 mt-2">⚠️ {state.message}</p>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".zip,.csv,.parquet,.json,.xlsx,.mat,.tdms"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
      </div>
    );
  },
});

// ── Generative UI: strategy_choice card (top-level, from chat stream) -----

function StrategyCardsInner({
  questions,
  options,
  onSelect,
}: {
  questions: string[];
  options: Array<{ option_id: string; label: string; description?: string }>;
  onSelect: (optionId: string) => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <div className="my-2">
      {questions[0] && <p className="text-sm text-slate-200 mb-2">{questions[0]}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {options.map((opt) => (
          <button
            key={opt.option_id}
            id={`strategy-${opt.option_id}`}
            disabled={selected !== null}
            onClick={() => {
              setSelected(opt.option_id);
              onSelect(opt.option_id);
            }}
            className={`text-left rounded-xl border p-3 transition-all disabled:opacity-60 ${
              selected === opt.option_id
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-slate-700 bg-slate-900/60 hover:border-blue-400'
            }`}
          >
            <span className="block text-xs font-bold text-white">{opt.label}</span>
            {opt.description && (
              <span className="block text-[11px] text-slate-400 mt-1">{opt.description}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

const StrategyChoiceToolUI = makeAssistantToolUI<
  {
    questions?: string[];
    options?: Array<{ option_id: string; label: string; description?: string }>;
  },
  unknown
>({
  toolName: 'strategy_choice',
  render: ({ args }) => {
    const { sessionRef, onDatasetCompiled } = useChatConfig();
    const [state, setState] = useState<UploadState>({
      kind: 'strategy',
      questions: args.questions ?? [],
      options: args.options ?? [],
    });

    const handleStrategy = async (optionId: string) => {
      setState({ kind: 'uploading', note: 'Compiling with selected strategy…' });
      await consumeToTerminal(
        streamSSE(`${BACKEND}/api/agent/resume`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionRef.current, answer: optionId }),
        }),
        (note) => setState({ kind: 'uploading', note }),
        (questions, options) => setState({ kind: 'strategy', questions, options }),
        (path) => {
          setState({ kind: 'compiled', path });
          onDatasetCompiled?.(sessionRef.current, path);
        },
        (message) => setState({ kind: 'error', message })
      );
    };

    if (state.kind === 'compiled') return <CompiledCardInner path={state.path} />;
    if (state.kind === 'uploading')
      return <p className="text-xs font-mono text-blue-300 animate-pulse my-2">{state.note}</p>;
    if (state.kind === 'error')
      return <p className="text-xs text-rose-400 my-2">⚠️ {state.message}</p>;
    return (
      <StrategyCardsInner
        questions={state.kind === 'strategy' ? state.questions : []}
        options={state.kind === 'strategy' ? state.options : []}
        onSelect={handleStrategy}
      />
    );
  },
});

// ── Generative UI: dataset_compiled card ----------------------------------

function CompiledCardInner({ path }: { path: string }) {
  const { sessionRef, onDatasetCompiled } = useChatConfig();
  const fileName = path.split(/[\\/]/).pop();
  return (
    <div className="rounded-xl border border-emerald-500/50 bg-emerald-500/10 p-4 my-2 flex items-center gap-3">
      <span className="text-xl">✅</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold text-white">Dataset compiled and ready</p>
        <p className="text-[11px] font-mono text-slate-400 truncate" title={path}>
          {fileName}
        </p>
      </div>
      <button
        id="launch-data-explorer"
        className="shrink-0 inline-flex items-center gap-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-bold text-white transition-colors"
        onClick={() => onDatasetCompiled?.(sessionRef.current, path)}
      >
        Launch Data Explorer →
      </button>
    </div>
  );
}

const DatasetCompiledToolUI = makeAssistantToolUI<
  { compiled_csv_path: string },
  unknown
>({
  toolName: 'dataset_compiled',
  render: ({ args }) => <CompiledCardInner path={args.compiled_csv_path} />,
});

// ── Thread UI (headless primitives + Tailwind) ----------------------------

const UserMessage = () => (
  <MessagePrimitive.Root className="flex justify-end my-2">
    <div className="max-w-[80%] rounded-2xl bg-blue-600 px-4 py-2.5 text-xs text-white">
      <MessagePrimitive.Content />
    </div>
  </MessagePrimitive.Root>
);

const AssistantMessage = () => (
  <MessagePrimitive.Root className="flex justify-start my-2">
    <div className="max-w-[85%] rounded-2xl bg-slate-800/80 px-4 py-2.5 text-xs text-slate-100 border border-slate-700 whitespace-pre-wrap">
      <MessagePrimitive.Content
        components={{
          tools: {
            by_name: {
              advise_upload: AdviseUploadToolUI,
              strategy_choice: StrategyChoiceToolUI,
              dataset_compiled: DatasetCompiledToolUI,
            },
          },
        }}
      />
    </div>
  </MessagePrimitive.Root>
);

/** Auto-send an initial message once, if provided. */
function InitialMessageSender({ initialMessage }: { initialMessage?: string }) {
  const thread = useThreadRuntime();
  const sent = useRef(false);
  useEffect(() => {
    if (initialMessage && !sent.current) {
      sent.current = true;
      thread.append(initialMessage);
    }
  }, [initialMessage, thread]);
  return null;
}

function ThreadUI() {
  return (
    <ThreadPrimitive.Root className="flex flex-col h-full min-h-[420px]">
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto px-4 py-3 scrollbar-thin scrollbar-thumb-slate-700">
        <ThreadPrimitive.Empty>
          <div className="text-center text-slate-400 text-xs py-10">
            Tell me what operational task or prediction problem you want to solve.
          </div>
        </ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages
          components={{ UserMessage, AssistantMessage }}
        />
      </ThreadPrimitive.Viewport>

      <ComposerPrimitive.Root className="border-t border-slate-800 bg-slate-950/80 p-3 flex items-end gap-2">
        <ComposerPrimitive.Input
          rows={1}
          autoFocus
          placeholder="Message AIConnex…"
          className="flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900 p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-600"
        />
        <ComposerPrimitive.Send
          className="shrink-0 inline-flex items-center justify-center rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 h-9 w-9 text-white transition-colors"
          aria-label="Send"
        >
          ↑
        </ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  );
}

// ── Public component ------------------------------------------------------

interface ChatViewProps {
  /** Optional first message to send automatically on mount (from sample prompt pills) */
  initialMessage?: string;
  /** Called when Scout finishes compilation (session id + compiled csv path) */
  onDatasetCompiled?: (sessionId: string, compiledCsvPath: string) => void;
}

export const ChatView: React.FC<ChatViewProps> = ({ initialMessage, onDatasetCompiled }) => {
  const sessionRef = useRef<string>('');

  // Restore / persist session id via URL query param
  useEffect(() => {
    const existing = new URLSearchParams(window.location.search).get('session');
    if (existing) sessionRef.current = existing;
  }, []);

  const config = useMemo<ChatConfig>(
    () => ({
      sessionRef,
      onDatasetCompiled: (sid, path) => {
        if (sid) {
          const params = new URLSearchParams(window.location.search);
          params.set('session', sid);
          window.history.replaceState({}, '', `?${params.toString()}`);
        }
        onDatasetCompiled?.(sid, path);
      },
    }),
    [onDatasetCompiled]
  );

  return (
    <ChatConfigContext.Provider value={config}>
      <ChatViewInner initialMessage={initialMessage} />
    </ChatConfigContext.Provider>
  );
};

function ChatViewInner({ initialMessage }: { initialMessage?: string }) {
  const adapter = useAgentAdapter();
  const runtime = useLocalRuntime(adapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <InitialMessageSender initialMessage={initialMessage} />
      <ThreadUI />
    </AssistantRuntimeProvider>
  );
}

export default ChatView;
