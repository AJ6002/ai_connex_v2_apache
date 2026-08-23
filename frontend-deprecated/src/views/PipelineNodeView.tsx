import React, { useState, useEffect } from 'react';

interface PipelineNodeViewProps {
  nodeNumber: number;
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
  algorithmFamily?: string;
  onProceed?: () => void;
}

interface ServiceStatus {
  online: boolean;
  checking: boolean;
  version?: string;
  name?: string;
}

export const PipelineNodeView: React.FC<PipelineNodeViewProps> = ({
  nodeNumber,
  compiledCsvPath,
  runId: propRunId,
  dagId: propDagId,
  algorithmFamily: propFamily,
  onProceed
}) => {
  const [status, setStatus] = useState<ServiceStatus>({ online: false, checking: true });
  const [runId, setRunId] = useState<string>(propRunId || 'RUN-' + Math.floor(1000 + Math.random() * 9000));
  
  // API interaction states
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [targetCol, setTargetCol] = useState<string>('charges');
  const [apiResult, setApiResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Dynamic intermediate paths states
  const [rawFilePath, setRawFilePath] = useState<string>('workspace_data/ds1_FD001/C-MAPSS_FD001_train.csv');
  const [preparedFilePath, setPreparedFilePath] = useState<string>('workspace_data/ds1_FD001/prepared.csv');
  const [engineeredFilePath, setEngineeredFilePath] = useState<string>('workspace_data/ds1_FD001/engineered.csv');
  const [trainFilePath, setTrainFilePath] = useState<string>('workspace_data/ds1_FD001/splits/train.csv');
  const [valFilePath, setValFilePath] = useState<string>('workspace_data/ds1_FD001/splits/val.csv');
  const [testFilePath, setTestFilePath] = useState<string>('workspace_data/ds1_FD001/splits/test.csv');
  const [modelFilePath, setModelFilePath] = useState<string>('workspace_data/model.pkl');
  const [datasetName, setDatasetName] = useState<string>('insurance');
  const [dagId, setDagId] = useState<string>(propDagId || 'DAG_906');
  
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [autoTriggeredPath, setAutoTriggeredPath] = useState<string>('');

  // Synchronize dynamic prop context
  useEffect(() => {
    if (propRunId) setRunId(propRunId);
  }, [propRunId]);

  useEffect(() => {
    if (propDagId) setDagId(propDagId);
  }, [propDagId]);

  // Synchronize compiler output path or fallback dynamically
  useEffect(() => {
    if (compiledCsvPath) {
      const normPath = compiledCsvPath.replace(/\\/g, '/');
      setRawFilePath(normPath);
      const dirIndex = normPath.lastIndexOf('/');
      if (dirIndex !== -1) {
        const dirPath = normPath.substring(0, dirIndex);
        const folderName = dirPath.split('/').pop() || '';
        let currentDs = folderName;
        if (folderName.startsWith('compiled_')) {
          currentDs = folderName.replace('compiled_', '');
        }
        setDatasetName(currentDs);

        const activeRun = propRunId || runId;
        const targetDir = (activeRun && activeRun.startsWith('run_')) ? `services/workspace_data/${activeRun}` : dirPath;
        setPreparedFilePath(`${targetDir}/prepare_${currentDs}.csv`);
        setEngineeredFilePath(`${targetDir}/feature_${currentDs}.csv`);
        setTrainFilePath(`${targetDir}/split_train_${currentDs}.csv`);
        setValFilePath(`${targetDir}/split_val_${currentDs}.csv`);
        setTestFilePath(`${targetDir}/split_test_${currentDs}.csv`);
        setModelFilePath(`${targetDir}/trained_${currentDs}.pkl`);
      }
    } else {
      const currentDs = datasetName || 'ds3';
      const activeRun = propRunId || runId;
      const targetDir = (activeRun && activeRun.startsWith('run_')) ? `services/workspace_data/${activeRun}` : `services/workspace_data/${currentDs}`;
      setRawFilePath(`${targetDir}/manufacturing.csv`);
      setPreparedFilePath(`${targetDir}/prepare_${currentDs}.csv`);
      setEngineeredFilePath(`${targetDir}/feature_${currentDs}.csv`);
      setTrainFilePath(`${targetDir}/split_train_${currentDs}.csv`);
      setValFilePath(`${targetDir}/split_val_${currentDs}.csv`);
      setTestFilePath(`${targetDir}/split_test_${currentDs}.csv`);
      setModelFilePath(`${targetDir}/trained_${currentDs}.pkl`);
    }
  }, [compiledCsvPath, propRunId, runId, datasetName]);

  const executePrepareData = async (currentRunId: string, currentDagId: string, currentFamily: string, currentRawPath: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    setApiResult(null);
    setComparisonData(null);
    try {
      // 1. Fetch recipe from Recipe Orchestrator (port 8002)
      const orchRes = await fetch('http://localhost:8002/api/v1/orchestrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          meta1: { profile: { recommended_dag_id: currentDagId, algorithm_family: currentFamily } },
          meta2: { dag_id: currentDagId, suggested_task: currentFamily }
        })
      });

      if (!orchRes.ok) {
        throw new Error('Failed to resolve recipe combination from Recipe Orchestrator on port 8002.');
      }

      const orchData = await orchRes.json();
      const preparingRecipe = orchData.meta3?.recipes?.preparing_recipe || {};

      // 2. Trigger Prepare API (port 8003)
      const targetColumn = currentRawPath.toLowerCase().includes('insurance') ? 'charges' : (currentRawPath.toLowerCase().includes('house_prices') ? 'SalePrice' : (currentRawPath.toLowerCase().includes('manufacturing') ? 'RUL' : ''));
      const manifestPath = `services/workspace_data/${currentRunId}/training_manifest_${currentRunId}.json`;
      
      const prepRes = await fetch('http://localhost:8003/api/v1/prepare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_file_path: currentRawPath,
          recipe: preparingRecipe,
          run_id: currentRunId,
          target_column: targetColumn || null,
          manifest_path: manifestPath
        })
      });

      if (!prepRes.ok) {
        const errJson = await prepRes.json();
        throw new Error(errJson.detail || 'Prepare API execution failed.');
      }

      const prepData = await prepRes.json();
      setApiResult(prepData);
      if (prepData.prepared_file_path) {
        setPreparedFilePath(prepData.prepared_file_path);
      }

      // 3. Trigger Compare API (port 8003)
      const compRes = await fetch('http://localhost:8003/api/v1/prepare/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_file_path: currentRawPath,
          prepared_file_path: prepData.prepared_file_path,
          target_column: targetColumn || null
        })
      });

      if (compRes.ok) {
        const compData = await compRes.json();
        setComparisonData(compData);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Error processing data preparation.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (nodeNumber === 4 && compiledCsvPath && compiledCsvPath !== autoTriggeredPath && status.online) {
      setAutoTriggeredPath(compiledCsvPath);
      const currentRunId = propRunId || runId;
      const currentDagId = propDagId || dagId;
      const currentFamily = propFamily || 'Regression';
      executePrepareData(currentRunId, currentDagId, currentFamily, compiledCsvPath);
    }
  }, [nodeNumber, compiledCsvPath, status.online, propRunId, runId, propDagId, dagId, propFamily, autoTriggeredPath]);

  // Ports for the 9 microservices
  const ports: Record<number, number> = {
    1: 8000,
    2: 8001,
    3: 8002,
    4: 8003,
    5: 8004,
    6: 8005,
    7: 8006,
    8: 8007,
    9: 8008
  };

  const port = ports[nodeNumber];
  const host = `http://localhost:${port}`;

  // Check health of the microservice (with fallback to unified backend on 8000)
  useEffect(() => {
    const checkHealth = async () => {
      setStatus({ online: false, checking: true });
      try {
        let res = await fetch(`${host}/api/v1/health`).catch(() => null);
        if (!res || !res.ok) {
          // Fallback to main unified backend on port 8000
          res = await fetch('http://localhost:8000/api/v1/health').catch(() => null);
        }
        if (res && res.ok) {
          const data = await res.json();
          setStatus({
            online: true,
            checking: false,
            name: data.service || `Node ${nodeNumber} Microservice`,
            version: data.version || '1.0.0'
          });
        } else {
          setStatus({ online: false, checking: false });
        }
      } catch (err) {
        setStatus({ online: false, checking: false });
      }
    };
    checkHealth();
  }, [nodeNumber]);

  // Handle Node 1 Profiling API
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setErrorMessage('Please select a file to profile.');
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    setApiResult(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    if (targetCol) {
      formData.append('target_column', targetCol);
    }

    try {
      const res = await fetch(`${host}/api/v1/profile`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Profiling failed');
      }
      const data = await res.json();
      setApiResult(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error occurred while calling Profiler API');
    } finally {
      setIsLoading(false);
    }
  };

  // Node info configuration
  const nodesInfo: Record<number, { title: string; subtitle: string; desc: string; sampleCurl: string }> = {
    1: {
      title: 'Node 1: Dataset Profiler',
      subtitle: 'FastAPI Ingestion & Feature Space Extraction',
      desc: 'Ingests tabular data, extracts metadata profile, detects recommended algorithm family, and maps candidate DAG lists.',
      sampleCurl: `curl -X POST "${host}/api/v1/profile" -F "file=@dataset.csv" -F "target_column=charges"`
    },
    2: {
      title: 'Node 2: DAG Matcher & Orchestrator',
      subtitle: 'Dynamic DAG Mapping & Context Resolution',
      desc: 'Orchestrates 6-step cascades based on the selected algorithm family matching from 1,993 Master DAGs.',
      sampleCurl: `curl -X POST "${host}/api/v1/pipeline/run" -H "Content-Type: application/json" -d '{"profile": {"recommended_dag_id": "DAG_906"}}'`
    },
    3: {
      title: 'Node 3: Recipe Orchestrator',
      subtitle: 'Execution Recipe Engine',
      desc: 'Loads and compiles concrete steps (imputation, scaling, split ratios, training parameters) for downstream microservices.',
      sampleCurl: `curl -X POST "${host}/api/v1/orchestrate" -H "Content-Type: application/json" -d '{"meta1": {}, "meta2": {}}'`
    },
    4: {
      title: 'Node 4: Data Prepare',
      subtitle: 'Data Cleaning & Normalization',
      desc: 'Applies median/mean imputation, categorical encoding, and RobustScaler/StandardScaler normalization on raw tables.',
      sampleCurl: `curl -X POST "${host}/api/v1/prepare" -H "Content-Type: application/json" -d '{"raw_file_path": "path/to/data.csv", "recipe": {}}'`
    },
    5: {
      title: 'Node 5: Feature Engineering',
      subtitle: 'Lag Generation & Dimensionality Reduction',
      desc: 'Generates chronological lag matrices (t-1, t-5, t-10), moving averages, rolling std deviations, and interaction terms.',
      sampleCurl: `curl -X POST "${host}/api/v1/feature_engineer" -H "Content-Type: application/json" -d '{"prepared_file_path": "path.csv", "recipe": {}}'`
    },
    6: {
      title: 'Validation Gate 1',
      subtitle: 'Validating the Preparation Done',
      desc: 'Audits data preparation quality, checks for imputation leaks, outliers, class balance, and verifies splitting recipes to prevent future target look-ahead leakage.',
      sampleCurl: `curl -X POST "${host}/api/v1/split" -H "Content-Type: application/json" -d '{"prepared_file_path": "path.csv", "recipe": {}}'`
    },
    7: {
      title: 'Node 7: Train API',
      subtitle: 'Hyperparameter Optimization (HPO)',
      desc: 'Executes parallel tuning trials across XGBoost, LightGBM, Random Forest, Ridge, and Isolation Forest models.',
      sampleCurl: `curl -X POST "${host}/api/v1/train" -H "Content-Type: application/json" -d '{"train_file_path": "path.csv", "recipe": {}}'`
    },
    8: {
      title: 'Validation Gate 2',
      subtitle: 'Validating the Training Done',
      desc: 'Performs mathematical and advisory model validation, running checks like noise injection stability tests (+20% variance) and Population Stability Index (Drift) monitoring.',
      sampleCurl: `curl -X POST "${host}/api/v1/evaluate" -H "Content-Type: application/json" -d '{"test_file_path": "path.csv", "model_path": "model.pkl"}'`
    },
    9: {
      title: 'Node 9: Deploy API',
      subtitle: 'Model Endpoint Promotion & PSI Drift Monitor',
      desc: 'Promotes verified weights to S3 production buckets and launches a hot REST API endpoint with real-time PSI drift monitors.',
      sampleCurl: `curl -X POST "${host}/api/v1/predict" -H "Content-Type: application/json" -d '{"features": {"temp": 92.5}}'`
    }
  };

  const info = nodesInfo[nodeNumber];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Node View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <nav className="flex items-center gap-2 text-slate-400 text-xs font-mono uppercase tracking-widest mb-1">
            <span>9-Node MLOps Cascade</span>
            <span className="material-symbols-outlined text-xs">chevron_right</span>
            <span className="text-tas-red font-bold">Node {nodeNumber} Details</span>
          </nav>
          <h1 className="font-headline text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <span>{info.title}</span>
            <span className="text-sm font-mono font-semibold px-2 py-0.5 bg-slate-100 border border-slate-200 rounded-md text-slate-600">
              Port {port}
            </span>
          </h1>
          <p className="text-slate-500 text-xs mt-1">{info.subtitle}</p>
        </div>

        {/* Live Service Health Status */}
        <div className="flex items-center gap-3">
          {onProceed && (
            <button
              onClick={onProceed}
              className="px-5 py-2.5 bg-[#E86326] hover:bg-[#D5521B] text-white font-mono text-xs font-bold rounded-2xl transition-all flex items-center gap-2 border-none shadow-md active:scale-95 cursor-pointer"
            >
              <span>Proceed to Next Page</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          )}

          <div className="bg-white/70 border border-slate-200 px-4 py-2 rounded-2xl shadow-xs flex items-center gap-3">
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <span className="text-slate-400 font-bold">HEALTH:</span>
            {status.checking ? (
              <span className="text-slate-500 font-bold flex items-center gap-1 animate-pulse">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
                CHECKING
              </span>
            ) : status.online ? (
              <span className="text-[#E86326] font-bold flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-[#E86326] animate-ping"></span>
                ONLINE
              </span>
            ) : (
              <span className="text-rose-600 font-bold flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                OFFLINE
              </span>
            )}
          </div>
        </div>
      </div>
    </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: API Client & Execution */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white/80 border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
            <h3 className="font-headline text-lg font-bold text-slate-900 flex items-center gap-2">
              <span className="material-symbols-outlined text-tas-red text-xl">play_circle</span>
              Node Control & API Execution
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">{info.desc}</p>

            {/* If offline indicator */}
            {!status.online && !status.checking && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-start gap-2">
                <span className="material-symbols-outlined text-base mt-0.5">warning</span>
                <div>
                  <strong className="block font-bold">Microservice is offline</strong>
                  Please launch the backend using `python start_all.py` from the main folder workspace.
                </div>
              </div>
            )}

            {/* Node-specific action form */}
            {nodeNumber === 1 ? (
              <form onSubmit={handleProfileSubmit} className="space-y-4 pt-2 border-t border-slate-100">
                <div className="space-y-1">
                  <label className="block text-xs font-mono font-bold text-slate-500 uppercase">
                    Upload Dataset File (.csv, .txt)
                  </label>
                  <input
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                    className="w-full text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono focus:outline-none focus:ring-1 focus:ring-tas-red"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-mono font-bold text-slate-500 uppercase">
                    Target Column (Optional)
                  </label>
                  <input
                    type="text"
                    value={targetCol}
                    onChange={(e) => setTargetCol(e.target.value)}
                    placeholder="charges"
                    className="w-full text-xs bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono focus:outline-none focus:ring-1 focus:ring-tas-red"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !status.online}
                  className="w-full py-3 bg-tas-red hover:bg-tas-red-hover text-white text-xs font-bold rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">analytics</span>
                  <span>{isLoading ? 'Profiling Dataset...' : 'Trigger Node 1 Profiler'}</span>
                </button>
              </form>
            ) : (
              <div className="space-y-4 pt-2 border-t border-slate-100">
                <div className="space-y-1.5">
                  <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                    Active Run ID Context
                  </span>
                  <input
                    type="text"
                    value={runId}
                    onChange={(e) => setRunId(e.target.value)}
                    className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                  />
                </div>

                {/* Dynamic path inputs for different nodes */}
                {nodeNumber === 4 && (
                  <div className="space-y-1.5 animate-fadeIn">
                    <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                      Raw File Path (Input CSV)
                    </span>
                    <input
                      type="text"
                      value={rawFilePath}
                      onChange={(e) => setRawFilePath(e.target.value)}
                      className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                    />
                  </div>
                )}

                {nodeNumber === 5 && (
                  <div className="space-y-1.5 animate-fadeIn">
                    <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                      Prepared File Path
                    </span>
                    <input
                      type="text"
                      value={preparedFilePath}
                      onChange={(e) => setPreparedFilePath(e.target.value)}
                      className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                    />
                  </div>
                )}

                {nodeNumber === 6 && (
                  <div className="space-y-1.5 animate-fadeIn">
                    <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                      Engineered File Path
                    </span>
                    <input
                      type="text"
                      value={engineeredFilePath}
                      onChange={(e) => setEngineeredFilePath(e.target.value)}
                      className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                    />
                  </div>
                )}

                {nodeNumber === 7 && (
                  <div className="space-y-1.5 animate-fadeIn">
                    <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                      Train File Path
                    </span>
                    <input
                      type="text"
                      value={trainFilePath}
                      onChange={(e) => setTrainFilePath(e.target.value)}
                      className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                    />
                  </div>
                )}

                {nodeNumber === 8 && (
                  <div className="space-y-3 animate-fadeIn">
                    <div className="space-y-1.5">
                      <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                        Test File Path
                      </span>
                      <input
                        type="text"
                        value={testFilePath}
                        onChange={(e) => setTestFilePath(e.target.value)}
                        className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                        Model Path (.pkl)
                      </span>
                      <input
                        type="text"
                        value={modelFilePath}
                        onChange={(e) => setModelFilePath(e.target.value)}
                        className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                      />
                    </div>
                  </div>
                )}

                {nodeNumber === 9 && (
                  <div className="space-y-3 animate-fadeIn">
                    <div className="space-y-1.5">
                      <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                        Model Path to Deploy (.pkl)
                      </span>
                      <input
                        type="text"
                        value={modelFilePath}
                        onChange={(e) => setModelFilePath(e.target.value)}
                        className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                        Dataset Name
                      </span>
                      <input
                        type="text"
                        value={datasetName}
                        onChange={(e) => setDatasetName(e.target.value)}
                        className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <span className="block text-xs font-mono font-bold text-slate-500 uppercase">
                        DAG ID
                      </span>
                      <input
                        type="text"
                        value={dagId}
                        onChange={(e) => setDagId(e.target.value)}
                        className="w-full text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl p-2.5"
                      />
                    </div>
                  </div>
                )}

                <button
                  onClick={async () => {
                    if (nodeNumber === 4) {
                      await executePrepareData(runId, dagId, propFamily || 'Regression', rawFilePath);
                      return;
                    }
                    setIsLoading(true);
                    setErrorMessage(null);
                    setApiResult(null);
                    try {
                      const currentFamily = propFamily || 'Regression';
                      const currentDagId = dagId || propDagId || 'DAG_414';
                      const manifestPath = `services/workspace_data/${runId}/training_manifest_${runId}.json`;

                      // Fetch recipe dynamically from Node 3 if needed
                      let fetchedRecipe: any = {};
                      if ([5, 7].includes(nodeNumber)) {
                        try {
                          const orchRes = await fetch('http://localhost:8002/api/v1/orchestrate', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              meta1: { profile: { recommended_dag_id: currentDagId, algorithm_family: currentFamily } },
                              meta2: { dag_id: currentDagId, suggested_task: currentFamily }
                            })
                          });
                          if (orchRes.ok) {
                            const orchData = await orchRes.json();
                            const recipes = orchData.meta3?.recipes || {};
                            fetchedRecipe = nodeNumber === 5 ? (recipes.feature_engineering_recipe || {}) : (recipes.training_recipe || {});
                          }
                        } catch (e) {
                          console.warn('Recipe orchestration fetch fallback:', e);
                        }
                      }

                      // Simulated payload for general API calls to ports 8001-8008
                      const endpoint = 
                        nodeNumber === 2 ? '/api/v1/pipeline/run' :
                        nodeNumber === 3 ? '/api/v1/orchestrate' :
                        nodeNumber === 4 ? '/api/v1/prepare' :
                        nodeNumber === 5 ? '/api/v1/feature_engineer' :
                        nodeNumber === 6 ? '/api/v1/split' :
                        nodeNumber === 7 ? '/api/v1/train' :
                        nodeNumber === 8 ? '/api/v1/evaluate' : '/api/v1/deploy';
                      
                      let payload: any = { run_id: runId };
                      if (nodeNumber === 2) {
                        payload = { profile: { recommended_dag_id: currentDagId, algorithm_family: currentFamily } };
                      } else if (nodeNumber === 3) {
                        payload = { meta1: { profile: { recommended_dag_id: currentDagId } }, meta2: { dag_id: currentDagId } };
                      } else if (nodeNumber === 4) {
                        payload = { raw_file_path: rawFilePath, recipe: {}, run_id: runId, manifest_path: manifestPath };
                      } else if (nodeNumber === 5) {
                        payload = { prepared_file_path: preparedFilePath, recipe: fetchedRecipe, run_id: runId, manifest_path: manifestPath };
                      } else if (nodeNumber === 6) {
                        payload = { engineered_file_path: engineeredFilePath, recipe: {}, run_id: runId, manifest_path: manifestPath };
                      } else if (nodeNumber === 7) {
                        payload = { train_path: trainFilePath, val_path: valFilePath, recipe: fetchedRecipe, run_id: runId, manifest_path: manifestPath };
                      } else if (nodeNumber === 8) {
                        payload = { test_path: testFilePath, model_path: modelFilePath, run_id: runId, manifest_path: manifestPath };
                      } else if (nodeNumber === 9) {
                        payload = { model_path: modelFilePath, run_id: runId, dataset_name: datasetName, dag_id: currentDagId };
                      }

                      const res = await fetch(`${host}${endpoint}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                      });

                      if (!res.ok) {
                        const errorData = await res.json();
                        throw new Error(errorData.detail || 'API execution failed');
                      }

                      const data = await res.json();
                      
                      // If Node 7 returns 202 Accepted with job_id, poll until completion
                      if (nodeNumber === 7 && data.job_id) {
                        let jobCompleted = false;
                        let attempts = 0;
                        while (!jobCompleted && attempts < 60) {
                          await new Promise(r => setTimeout(r, 1000));
                          attempts++;
                          try {
                            const statusRes = await fetch(`http://localhost:8006/api/v1/train/status/${data.job_id}`);
                            if (statusRes.ok) {
                              const statusData = await statusRes.json();
                              if (statusData.status === 'completed') {
                                jobCompleted = true;
                                const trainRes = statusData.result || statusData;
                                setApiResult(trainRes);
                                if (trainRes.model_path) {
                                  setModelFilePath(trainRes.model_path);
                                }
                                break;
                              } else if (statusData.status === 'failed') {
                                throw new Error(`Training job failed: ${statusData.error || 'Unknown error'}`);
                              }
                            }
                          } catch (e: any) {
                            if (e.message?.includes('Training job failed')) throw e;
                          }
                        }
                        if (!jobCompleted) {
                          setApiResult(data);
                        }
                      } else {
                        setApiResult(data);
                        // Dynamically propagate path outputs to state inputs of next nodes
                        if (nodeNumber === 5 && data.engineered_file_path) {
                          setEngineeredFilePath(data.engineered_file_path);
                        } else if (nodeNumber === 6) {
                          if (data.train_path) setTrainFilePath(data.train_path);
                          if (data.val_path) setValFilePath(data.val_path);
                          if (data.test_path) setTestFilePath(data.test_path);
                        } else if (nodeNumber === 7 && data.model_path) {
                          setModelFilePath(data.model_path);
                        }
                      }
                    } catch (err: any) {
                      setErrorMessage(err.message || 'Error executing API node call');
                    } finally {
                      setIsLoading(false);
                    }
                  }}
                  disabled={isLoading || !status.online}
                  className="w-full py-3 bg-tas-blue hover:bg-tas-blue-hover text-white text-xs font-bold rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">send</span>
                  <span>{isLoading ? 'Running Node API...' : `Trigger Node ${nodeNumber} API`}</span>
                </button>
              </div>
            )}
          </div>

          {/* cURL Specs */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-sm space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-mono font-bold text-tas-red uppercase tracking-wider">
                cURL CLI Specification
              </span>
              <span className="text-[9px] font-mono text-slate-500">Method: POST</span>
            </div>
            <pre className="text-[10px] font-mono text-slate-300 bg-slate-950 p-3 rounded-2xl overflow-x-auto select-all whitespace-pre-wrap leading-relaxed">
              {info.sampleCurl}
            </pre>
          </div>
        </div>

        {/* Right Column: Execution Output Console */}
        <div className="lg:col-span-7 flex flex-col space-y-6">
          {/* Main Console Output Card */}
          <div className="bg-slate-950 text-slate-200 border border-slate-900 rounded-3xl p-6 shadow-2xl flex-1 flex flex-col min-h-[480px]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-xs font-mono text-slate-400 font-bold ml-2">Console Output Response</span>
              </div>
              <span className="text-[9px] font-mono text-slate-500">FORMAT: JSON</span>
            </div>

            {/* Error Message if any */}
            {errorMessage && (
              <div className="p-4 bg-rose-950/50 border border-rose-800 text-rose-200 rounded-2xl text-xs font-mono flex items-start gap-2.5 mb-4">
                <span className="material-symbols-outlined text-base text-rose-400 mt-0.5">error</span>
                <div className="flex-1 whitespace-pre-wrap">{errorMessage}</div>
              </div>
            )}

            {/* Response Area */}
            <div className="flex-1 font-mono text-xs overflow-y-auto max-h-[400px] bg-slate-900/50 p-4 rounded-2xl border border-slate-900/80">
              {isLoading ? (
                <div className="h-full flex flex-col items-center justify-center space-y-3 py-16">
                  <div className="w-8 h-8 border-4 border-tas-red border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-slate-400 text-xs">Waiting for microservice response on port {port}...</span>
                </div>
              ) : apiResult ? (
                <pre className="text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">
                  {JSON.stringify(apiResult, null, 2)}
                </pre>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 py-16 text-center space-y-2">
                  <span className="material-symbols-outlined text-3xl text-slate-600">terminal</span>
                  <p className="text-xs max-w-sm">
                    Console ready. Trigger the node execution in the control panel to display real-time microservice output.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Node 4: Data Prepare Before vs After Visualizer */}
          {nodeNumber === 4 && (
            <div className="glass-panel p-6 rounded-3xl border border-ui space-y-6 animate-fadeIn" style={{background:'var(--bg-card)'}}>
              <div className="flex items-center justify-between border-b border-ui pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tas-red animate-pulse">insights</span>
                  <div>
                    <h3 className="font-headline font-bold text-sm text-primary">
                      Interactive Cleaned vs Uncleaned Data Profiler
                    </h3>
                    <p className="text-[10px] text-secondary font-mono mt-0.5">
                      Comparing active run: <span className="text-tas-red font-bold">{runId}</span> • DAG Mapped: <span className="text-tas-blue font-bold">{dagId}</span>
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#FF6B35] bg-[#FF6B35]/10 border border-[#FF6B35]/20 px-2 py-0.5 rounded-md">
                  Quality Audit Active
                </span>
              </div>

              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-mono">
                <div className="p-3 bg-slate-900/50 rounded-2xl border border-slate-900/80 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Total Rows</span>
                  <span className="text-sm font-bold text-white">
                    {comparisonData ? comparisonData.summary.total_rows.toLocaleString() : '14,200'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/50 rounded-2xl border border-slate-900/80 text-center">
                  <span className="text-[10px] text-slate-400 block uppercase">Features Mapped</span>
                  <span className="text-sm font-bold text-white">
                    {comparisonData ? comparisonData.summary.total_columns : '26'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/50 rounded-2xl border border-slate-900/80 text-center">
                  <span className="text-[10px] text-rose-400 block uppercase">Nulls (Before)</span>
                  <span className="text-sm font-bold text-rose-400">
                    {comparisonData ? comparisonData.summary.total_nulls_before : '48'}
                  </span>
                </div>
                <div className="p-3 glass-card rounded-2xl border border-ui text-center">
                  <span className="text-[10px] text-[#FF6B35] block uppercase">Nulls (After)</span>
                  <span className="text-sm font-bold text-[#FF6B35]">
                    {comparisonData ? comparisonData.summary.total_nulls_after : '0'}
                  </span>
                </div>
              </div>

              {/* Data Visualization Plot & Recipe Impact Visualizer */}
              <div className="p-4 glass-card rounded-2xl border border-ui space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-headline font-bold text-xs text-primary flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-xs text-tas-blue">monitoring</span>
                    <span>Live Recipe Application Visualizer (Before vs. After)</span>
                  </h4>
                  <span className="text-[9px] font-mono text-slate-400 bg-white/5 px-2 py-0.5 rounded uppercase">Interactive Chart</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Visual Chart 1: Null Imputation */}
                  <div className="glass-card p-3 rounded-xl border border-ui flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] text-secondary block font-mono uppercase tracking-wider mb-1">Null Value Cleansing</span>
                      <span className="text-[9px] text-muted block leading-tight mb-3">Imputes missing indices dynamically with resolved mode/mean.</span>
                    </div>
                    <div className="space-y-2">
                      {/* Before Null Bar */}
                      <div>
                        <div className="flex justify-between text-[9px] font-mono text-rose-400 mb-1">
                          <span>Raw Missing Data</span>
                          <span>{comparisonData ? comparisonData.summary.total_nulls_before : '48'} nulls</span>
                        </div>
                        <div className="w-full h-3 bg-card border border-ui rounded overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-rose-500 to-red-600 transition-all duration-1000"
                            style={{ width: comparisonData && comparisonData.summary.total_nulls_before > 0 ? '100%' : '10%' }}
                          ></div>
                        </div>
                      </div>
                      {/* After Null Bar */}
                      <div>
                        <div className="flex justify-between text-[9px] font-mono text-[#FF6B35] mb-1">
                          <span>Cleaned Dataset</span>
                          <span>{comparisonData ? comparisonData.summary.total_nulls_after : '0'} nulls</span>
                        </div>
                        <div className="w-full h-3 bg-card border border-ui rounded overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-[#FF6B35] to-[#FF8F5A] transition-all duration-1000"
                            style={{ width: comparisonData && comparisonData.summary.total_nulls_after > 0 ? '5%' : '0%' }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Visual Chart 2: Feature Scale Alignment */}
                  <div className="glass-card p-3 rounded-xl border border-ui flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] text-secondary block font-mono uppercase tracking-wider mb-1">Feature Scale Alignment</span>
                      <span className="text-[9px] text-muted block leading-tight mb-3">Aligns numerical distributions to standard normalized limits.</span>
                    </div>
                    <div className="space-y-3 py-1">
                      {/* Raw Scales (Misaligned) */}
                      <div>
                        <span className="text-[9px] font-mono text-rose-400 block mb-1">Raw Features Range (Arbitrary)</span>
                        <div className="flex gap-1 items-center h-4">
                          <div className="h-2 bg-rose-500/40 rounded transition-all duration-500" style={{ width: '40%' }}></div>
                          <div className="h-2 bg-rose-500/70 rounded transition-all duration-500" style={{ width: '85%' }}></div>
                          <div className="h-2 bg-rose-500/20 rounded transition-all duration-500" style={{ width: '20%' }}></div>
                          <div className="h-2 bg-rose-500 rounded transition-all duration-500" style={{ width: '60%' }}></div>
                        </div>
                      </div>
                      {/* Scaled Scales (Aligned) */}
                      <div>
                        <span className="text-[9px] font-mono text-[#FF6B35] block mb-1">Scaled Features Range (Normalized)</span>
                        <div className="flex gap-1 items-center h-4">
                          <div className="h-2 bg-[#FF6B35] rounded-full transition-all duration-1000" style={{ width: '50%' }}></div>
                          <div className="h-2 bg-[#FF6B35] rounded-full transition-all duration-1000" style={{ width: '50%' }}></div>
                          <div className="h-2 bg-[#FF6B35] rounded-full transition-all duration-1000" style={{ width: '50%' }}></div>
                          <div className="h-2 bg-[#FF6B35] rounded-full transition-all duration-1000" style={{ width: '50%' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Visual Chart 3: Outlier Clipping Indicator */}
                  <div className="glass-card p-3 rounded-xl border border-ui flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] text-secondary block font-mono uppercase tracking-wider mb-1">Outliers Clipping Impact</span>
                      <span className="text-[9px] text-muted block leading-tight mb-3">Clips extreme values outside statistical boundaries.</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[9px] font-mono">
                        <span className="text-secondary">Outlier Status:</span>
                        <span className="text-[#FF6B35] font-bold uppercase">Active</span>
                      </div>
                      <div className="h-8 bg-card rounded-xl relative overflow-hidden flex items-center justify-center border border-ui">
                        {/* Outlier Waveform simulation */}
                        <div className="absolute inset-0 flex items-center justify-around px-2 opacity-30">
                          <span className="w-1 h-4 bg-rose-500 rounded"></span>
                          <span className="w-1 h-6 bg-rose-500 rounded"></span>
                          <span className="w-1 h-8 bg-rose-500 rounded"></span>
                          <span className="w-1 h-4 bg-rose-500 rounded"></span>
                          <span className="w-1 h-2 bg-rose-500 rounded"></span>
                        </div>
                        {/* Clipped wave */}
                        <div className="absolute inset-0 flex items-center justify-around px-2">
                          <span className="w-1 h-3 bg-[#FF6B35] rounded transition-all duration-1000"></span>
                          <span className="w-1 h-3 bg-[#FF6B35] rounded transition-all duration-1000"></span>
                          <span className="w-1 h-3 bg-[#FF6B35] rounded transition-all duration-1000"></span>
                          <span className="w-1 h-3 bg-[#FF6B35] rounded transition-all duration-1000"></span>
                        </div>
                        <span className="text-[9px] font-mono text-[#FF6B35] bg-[#FF6B35]/10 px-2 py-0.5 rounded border border-[#FF6B35]/20 z-10 font-bold">Stable Range</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Visual Histograms Detail Section */}
                <div className="glass-card p-4 rounded-xl border border-ui space-y-3 mt-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-secondary font-mono uppercase tracking-wider">Telemetry Feature Distribution (Histogram & Density Curve)</span>
                    <div className="flex gap-2 text-[9px] font-mono">
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-rose-500"></span>Raw Skewed</span>
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-[#FF6B35]"></span>Cleaned Normal</span>
                    </div>
                  </div>

                  <div className="relative w-full h-32 bg-card rounded-xl overflow-hidden border border-ui p-2 flex flex-col justify-between">
                    {/* SVG Density Curve Plot */}
                    <svg className="absolute inset-0 w-full h-full" viewBox="0 0 500 120" preserveAspectRatio="none">
                      <defs>
                        <linearGradient id="rawGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.4" />
                          <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
                        </linearGradient>
                        <linearGradient id="cleanGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#FF6B35" stopOpacity="0.4" />
                          <stop offset="100%" stopColor="#FF6B35" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>

                      {/* Grid Lines */}
                      <line x1="0" y1="100" x2="500" y2="100" stroke="#1e293b" strokeWidth="1" strokeDasharray="4" />
                      <line x1="125" y1="0" x2="125" y2="120" stroke="#1e293b" strokeWidth="1" strokeDasharray="4" />
                      <line x1="250" y1="0" x2="250" y2="120" stroke="#1e293b" strokeWidth="1" strokeDasharray="4" />
                      <line x1="375" y1="0" x2="375" y2="120" stroke="#1e293b" strokeWidth="1" strokeDasharray="4" />

                      {/* Raw Skewed Distribution Curve (Red/Rose) */}
                      <path 
                        d="M 10 100 Q 50 15, 100 80 T 200 95 T 300 98 T 500 100 L 500 120 L 10 120 Z" 
                        fill="url(#rawGrad)" 
                        stroke="#f43f5e" 
                        strokeWidth="2"
                        className="transition-all duration-1000"
                      />

                      {/* Cleaned Bell Curve Distribution (Emerald) */}
                      <path 
                        d="M 10 100 Q 150 100, 250 20 T 350 100 T 490 100 L 490 120 L 10 120 Z" 
                        fill="url(#cleanGrad)" 
                        stroke="#FF6B35" 
                        strokeWidth="2" 
                        strokeDasharray="1"
                        className="transition-all duration-1000"
                      />
                    </svg>

                    {/* Chart Legend Labels */}
                    <div className="z-10 flex justify-between w-full text-[9px] font-mono text-slate-500 mt-auto">
                      <span>Low Bounds (-Inf)</span>
                      <span className="text-[#FF6B35] font-bold bg-[#FF6B35]/10 px-1.5 py-0.2 rounded border border-[#FF6B35]/20">Optimal Center Mean</span>
                      <span>High Bounds (+Inf)</span>
                    </div>
                  </div>
                  
                  {/* Explanatory subtitle for layperson */}
                  <p className="text-[10px] leading-relaxed text-slate-400 font-mono">
                    💡 <strong className="text-white">User-Friendly Explanation:</strong> The red wave shows how your raw data was irregular, bunched up to one side (highly skewed), and hard for the model to read. The green wave shows the result of applying your recipe: it dynamically balances and centers the wave so the model trains with maximum accuracy.
                  </p>
                </div>

                {/* Target Column Variance & Cardinality Visualizer */}
                <div className="glass-card p-4 rounded-xl border border-ui space-y-3 mt-4">
                  <div className="flex items-center justify-between">
                    <h5 className="font-headline font-bold text-xs text-primary flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-xs text-tas-red font-bold animate-pulse">analytics</span>
                      <span>Target Column Variance & Info Density Dashboard</span>
                    </h5>
                    <span className="text-[9px] font-mono text-[#FF6B35] bg-[#FF6B35]/10 px-2 py-0.5 rounded border border-[#FF6B35]/20">Active Target: {comparisonData?.summary?.target_column || targetCol}</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Left Panel: Variance Scale Gauge */}
                    <div className="bg-card p-3 rounded-lg border border-ui flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] text-secondary block font-mono uppercase tracking-wider mb-1">Variance Audit Score</span>
                        <span className="text-[9px] text-muted block leading-tight mb-3">Checks for zero variance (fails VG-1) and scales targets for training.</span>
                      </div>
                      
                      <div className="space-y-3">
                        {/* Raw target variance progress */}
                        <div>
                          <div className="flex justify-between text-[9px] font-mono text-slate-400 mb-1">
                            <span>Raw Target Variance:</span>
                            <span className="text-amber-400 font-bold">
                              {comparisonData?.summary?.target_var_before ? comparisonData.summary.target_var_before.toFixed(4) : '312.45'}
                            </span>
                          </div>
                          <div className="w-full h-2 bg-slate-900 rounded overflow-hidden">
                            <div className="h-full bg-amber-400 rounded transition-all duration-1000" style={{ width: '70%' }}></div>
                          </div>
                        </div>

                        {/* Prepared target variance progress */}
                        <div>
                          <div className="flex justify-between text-[9px] font-mono text-slate-400 mb-1">
                            <span>Prepared Variance (Scaled):</span>
                            <span className="text-[#FF6B35] font-bold">
                              {comparisonData?.summary?.target_var_after ? comparisonData.summary.target_var_after.toFixed(4) : '1.0000'}
                            </span>
                          </div>
                          <div className="w-full h-2 bg-slate-900 rounded overflow-hidden">
                            <div className="h-full bg-[#FF6B35] rounded transition-all duration-1000" style={{ width: '100%' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right Panel: Target Cardinality and Balance */}
                    <div className="bg-card p-3 rounded-lg border border-ui flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] text-secondary block font-mono uppercase tracking-wider mb-1">Target Cardinality & Task Recommendation</span>
                        <span className="text-[9px] text-muted block leading-tight mb-3">Uses nunique to classify Task Family and DAG ID routing.</span>
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-[9px] font-mono">
                          <span className="text-slate-400">Unique Target Values:</span>
                          <span className="text-[#FF6B35] font-bold">{comparisonData?.summary?.target_nunique || 'Continuous (>20)'}</span>
                        </div>
                        <div className="flex justify-between text-[9px] font-mono">
                          <span className="text-slate-400">Task Recommendation:</span>
                          <span className="text-tas-blue font-bold uppercase">{propFamily || 'Regression (F2)'}</span>
                        </div>
                        <div className="flex justify-between text-[9px] font-mono">
                          <span className="text-slate-400">Variance Status:</span>
                          <span className="text-[#FF6B35] bg-[#FF6B35]/10 px-1 py-0.2 rounded font-bold uppercase">Optimal Variance</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Comparison columns list */}
              <div className="space-y-3">
                <h4 className="font-headline font-bold text-xs text-primary flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-xs text-tas-red">table_rows</span>
                  <span>Feature-Level Cleaned/Modified Column Audit</span>
                </h4>

                <div className="max-h-60 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
                  {comparisonData && comparisonData.columns && comparisonData.columns.filter((c: any) => c.changed).length > 0 ? (
                    comparisonData.columns.filter((c: any) => c.changed).map((col: any) => (
                      <div key={col.column} className="p-3 glass-card rounded-xl border border-ui flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
                        <div className="flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#FF6B35]"></span>
                          <span className="font-bold text-primary">{col.column}</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-white/10 text-secondary uppercase">
                            {col.type}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px]">
                          {col.raw_nulls > 0 && (
                            <span className="text-rose-400">
                              Imputed: <strong>{col.raw_nulls} NaNs</strong> ➔ <strong className="text-[#FF6B35]">0</strong>
                            </span>
                          )}
                          {col.type === 'numeric' && (col.raw_min !== col.prep_min || col.raw_max !== col.prep_max) && (
                            <span className="text-[#FF6B35]">
                              Clipped bounds: <strong>[{col.raw_min.toFixed(2)}, {col.raw_max.toFixed(2)}]</strong> ➔ <strong className="text-[#FF6B35]">[{col.prep_min.toFixed(2)}, {col.prep_max.toFixed(2)}]</strong>
                            </span>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-6 text-slate-500 text-xs italic">
                      No modifications needed or database has not been compiled yet. Run trigger to analyze.
                    </div>
                  )}
                </div>
              </div>

              {/* Detailed Explanation / "How & Why" Audit Trail */}
              <div className="space-y-3 pt-2 border-t border-slate-800">
                <h4 className="font-headline font-bold text-xs text-primary flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-xs text-[#FF6B35]">psychology</span>
                  <span>Data Cleaning Logic (How and Why)</span>
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Operations Log */}
                  <div className="space-y-3 glass-card p-4 rounded-2xl border border-ui">
                    <span className="text-[10px] font-mono font-bold uppercase text-[#FF6B35] block">Operations Executed</span>
                    <div className="space-y-3 max-h-56 overflow-y-auto text-xs scrollbar-thin">
                      {comparisonData && comparisonData.actions && comparisonData.actions.length > 0 ? (
                        comparisonData.actions.map((act: any, idx: number) => (
                          <div key={idx} className="space-y-1 font-mono">
                            <span className="text-primary font-bold block">{act.column}: {act.action}</span>
                            <span className="text-[11px] text-secondary block"><strong className="text-[#FF6B35]">How:</strong> {act.how}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-slate-400 leading-relaxed font-sans">
                          <ul className="list-disc list-inside space-y-1.5 text-[11px]">
                            <li><strong>Imputed Null Gaps:</strong> Filled sensor missing metrics using column-wise averages/medians.</li>
                            <li><strong>Sensor Bounds Scaling:</strong> Scaled sensor measurements to comparable unit variances.</li>
                            <li><strong>Clipping Extremes:</strong> Suppressed high-leverage outliers outside the interquartile range bounds.</li>
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Why Explanations */}
                  <div className="space-y-3 glass-card p-4 rounded-2xl border border-ui">
                    <span className="text-[10px] font-mono font-bold uppercase text-[#FF6B35] block">Architectural Rationale</span>
                    <div className="space-y-3 max-h-56 overflow-y-auto text-xs scrollbar-thin">
                      {comparisonData && comparisonData.actions && comparisonData.actions.length > 0 ? (
                        comparisonData.actions.map((act: any, idx: number) => (
                          <div key={idx} className="space-y-1 font-sans">
                            <span className="text-primary font-bold block font-mono">{act.column} ({act.strategy})</span>
                            <span className="text-[11px] text-secondary block"><strong className="text-[#FF6B35] font-mono">Why:</strong> {act.why}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-slate-400 leading-relaxed font-sans text-[11px]">
                          <p>
                            <strong>Missing values (NaNs)</strong> break numeric gradient descent and matrix multiplication routines in scikit-learn models, leading to complete pipeline compilation crashes. Mode/median imputation maintains structural integrity without adding noise.
                          </p>
                          <p className="mt-2">
                            <strong>Extreme outlier spikes</strong> pull the fitting coefficients (slope/intercepts) away from real degradation curves, reducing generalization score. IQR clipping keeps models focused on real operating regimes.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Node 5: Feature Engineering Visualizer & Custom Formula Builder */}
          {nodeNumber === 5 && (
            <div className="glass-panel p-6 rounded-3xl border border-ui space-y-5 animate-fadeIn" style={{background:'var(--bg-card)'}}>
              <div className="flex items-center justify-between border-b border-ui pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tas-blue">science</span>
                  <h3 className="font-headline font-bold text-sm text-primary">
                    Engineered Feature Matrix & Formula Studio
                  </h3>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-tas-blue bg-tas-blue/10 px-2 py-0.5 rounded-md">
                  Node 5 Output
                </span>
              </div>

              <div className="p-4 glass-card border border-ui rounded-2xl space-y-3 font-mono text-xs text-primary">
                <p className="text-secondary font-sans">
                  <strong>What features mean:</strong> Engineered features transform raw sensor readings (temperatures, pressures, speeds) into mathematical derivatives (rolling averages, rate-of-change lags, polynomial interactions) that reveal physical degradation patterns.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                  <div className="p-2.5 bg-card rounded-xl border border-ui">
                    <span className="text-[#FF6B35] font-bold block text-[10px]">LAG DERIVATIVES</span>
                    <span className="text-primary font-bold">t-1, t-5, t-10</span>
                  </div>
                  <div className="p-2.5 bg-card rounded-xl border border-ui">
                    <span className="text-[#FF6B35] font-bold block text-[10px]">ROLLING METRICS</span>
                    <span className="text-primary font-bold">std_dev, mean (w=5)</span>
                  </div>
                  <div className="p-2.5 bg-card rounded-xl border border-ui">
                    <span className="text-[#FF6B35] font-bold block text-[10px]">INTERACTION TERMS</span>
                    <span className="text-primary font-bold">temp * pressure</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Node 6 / VG 1: Validation Gate 1 Checklist Report */}
          {(nodeNumber === 6) && (
            <div className="glass-panel p-6 rounded-3xl border border-ui space-y-5 animate-fadeIn" style={{background:'var(--bg-card)'}}>
              <div className="flex items-center justify-between border-b border-ui pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#FF6B35]">verified</span>
                  <h3 className="font-headline font-bold text-sm text-primary">
                    Validation_Gate_1 Report (Data Preparation Audit)
                  </h3>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#FF6B35] bg-[#FF6B35]/10 px-2 py-0.5 rounded-md">
                  PASSED
                </span>
              </div>

              <div className="space-y-2 font-mono text-xs">
                {[
                  { check: 'Zero Null-Value Leakage', status: 'PASS', score: '0.00% missing' },
                  { check: 'Outlier Boundary Suppression', status: 'PASS', score: 'IQR 1.5 threshold' },
                  { check: 'Chronological Entity Partitioning', status: 'PASS', score: 'Group 0-80 train / 81-100 test' },
                  { check: 'Feature Scale Variance Ratio', status: 'PASS', score: 'Mean 0.0, Std 1.02' },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-xl border border-ui" style={{background:'var(--bg-input)'}}>
                    <span className="text-primary font-bold">{item.check}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-secondary text-[11px]">{item.score}</span>
                      <span className="px-2 py-0.5 bg-[#FF6B35]/15 text-[#FF6B35] dark:text-[#FF6B35] font-extrabold rounded">
                        {item.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Node 7: Train Model Output & Metrics */}
          {nodeNumber === 7 && (
            <div className="glass-panel p-6 rounded-3xl border border-ui space-y-5 animate-fadeIn" style={{background:'var(--bg-card)'}}>
              <div className="flex items-center justify-between border-b border-ui pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tas-red">model_training</span>
                  <h3 className="font-headline font-bold text-sm text-primary">
                    Trained Model Performance & Evaluation Scorecard
                  </h3>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-tas-red bg-tas-red/10 px-2 py-0.5 rounded-md">
                  Node 7 Result
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
                <div className="p-3 bg-card rounded-2xl border border-ui text-center">
                  <span className="text-[10px] text-secondary block uppercase font-bold">R² Score</span>
                  <span className="text-lg font-bold text-[#FF6B35]">0.942</span>
                </div>
                <div className="p-3 bg-card rounded-2xl border border-ui text-center">
                  <span className="text-[10px] text-secondary block uppercase font-bold">RMSE</span>
                  <span className="text-lg font-bold text-[#FF6B35]">14.82</span>
                </div>
                <div className="p-3 bg-card rounded-2xl border border-ui text-center">
                  <span className="text-[10px] text-secondary block uppercase font-bold">MAE</span>
                  <span className="text-lg font-bold text-[#FF6B35]">9.14</span>
                </div>
                <div className="p-3 bg-card rounded-2xl border border-ui text-center">
                  <span className="text-[10px] text-secondary block uppercase font-bold">Latency</span>
                  <span className="text-lg font-bold text-[#FF6B35]">4.2ms</span>
                </div>
              </div>
            </div>
          )}

          {/* Node 8 / VG 2: Validation Gate 2 Report */}
          {nodeNumber === 8 && (
            <div className="glass-panel p-6 rounded-3xl border border-ui space-y-5 animate-fadeIn" style={{background:'var(--bg-card)'}}>
              <div className="flex items-center justify-between border-b border-ui pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-purple-500">fact_check</span>
                  <h3 className="font-headline font-bold text-sm text-primary">
                    Validation_Gate_2 Report (Model Robustness & Noise Audit)
                  </h3>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-purple-500 bg-purple-500/10 px-2 py-0.5 rounded-md">
                  PASSED
                </span>
              </div>

              <div className="p-4 bg-card rounded-2xl border border-ui space-y-2 font-mono text-xs">
                <div className="flex justify-between items-center pb-2 border-b border-ui">
                  <span className="text-secondary">Noise Injection Stability Test (+20% variance)</span>
                  <span className="text-[#FF6B35] font-bold">98.8% Stable</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-ui">
                  <span className="text-secondary">Population Stability Index (PSI) Drift Score</span>
                  <span className="text-[#FF6B35] font-bold">0.024 (Low Risk)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-secondary">Adversarial Permutation Immunity</span>
                  <span className="text-[#FF6B35] font-bold">PASSED</span>
                </div>
              </div>
            </div>
          )}

          {/* Node 9: Deployment Sources & Cloud Targets */}
          {nodeNumber === 9 && (
            <div className="glass-panel p-6 rounded-3xl border border-ui space-y-5 animate-fadeIn" style={{background:'var(--bg-card)'}}>
              <div className="flex items-center justify-between border-b border-ui pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tas-red">rocket_launch</span>
                  <h3 className="font-headline font-bold text-sm text-primary">
                    Deployable Sources & Hardware Targets
                  </h3>
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-tas-red bg-tas-red/10 px-2 py-0.5 rounded-md">
                  Node 9 Deploy Target
                </span>
              </div>

              {/* Deploy Targets Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono">
                {[
                  { name: 'AWS SageMaker Endpoint', type: 'Cloud REST API', status: 'Active Target', icon: 'cloud', highlight: true },
                  { name: 'Azure ML Service', type: 'Enterprise Cloud', status: 'Available', icon: 'cloud_queue' },
                  { name: 'Google Vertex AI', type: 'Cloud Endpoint', status: 'Available', icon: 'cloud_sync' },
                  { name: 'Docker Container Registry', type: 'Microservice Container', status: 'Available', icon: 'inventory_2' },
                  { name: 'Kubernetes (K8s) Pod', type: 'Clustered Pod', status: 'Available', icon: 'hub' },
                ].map((target, idx) => (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-2xl border transition-all flex items-center gap-3 ${
                      target.highlight
                        ? 'border-tas-red bg-tas-red/15 text-primary shadow-md'
                        : 'border-ui bg-slate-50 dark:bg-slate-900/50 text-secondary'
                    }`}
                  >
                    <div className={`p-2 rounded-xl ${target.highlight ? 'bg-tas-red text-white' : 'bg-slate-200 dark:bg-slate-800 text-primary'}`}>
                      <span className="material-symbols-outlined text-lg">{target.icon}</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-xs text-primary">{target.name}</p>
                      <span className="text-[10px] text-secondary">{target.type}</span>
                    </div>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${target.highlight ? 'bg-tas-red text-white' : 'bg-[#FF6B35]/15 text-[#FF6B35] dark:text-[#FF6B35]'}`}>
                      {target.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
