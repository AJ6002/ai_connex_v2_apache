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
  sender: 'user' | 'ai';
  text: string;
  options?: { label: string; value: string }[];
}

interface ExtractedInputs {
  targetColumn: string;
  problemType: string;
  timestampColumn: string;
  entityColumn: string;
}

// Easier question mappings for family requirements
const FAMILY_CONFIGS: Record<string, {
  name: string;
  required: ('problemType' | 'targetColumn' | 'timestampColumn' | 'entityColumn')[];
  questions: Record<string, string>;
  options?: Record<string, { label: string; value: string }[]>;
}> = {
  regression: {
    name: 'Continuous Calculation (estimating numbers)',
    required: ['targetColumn'],
    questions: {
      targetColumn: 'What is the exact name of the column containing the numbers you want the AI to calculate (like charges, SalePrice, or temperature)?'
    }
  },
  classification: {
    name: 'Category Selector (sorting into groups)',
    required: ['targetColumn'],
    questions: {
      targetColumn: 'What is the exact name of the column containing the category labels or yes/no answers you want to predict?'
    }
  },
  anomaly: {
    name: 'Outlier Detector (flagging errors)',
    required: [],
    questions: {}
  },
  'time-series': {
    name: 'Time Forecast (tracking values over time)',
    required: ['targetColumn', 'timestampColumn'],
    questions: {
      targetColumn: 'Which column holds the numerical values you want the model to forecast over time?',
      timestampColumn: 'Which column contains the timing sequence, cycle count, or date stamp (e.g. cycle, timestamp, date)?'
    }
  },
  clustering: {
    name: 'Natural Grouping (finding patterns)',
    required: [],
    questions: {}
  }
};

export const LandingView: React.FC<LandingViewProps> = ({ onNavigateToUpload }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'ai',
      text: 'Hello! I am the AI Connexx assistant. What calculation or prediction task would you like to solve using your dataset today?'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [inputs, setInputs] = useState<ExtractedInputs>({
    targetColumn: '',
    problemType: '',
    timestampColumn: '',
    entityColumn: ''
  });
  
  // Track currently active question key
  const [activeQuestion, setActiveQuestion] = useState<keyof ExtractedInputs | 'chooseProblemType' | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const samplePrompts = [
    { text: "Train a Remaining Useful Life (RUL) predictor for C-MAPSS turbofan engine SCADA logs.", icon: "speed", color: "#C8102E" },
    { text: "Detect anomalies and drifts in multivariate industrial sensor streams.", icon: "insights", color: "#1E47C8" },
    { text: "Build a failure classification pipeline with custom outlier thresholds.", icon: "warning", color: "#eab308" }
  ];

  // Simple rule-based NLP extraction
  const extractNLP = (text: string) => {
    const lower = text.toLowerCase();
    let problemType = '';
    let targetColumn = '';
    let timestampColumn = '';
    let entityColumn = '';

    // 1. Problem Type heuristics
    if (lower.includes('classify') || lower.includes('classification') || lower.includes('fault') || lower.includes('anomaly') || lower.includes('outlier') || lower.includes('yes/no') || lower.includes('categories')) {
      if (lower.includes('anomaly') || lower.includes('outlier') || lower.includes('unusual')) {
        problemType = 'anomaly';
      } else {
        problemType = 'classification';
      }
    } else if (lower.includes('time') || lower.includes('forecast') || lower.includes('series') || lower.includes('chronological')) {
      problemType = 'time-series';
    } else if (lower.includes('cluster') || lower.includes('group') || lower.includes('segment')) {
      problemType = 'clustering';
    } else if (lower.includes('predict') || lower.includes('regress') || lower.includes('continuous') || lower.includes('rul') || lower.includes('charges') || lower.includes('saleprice')) {
      problemType = 'regression';
    }

    // 2. Target Column heuristics
    const targetMatch = lower.match(/(?:predict|forecast|target is|target column is|estimate|calculate)\s+([a-zA-Z0-9_\-]+)/);
    if (targetMatch && targetMatch[1]) {
      targetColumn = targetMatch[1];
    } else {
      const commonColumns = ['rul', 'charges', 'saleprice', 'temperature', 'pressure', 'voltage', 'vibration', 'cycles', 'price', 'cost', 'failure', 'label'];
      for (const col of commonColumns) {
        if (lower.includes(col)) {
          targetColumn = col;
          break;
        }
      }
    }

    // 3. Time Index heuristics
    const timeMatch = lower.match(/(?:time|date|timestamp|cycle|epoch|sequence)\s+(?:column|index|is)?\s*([a-zA-Z0-9_\-]+)/);
    if (timeMatch && timeMatch[1]) {
      timestampColumn = timeMatch[1];
    } else {
      const commonTime = ['time_cycle', 'time', 'date', 'timestamp', 'datetime', 'cycle'];
      for (const t of commonTime) {
        if (lower.includes(t)) {
          timestampColumn = t;
          break;
        }
      }
    }

    // 4. Entity ID heuristics
    const entityMatch = lower.match(/(?:entity|asset|machine|device|unit|id|identifier)\s+(?:column|is)?\s*([a-zA-Z0-9_\-]+)/);
    if (entityMatch && entityMatch[1]) {
      entityColumn = entityMatch[1];
    } else {
      const commonEntity = ['unit_id', 'asset_id', 'machine_id', 'device_id', 'serial', 'id'];
      for (const e of commonEntity) {
        if (lower.includes(e)) {
          entityColumn = e;
          break;
        }
      }
    }

    return { problemType, targetColumn, timestampColumn, entityColumn };
  };

  const handleSend = (text: string) => {
    if (!text.trim()) return;

    // Append User Message
    const updatedMessages = [...messages, { sender: 'user' as const, text }];
    setMessages(updatedMessages);

    // If currently answering a targeted question:
    if (activeQuestion) {
      const cleanAnswer = text.trim();
      const updatedInputs = { ...inputs };

      if (activeQuestion === 'chooseProblemType') {
        const val = cleanAnswer.toLowerCase();
        if (val.includes('regression') || val.includes('continuous') || val.includes('number')) {
          updatedInputs.problemType = 'regression';
        } else if (val.includes('classify') || val.includes('categories') || val.includes('choice')) {
          updatedInputs.problemType = 'classification';
        } else if (val.includes('anomaly') || val.includes('outlier')) {
          updatedInputs.problemType = 'anomaly';
        } else if (val.includes('time') || val.includes('forecast')) {
          updatedInputs.problemType = 'time-series';
        } else {
          updatedInputs.problemType = 'clustering';
        }
      } else {
        updatedInputs[activeQuestion] = cleanAnswer;
      }

      setInputs(updatedInputs);
      evaluateNextStep(updatedInputs, updatedMessages);
      return;
    }

    // Otherwise, parse initial request using NLP
    const extracted = extractNLP(text);
    const mergedInputs = {
      targetColumn: extracted.targetColumn || inputs.targetColumn,
      problemType: extracted.problemType || inputs.problemType,
      timestampColumn: extracted.timestampColumn || inputs.timestampColumn,
      entityColumn: extracted.entityColumn || inputs.entityColumn
    };
    setInputs(mergedInputs);

    evaluateNextStep(mergedInputs, updatedMessages);
  };

  const evaluateNextStep = (currentInputs: ExtractedInputs, currentMessages: Message[]) => {
    // 1. If problem type is not known, ask for it
    if (!currentInputs.problemType) {
      setActiveQuestion('chooseProblemType');
      setMessages([
        ...currentMessages,
        {
          sender: 'ai',
          text: 'What type of calculation should the AI model perform on your dataset?',
          options: [
            { label: 'Continuous Number (e.g. Price, Temperature, RUL)', value: 'regression' },
            { label: 'Category Selection (e.g. yes/no outcomes or choice categories)', value: 'classification' },
            { label: 'Unusual Patterns (e.g. anomaly or outlier detection)', value: 'anomaly' },
            { label: 'Time Sequence Forecasting (e.g. trends over cycle counts or timestamp keys)', value: 'time-series' }
          ]
        }
      ]);
      return;
    }

    // 2. Identify required parameters for the active problem type
    const config = FAMILY_CONFIGS[currentInputs.problemType] || { required: [], name: 'Custom Modeling' };
    const missing = config.required.find(key => !currentInputs[key]);

    if (missing) {
      setActiveQuestion(missing);
      setMessages([
        ...currentMessages,
        {
          sender: 'ai',
          text: `✨ Mapped to: ${config.name}.\n\n${config.questions[missing]}`
        }
      ]);
      return;
    }

    // 3. All required inputs solved!
    setActiveQuestion(null);
    const summaryList = [
      `🎯 Problem Category: **${config.name}**`,
      currentInputs.targetColumn ? `📊 Target Value Column: **"${currentInputs.targetColumn}"**` : null,
      currentInputs.timestampColumn ? `📅 Timing Index Column: **"${currentInputs.timestampColumn}"**` : null,
      currentInputs.entityColumn ? `⚙️ Device ID Column: **"${currentInputs.entityColumn}"**` : null
    ].filter(Boolean).join('\n');

    setMessages([
      ...currentMessages,
      {
        sender: 'ai',
        text: `🎉 **Onboarding Successful!** I have successfully extracted all parameters for your training pipeline:\n\n${summaryList}\n\nWe are now ready to compile your dataset schema. Click **Proceed to Upload** below to continue.`
      }
    ]);
  };

  const isReadyToProceed = inputs.problemType && 
    (FAMILY_CONFIGS[inputs.problemType]?.required.every(key => !!inputs[key]) ?? true);

  return (
    <div className="min-h-[85vh] flex flex-col justify-center items-center px-4 relative select-none animate-fadeIn">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-tas-red/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-tas-blue/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="max-w-3xl w-full text-center space-y-6 relative z-10">
        {/* Dynamic header - shrinks slightly when messages are active */}
        <div className={`flex flex-col items-center gap-3 transition-all duration-500 ${messages.length > 1 ? 'scale-90 opacity-90' : ''}`}>
          <TasLogo className="h-16 animate-pulse" showSubtitle={false} />
          <h1 className="font-headline text-3xl sm:text-4xl font-black tracking-tight text-[#0F172A]">
            AI Connexx
          </h1>
          <p className="text-sm font-mono text-slate-500 max-w-xl">
            Type your operational maintenance goals below. Our compiler will automatically assign optimal data topology, match DAG schemas, and compile training recipes.
          </p>
        </div>

        {/* Interactive Chat Window Container */}
        <div className="glass-panel rounded-3xl border border-slate-200/80 shadow-2xl p-5 text-left bg-white/95 flex flex-col gap-4 overflow-hidden min-h-[300px] max-h-[500px]">
          {/* Messages log */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-slate-300">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600 text-white font-sans' 
                    : 'bg-slate-100 text-slate-800 font-mono border border-slate-200'
                }`}>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                  
                  {/* Option buttons for easy clicking */}
                  {msg.options && (
                    <div className="flex flex-wrap gap-2 mt-3 pt-2 border-t border-slate-200">
                      {msg.options.map((opt, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setInputText('');
                            handleSend(opt.label);
                          }}
                          className="px-3 py-1.5 bg-white hover:bg-blue-50 text-blue-600 border border-blue-300 hover:border-blue-400 font-sans text-[11px] font-bold rounded-xl transition-all cursor-pointer shadow-xs active:scale-95"
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Control Input Action Row */}
          <div className="border-t border-slate-100 pt-3">
            {isReadyToProceed ? (
              <div className="flex justify-center py-2 animate-bounce">
                <button
                  onClick={() => onNavigateToUpload(messages[1]?.text || 'Pipeline Studio configuration', inputs)}
                  className="px-8 py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:scale-105 text-white text-xs font-mono font-bold rounded-2xl shadow-xl transition-all flex items-center gap-2 border-none cursor-pointer"
                >
                  <span>Proceed to Upload Page</span>
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </button>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!inputText.trim()) return;
                  handleSend(inputText);
                  setInputText('');
                }}
                className="flex items-center gap-2 p-1 border border-slate-200 focus-within:border-blue-500 rounded-2xl bg-slate-50 transition-all"
              >
                <span className="material-symbols-outlined text-slate-400 pl-2 pr-1 text-base select-none">chat</span>
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={activeQuestion ? "Type your answer here..." : "What operational task would you like to solve?..."}
                  className="flex-1 bg-transparent border-none text-slate-800 placeholder-slate-400 focus:outline-none text-xs font-sans py-2.5 px-1"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-mono font-bold rounded-xl shadow-md transition-all flex items-center gap-1 border-none cursor-pointer"
                >
                  <span>Send</span>
                  <span className="material-symbols-outlined text-xs">send</span>
                </button>
              </form>
            )}
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
