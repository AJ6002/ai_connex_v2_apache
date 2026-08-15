import React, { useState } from 'react';
import { ModelRegistryItem } from '../types';

interface PipelineStudioViewProps {
  models: ModelRegistryItem[];
  onRegisterModel: (name: string, framework: string) => void;
  onRunInference: (jsonInput: string) => Promise<{
    status: string;
    action: string;
    confidence: number;
    latencyMs: number;
  }>;
}

export const PipelineStudioView: React.FC<PipelineStudioViewProps> = ({
  models,
  onRegisterModel,
  onRunInference,
}) => {
  const [jsonInput, setJsonInput] = useState<string>(`{
  "model_id": "alpha-v4",
  "features": {
    "engine_load": 85.2,
    "rpm": 1200,
    "vibration_index": 0.042,
    "temp_celsius": 92.5
  },
  "timestamp": "2026-07-22T14:30:00Z"
}`);

  const [isInferenceRunning, setIsInferenceRunning] = useState(false);
  const [predictionResult, setPredictionResult] = useState<{
    status: string;
    action: string;
    confidence: number;
    latencyMs: number;
  } | null>(null);

  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [newModelName, setNewModelName] = useState('');
  const [newModelFramework, setNewModelFramework] = useState('PyTorch / TensorRT');

  const handlePredict = async () => {
    setIsInferenceRunning(true);
    setPredictionResult(null);
    try {
      const res = await onRunInference(jsonInput);
      setPredictionResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsInferenceRunning(false);
    }
  };

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newModelName.trim()) return;
    onRegisterModel(newModelName.trim(), newModelFramework);
    setNewModelName('');
    setIsRegisterModalOpen(false);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1 */}
        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-4xl text-tas-blue">rocket_launch</span>
          </div>
          <span className="text-slate-400 font-mono text-xs uppercase tracking-wider font-semibold">
            ACTIVE DEPLOYMENTS
          </span>
          <div className="flex items-baseline gap-3 mt-2">
            <span className="font-mono text-3xl font-bold text-slate-900">98% Active</span>
            <span className="text-[#FF6B35] font-mono text-xs font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">check_circle</span> STABLE
            </span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-4 overflow-hidden">
            <div className="bg-tas-blue h-full w-[98%]"></div>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-4xl text-tas-blue">speed</span>
          </div>
          <span className="text-slate-400 font-mono text-xs uppercase tracking-wider font-semibold">
            AVG. RESPONSE LATENCY
          </span>
          <div className="flex items-baseline gap-3 mt-2">
            <span className="font-mono text-3xl font-bold text-slate-900">42ms</span>
            <span className="text-[#FF6B35] font-mono text-xs font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">arrow_downward</span> -4ms
            </span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-4 overflow-hidden">
            <div className="bg-tas-blue h-full w-[42%]"></div>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-4xl text-tas-blue">data_thresholding</span>
          </div>
          <span className="text-slate-400 font-mono text-xs uppercase tracking-wider font-semibold">
            DATA DRIFT INDEX
          </span>
          <div className="flex items-baseline gap-3 mt-2">
            <span className="font-mono text-3xl font-bold text-slate-900">12.4%</span>
            <span className="text-tas-red font-mono text-xs font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-sm">warning</span> CAUTION
            </span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-4 overflow-hidden">
            <div className="bg-tas-red h-full w-[12.4%]"></div>
          </div>
        </div>
      </div>

      {/* Main Grid: Model Registry & Inference Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Model Registry Table */}
        <div className="lg:col-span-7 flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
            <div>
              <h2 className="font-headline text-lg font-bold text-slate-900 tracking-tight">Model Registry</h2>
              <p className="text-xs text-slate-500">Production endpoints &amp; active versioning</p>
            </div>
            <button
              onClick={() => setIsRegisterModalOpen(true)}
              className="bg-tas-blue hover:bg-tas-blue-hover text-white px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 active:scale-95 shadow-xs"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              <span>Register New Model</span>
            </button>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100 text-slate-500 font-mono text-[11px] uppercase tracking-wider border-b border-slate-200">
                  <th className="px-5 py-3 font-semibold">Model Name</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Version</th>
                  <th className="px-5 py-3 font-semibold">Last Sync</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {models.map((model) => (
                  <tr key={model.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <span className="material-symbols-outlined text-tas-blue">neurology</span>
                        <div>
                          <span className="font-bold text-slate-900 block">{model.name}</span>
                          <span className="text-[10px] text-slate-400 font-mono">{model.framework}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded border ${
                          model.status === 'Deployed'
                            ? 'bg-[#FF6B35]/15 text-[#FF6B35] border-[#FF6B35]/30'
                            : model.status === 'Training'
                            ? 'bg-white/10 text-white border-white/20'
                            : model.status === 'Validation'
                            ? 'bg-white/6 text-white/60 border-white/15'
                            : 'bg-white/5 text-white/40 border-white/10'
                        }`}
                      >
                        {model.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-800 font-semibold">{model.version}</td>
                    <td className="px-5 py-3.5 text-slate-400 font-mono text-[11px]">{model.lastSync}</td>
                    <td className="px-5 py-3.5 text-right">
                      <button className="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-100 transition-colors">
                        <span className="material-symbols-outlined text-base">more_vert</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Inference Playground */}
        <div className="lg:col-span-5 flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-200 bg-slate-50/50">
            <h2 className="font-headline text-lg font-bold text-slate-900 tracking-tight">Inference Playground</h2>
            <p className="text-xs text-slate-500">Test live AI model endpoints with sample JSON telemetry</p>
          </div>

          <div className="p-5 flex-1 flex flex-col gap-4">
            <div className="flex-1 flex flex-col gap-1.5">
              <label className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                INPUT JSON PAYLOAD
              </label>
              <textarea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                spellCheck={false}
                rows={8}
                className="w-full p-3 bg-[#1A0530] text-[#FF6B35] font-mono text-xs rounded-lg border border-white/10 focus:ring-2 focus:ring-[#FF6B35]/50 outline-none resize-none leading-relaxed shadow-inner"
              />
            </div>

            <button
              onClick={handlePredict}
              disabled={isInferenceRunning}
              className="w-full bg-tas-blue hover:bg-tas-blue-hover text-white font-bold py-3 px-4 rounded-lg text-xs flex items-center justify-center gap-2 transition-all shadow-sm active:scale-98 disabled:opacity-50"
            >
              {isInferenceRunning ? (
                <>
                  <span className="material-symbols-outlined text-base animate-spin">sync</span>
                  <span>RUNNING INFERENCE...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-base">play_arrow</span>
                  <span>RUN PREDICTION</span>
                </>
              )}
            </button>

            {/* Prediction Result Display Box */}
            {predictionResult && (
              <div className="p-4 bg-[#1A0530] border-l-4 border-[#FF6B35] rounded-r-lg border border-white/10 animate-fadeIn">
                <div className="flex justify-between items-center mb-2 font-mono text-xs">
                  <span className="font-bold text-[#FF6B35]">PREDICTION RESULT</span>
                  <span className="text-[#FF6B35] font-bold">
                    CONFIDENCE: {predictionResult.confidence}%
                  </span>
                </div>

                <div className="bg-[#280B43] text-[#FF6B35] p-3 rounded-lg font-mono text-xs space-y-1">
                  <div>STATUS: "{predictionResult.status}"</div>
                  <div>RECOMMENDED ACTION: "{predictionResult.action}"</div>
                  <div className="text-white/35 text-[10px] pt-1 border-t border-white/10 mt-2">
                    LATENCY: {predictionResult.latencyMs}ms | COMPUTE: A100-80GB
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Register Model Modal */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h3 className="font-headline text-lg font-bold text-slate-900">Register New Model</h3>
              <button onClick={() => setIsRegisterModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
                  MODEL IDENTIFIER
                </label>
                <input
                  type="text"
                  required
                  value={newModelName}
                  onChange={(e) => setNewModelName(e.target.value)}
                  placeholder="e.g. Turbine_Vibration_Detector_V1"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
                  FRAMEWORK / RUNTIME
                </label>
                <select
                  value={newModelFramework}
                  onChange={(e) => setNewModelFramework(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
                >
                  <option value="PyTorch / TensorRT">PyTorch / TensorRT</option>
                  <option value="ONNX / CUDA">ONNX / CUDA</option>
                  <option value="XGBoost">XGBoost</option>
                  <option value="Scikit-Learn">Scikit-Learn</option>
                  <option value="LightGBM">LightGBM</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end gap-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsRegisterModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-tas-blue hover:bg-tas-blue-hover text-white text-xs font-bold rounded-lg shadow-xs"
                >
                  Register Model
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
