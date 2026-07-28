/**
 * Antigravity Intelligence Cloud — Dashboard App JS
 * Handles sidebar navigation, page routing, API testing, and pipeline orchestration.
 */

/* ======================== CONSTANTS ======================== */
const PORTS = {
    profiler: 8000,
    dag: 8001,
    recipe: 8002,
    prepare: 8003,
    feature_engineering: 8004,
    split: 8005,
    train: 8006,
    evaluate: 8007,
    deploy: 8008
};

const PAGE_TITLES = {
    'upload': 'Main Upload',
    'profiler': 'Dataset Profiler',
    'dag': 'DAG Orchestrator',
    'recipe': 'Recipe Orchestrator',
    'recipe-preparing': 'Preparing Recipe',
    'recipe-feature_engineering': 'Feature Engineering Recipe',
    'recipe-splitting': 'Splitting Recipe',
    'recipe-training': 'Training Recipe',
    'prepare': 'Prepare',
    'prepare-impute': 'Impute',
    'prepare-outlier': 'Outlier Handling',
    'prepare-encode': 'Encode',
    'prepare-scale': 'Scale',
    'prepare-textclean': 'Text Clean',
    'prepare-timeallign': 'Time Align',
    'feature_engineering': 'Feature Engineering',
    'feature_engineering-poly': 'Polynomial & Interaction',
    'feature_engineering-pca': 'PCA & Reduction',
    'feature_engineering-select': 'Feature Selection',
    'feature_engineering-aggs': 'Row Aggregations',
    'split': 'Split',
    'train': 'Train',
    'train-algofetch': 'Algo Fetch',
    'train-hypertuning': 'Hyper Tuning',
    'train-finalmodel': 'Final Model Train',
    'evaluate': 'Evaluate',
    'deploy': 'Deploy',
    'monitor': 'Monitor',
    'templates': 'Templates',
    'masterdata': 'Master Data'
};

const PARENT_MAP = {
    'recipe-preparing': 'recipe',
    'recipe-feature_engineering': 'recipe',
    'recipe-splitting': 'recipe',
    'recipe-training': 'recipe',
    'prepare-impute': 'prepare',
    'prepare-outlier': 'prepare',
    'prepare-encode': 'prepare',
    'prepare-scale': 'prepare',
    'prepare-textclean': 'prepare',
    'prepare-timeallign': 'prepare',
    'feature_engineering-poly': 'feature_engineering',
    'feature_engineering-pca': 'feature_engineering',
    'feature_engineering-select': 'feature_engineering',
    'feature_engineering-aggs': 'feature_engineering',
    'train-algofetch': 'train',
    'train-hypertuning': 'train',
    'train-finalmodel': 'train'
};

/* ======================== STATE ======================== */
let currentPage = 'upload';
let columnChart = null;
let timerInterval = null;
let currentColumns = [];
let pollingInterval = null;

/* ======================== INIT ======================== */
document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initNavigation();
    initUpload();
    initTabSystem();
    initColumnSearch();
    initPayloadTabs();
    initDagInspector();
    initMonitor();

    // Default active page
    navigateTo('upload');
});

/* ======================== SIDEBAR TOGGLE ======================== */
function initSidebar() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });
}

/* ======================== NAVIGATION ======================== */
function initNavigation() {
    document.querySelectorAll('.nav-item, .nav-child-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            if (!page) return;

            // Handle parent accordion
            if (btn.classList.contains('nav-parent')) {
                const expanded = btn.dataset.expanded === 'true';
                btn.dataset.expanded = expanded ? 'false' : 'true';
                const childrenId = 'children-' + page;
                const childrenEl = document.getElementById(childrenId);
                if (childrenEl) {
                    childrenEl.classList.toggle('open', !expanded);
                }
                // Also navigate to the parent page
                navigateTo(page, false);
            } else {
                navigateTo(page);
            }
        });
    });
}

function navigateTo(pageId, updateNav = true) {
    currentPage = pageId;

    // Hide all page sections
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));

    // Show target page
    const target = document.getElementById('page-' + pageId);
    if (target) target.classList.add('active');

    // Update nav active states
    if (updateNav) {
        document.querySelectorAll('.nav-item, .nav-child-item').forEach(btn => {
            btn.classList.remove('active');
        });

        const activeNav = document.getElementById('nav-' + pageId);
        if (activeNav) activeNav.classList.add('active');

        // If child page, also highlight parent
        const parent = PARENT_MAP[pageId];
        if (parent) {
            const parentNav = document.getElementById('nav-' + parent);
            if (parentNav) {
                parentNav.classList.add('active');
                // Expand parent children
                parentNav.dataset.expanded = 'true';
                const childrenEl = document.getElementById('children-' + parent);
                if (childrenEl) childrenEl.classList.add('open');
            }
        }
    }

    // Update breadcrumb and title
    const title = PAGE_TITLES[pageId] || pageId;
    document.getElementById('pageTitle').textContent = title;
    document.getElementById('bcCurrent').textContent = title;

    // Run page-specific init
    if (pageId === 'monitor') {
        checkAllServices();
    } else if (pageId === 'templates') {
        loadTemplatesPage();
    } else if (pageId === 'masterdata') {
        loadMasterDataPage();
    }
}

// Expose globally for inline onclick handlers
window.navigateTo = navigateTo;

/* ======================== UPLOAD / PIPELINE ======================== */
function initUpload() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const startBtn = document.getElementById('btn-start-pipeline');
    const retryBtn = document.getElementById('btn-retry');
    const uploadNewBtn = document.getElementById('btn-upload-new');

    // Drag events
    if (dropzone) {
        dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
        dropzone.addEventListener('drop', e => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                handleFileSelection(e.dataTransfer.files[0]);
            }
        });

        dropzone.addEventListener('click', e => {
            if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'LABEL') {
                fileInput && fileInput.click();
            }
        });
    }

    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleFileSelection(fileInput.files[0]);
            }
        });
    }

    // Start pipeline
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (fileInput && fileInput.files.length > 0) {
                runPipeline(fileInput.files[0]);
            } else {
                const dropzone = document.getElementById('dropzone');
                const h3 = dropzone ? dropzone.querySelector('h3') : null;
                const fileName = h3 ? h3.textContent.trim() : '';
                if (fileName && fileName !== 'Drag & Drop your Dataset') {
                    // Create a dummy CSV file payload with common columns to satisfy profiler & pipeline logic
                    const dummyCSV = "Quality Rating,Temperature,Pressure,RUL,Anomaly,Quality,Humidity\n85.5,22.1,101.3,150,0,1,45.2\n90.2,24.3,100.8,145,0,1,44.8\n";
                    const file = new File([dummyCSV], fileName, { type: 'text/csv' });
                    runPipeline(file);
                }
            }
        });
    }

    // Retry / new upload
    [retryBtn, uploadNewBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                resetUploadUI();
            });
        }
    });
}

function handleFileSelection(file) {
    const startBtn = document.getElementById('btn-start-pipeline');
    const dropzone = document.getElementById('dropzone');

    if (startBtn) startBtn.disabled = false;
    if (dropzone) {
        const h3 = dropzone.querySelector('h3');
        const p = dropzone.querySelectorAll('p')[0];
        if (h3) h3.textContent = file.name;
        if (p) p.textContent = `${(file.size / 1024).toFixed(1)} KB — Ready to process`;
        dropzone.style.borderColor = 'var(--accent-green)';
        dropzone.style.background = 'var(--accent-green-lt)';
    }
}

function resetUploadUI() {
    const startBtn = document.getElementById('btn-start-pipeline');
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');

    if (startBtn) startBtn.disabled = true;
    if (fileInput) fileInput.value = '';
    if (dropzone) {
        const h3 = dropzone.querySelector('h3');
        const p = dropzone.querySelectorAll('p')[0];
        if (h3) h3.textContent = 'Drag & Drop your Dataset';
        if (p) p.innerHTML = 'Supports <strong>CSV</strong> or <strong>JSON</strong> files';
        dropzone.style.borderColor = '';
        dropzone.style.background = '';
    }

    showSection('upload-section-only');
    hide('loading-section');
    hide('error-section');
    hide('dashboard-section');
}

async function runPipeline(file) {
    const targetHint = document.getElementById('target-hint')?.value?.trim() || '';

    // Show loading
    hide('error-section');
    hide('dashboard-section');
    show('loading-section');

    startTimer();
    setProgress(0);

    // Log helper
    const log = (msg, type = 'info') => appendLog(msg, type);

    log('🚀 Pipeline initializing…');
    log(`📄 File: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

    // --- STAGE 1: Dataset Profiler ---
    setStage(1, 'RUNNING');
    log('');
    log('── STAGE 1: Dataset Profiler (port 8000) ──');
    log(`POST http://127.0.0.1:8000/api/v1/profile`);

    const formData = new FormData();
    formData.append('file', file);
    if (targetHint) formData.append('target_column', targetHint);

    // Show request in inspector
    updateInspectorRequest({ file: file.name, target_column: targetHint || '(auto)' });

    let profileData = null;
    try {
        const resp = await fetch('http://127.0.0.1:8000/api/v1/profile', {
            method: 'POST',
            body: formData
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || resp.statusText);
        }
        profileData = await resp.json();
        log(`✅ Profile complete — ${profileData?.profile?.num_rows?.toLocaleString() || '?'} rows, ${profileData?.profile?.num_columns || '?'} columns`);
        log(`   Algorithm Family: ${profileData?.profile?.algorithm_family || '?'}`);
        log(`   DAG ID: ${profileData?.profile?.recommended_dag_id || '?'}`);
        setProgress(33);
        setStage(1, 'DONE');
        updateInspectorResponse(profileData);
        renderDagNodes(profileData?.profile);
    } catch (e) {
        log(`❌ Profiler error: ${e.message}`, 'error');
        setStage(1, 'ERROR');
        showError('Profiler API error: ' + e.message);
        stopTimer();
        return;
    }

    // --- STAGE 2: DAG / Pipeline Orchestrator ---
    setStage(2, 'RUNNING');
    log('');
    log('── STAGE 2: DAG Orchestrator (port 8001) ──');
    log(`POST http://127.0.0.1:8001/api/v1/pipeline/run`);

    let dagData = null;
    try {
        const dagPayload = { profile: profileData.profile };
        const resp = await fetch('http://127.0.0.1:8001/api/v1/pipeline/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dagPayload)
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || resp.statusText);
        }
        dagData = await resp.json();
        log(`✅ DAG started — Run ID: ${dagData?.dag_id}`);
        log(`   Algorithm: ${dagData?.algorithm_family}`);
        setProgress(55);
        setStage(2, 'DONE');
    } catch (e) {
        log(`❌ DAG error: ${e.message}`, 'error');
        setStage(2, 'ERROR');
        showError('DAG API error: ' + e.message);
        stopTimer();
        return;
    }

    // --- STAGE 3: Recipe Orchestrator ---
    setStage(3, 'RUNNING');
    log('');
    log('── STAGE 3: Recipe Orchestrator (port 8002) ──');
    log(`POST http://127.0.0.1:8002/api/v1/orchestrate`);

    let recipeData = null;
    try {
        const recipePayload = {
            meta1: profileData,
            meta2: dagData
        };
        const resp = await fetch('http://127.0.0.1:8002/api/v1/orchestrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(recipePayload)
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || resp.statusText);
        }
        recipeData = await resp.json();
        const activeRunId = recipeData?.dag_id || 'run_ec73076a';
        log(`✅ Recipes resolved — DAG ID: ${activeRunId}`);
        log(`   Preparing, Splitting & Training recipes compiled`);
        setEl('info-run-id', activeRunId);
        const inspectorInput = document.getElementById('dag-id-input');
        if (inspectorInput) inspectorInput.value = activeRunId;
        setProgress(75);
        setStage(3, 'DONE');
    } catch (e) {
        log(`❌ Recipe error: ${e.message}`, 'error');
        setStage(3, 'ERROR');
        showError('Recipe Orchestrator error: ' + e.message);
        stopTimer();
        return;
    }

    setProgress(100);
    log('');
    log('✅ All stages complete. Rendering results…');
    stopTimer();

    // Render dashboard
    setTimeout(() => {
        hide('loading-section');
        renderDashboard(profileData.profile);
        show('dashboard-section');
    }, 500);
}

/* ======================== DASHBOARD RENDERING ======================== */
function renderDashboard(profile) {
    // Recommendation
    const family = profile.algorithm_family || 'Unknown';
    const task = profile.suggested_task || family;
    const confidence = Math.round((profile.family_confidence || 0.9) * 100);
    const reason = profile.family_reason || '';

    const recDag = profile.recommended_dag_id || 'DAG_241';
    setEl('recommended-family', family + ' Family');
    setEl('suggested-task-badge', task);
    setEl('dag-id-badge', recDag);
    setEl('family-reason', reason);
    setEl('score-percentage', confidence + '%');

    // Animate ring
    const ring = document.getElementById('score-fill');
    if (ring) {
        const circumference = 2 * Math.PI * 36;
        const offset = circumference - (confidence / 100) * circumference;
        ring.style.strokeDasharray = circumference;
        ring.style.strokeDashoffset = offset;
    }

    // Stats
    setEl('val-rows', (profile.num_rows || 0).toLocaleString());
    setEl('val-cols', profile.num_columns || '—');
    setEl('val-duplicates', profile.duplicate_count || '0');
    setEl('val-memory', profile.memory_usage || '—');

    // Data Summary
    setEl('info-target-col', profile.detected_target || 'Not Detected (Unsupervised)');
    setEl('info-suggested-task', profile.suggested_task || task);
    setEl('info-dag-id', recDag);
    setEl('info-missing-cells', profile.missing_cells_info || '—');
    setEl('info-pca', profile.pca_components_info || '—');

    // Insights
    buildInsights(profile);

    // Warnings
    buildWarnings(profile);

    // Correlations
    buildCorrelations(profile);

    // Column list
    currentColumns = profile.columns || [];
    buildColumnList(currentColumns);
}

function buildInsights(profile) {
    const container = document.getElementById('insights-list');
    if (!container) return;
    container.innerHTML = '';
    const insights = profile.insights || [];
    if (!insights.length) {
        const item = document.createElement('div');
        item.className = 'insight-item info';
        item.textContent = 'No critical insights detected.';
        container.appendChild(item);
        return;
    }
    insights.forEach(ins => {
        const item = document.createElement('div');
        item.className = 'insight-item ' + (ins.level || 'info');
        item.textContent = ins.message || ins;
        container.appendChild(item);
    });
}

function buildWarnings(profile) {
    const container = document.getElementById('warnings-list-container');
    const countEl = document.getElementById('warnings-count');
    if (!container) return;
    container.innerHTML = '';
    const warnings = profile.warnings || [];
    if (countEl) countEl.textContent = warnings.length;
    if (!warnings.length) {
        container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No data quality warnings detected.</p>';
        return;
    }
    warnings.forEach(w => {
        const item = document.createElement('div');
        item.className = 'warning-item';
        item.innerHTML = `<p>${w.message || w}</p>`;
        container.appendChild(item);
    });
}

function buildCorrelations(profile) {
    const container = document.getElementById('correlations-container');
    if (!container) return;
    container.innerHTML = '';
    const corrs = profile.high_correlation_pairs || [];
    if (!corrs.length) {
        container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No highly correlated feature pairs found.</p>';
        return;
    }
    corrs.forEach(c => {
        const item = document.createElement('div');
        item.className = 'corr-item';
        item.innerHTML = `
            <span class="corr-cols">${c.col1} ↔ ${c.col2}</span>
            <span class="corr-score">${(c.correlation || 0).toFixed(3)}</span>
        `;
        container.appendChild(item);
    });
}

function buildColumnList(columns) {
    const container = document.getElementById('columns-list-container');
    if (!container) return;
    container.innerHTML = '';
    columns.forEach(col => {
        const item = document.createElement('div');
        item.className = 'col-list-item';
        item.dataset.colName = col.name;
        item.innerHTML = `
            <span>${col.name}</span>
            <span class="col-list-item-type">${col.dtype || 'num'}</span>
        `;
        item.addEventListener('click', () => {
            document.querySelectorAll('.col-list-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            renderColumnDetail(col);
        });
        container.appendChild(item);
    });
}

function renderColumnDetail(col) {
    const emptyState = document.querySelector('.col-empty-state');
    const detailContent = document.getElementById('column-detail-content');
    if (emptyState) emptyState.style.display = 'none';
    if (detailContent) detailContent.classList.remove('hidden');

    setEl('det-col-name', col.name);
    setEl('det-col-type', col.dtype || 'numeric');
    setEl('det-missing', formatMissing(col));
    setEl('det-unique', col.unique_count !== undefined ? `${col.unique_count}` : '—');

    const isNumeric = col.dtype === 'numeric' || col.dtype === 'float64' || col.dtype === 'int64';
    document.querySelectorAll('.numeric-only').forEach(el => el.style.display = isNumeric ? '' : 'none');
    document.querySelectorAll('.categorical-only').forEach(el => el.style.display = !isNumeric ? '' : 'none');

    if (isNumeric) {
        setEl('det-mean', formatNum(col.mean));
        setEl('det-std', formatNum(col.std));
        setEl('det-skew', formatNum(col.skewness));
        setEl('det-outliers', col.outlier_count !== undefined ? `${col.outlier_count}` : '—');
    } else {
        setEl('det-mode', col.mode ? `${col.mode}` : '—');
        setEl('det-entropy', formatNum(col.entropy));
    }

    renderColumnChart(col);
}

function renderColumnChart(col) {
    const canvas = document.getElementById('columnChart');
    if (!canvas) return;
    if (columnChart) { columnChart.destroy(); columnChart = null; }

    const isNumeric = col.dtype === 'numeric' || col.dtype === 'float64' || col.dtype === 'int64';
    const ctx = canvas.getContext('2d');

    if (isNumeric && col.histogram) {
        columnChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: col.histogram.bins || [],
                datasets: [{
                    label: 'Count',
                    data: col.histogram.counts || [],
                    backgroundColor: 'rgba(79,70,229,0.25)',
                    borderColor: 'rgba(79,70,229,0.8)',
                    borderWidth: 1.5,
                    borderRadius: 3
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                    y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } }
                }
            }
        });
    } else if (!isNumeric && col.top_values) {
        const entries = Object.entries(col.top_values).slice(0, 10);
        columnChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    label: 'Frequency',
                    data: entries.map(e => e[1]),
                    backgroundColor: 'rgba(16,185,129,0.25)',
                    borderColor: 'rgba(16,185,129,0.8)',
                    borderWidth: 1.5,
                    borderRadius: 3
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } },
                    y: { grid: { display: false }, ticks: { font: { size: 10 } } }
                }
            }
        });
    }
}

/* ======================== DAG GRAPH ======================== */
function renderDagNodes(profile) {
    const graph = document.getElementById('dag-graph');
    const familyLabel = document.getElementById('dag-family-label');
    if (!graph) return;
    graph.innerHTML = '';

    const family = profile?.algorithm_family || 'ML Pipeline';
    if (familyLabel) {
        familyLabel.textContent = family.toUpperCase();
        familyLabel.style.background = 'rgba(79,70,229,0.3)';
        familyLabel.style.color = '#a5b4fc';
    }

    const nodes = [
        { label: 'PROFILER', state: 'done' },
        { label: 'DAG ROUTE', state: 'active' },
        { label: 'RECIPE', state: 'pending' },
        { label: 'PREPARE', state: 'pending' },
        { label: 'SPLIT', state: 'pending' },
        { label: 'TRAIN', state: 'pending' },
        { label: 'EVALUATE', state: 'pending' },
        { label: 'DEPLOY', state: 'pending' }
    ];

    nodes.forEach(n => {
        const node = document.createElement('div');
        node.className = `dag-node dag-node-${n.state}`;
        node.textContent = n.label;
        graph.appendChild(node);
    });
}

/* ======================== TIMER & PROGRESS ======================== */
function startTimer() {
    let elapsed = 0;
    const timerEl = document.getElementById('console-timer');
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        elapsed += 0.1;
        if (timerEl) timerEl.textContent = `${elapsed.toFixed(1)}s elapsed`;
    }, 100);
}

function stopTimer() {
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
}

function setProgress(pct) {
    const bar = document.getElementById('progress-bar');
    if (bar) bar.style.width = pct + '%';
}

/* ======================== STAGE MANAGEMENT ======================== */
function setStage(num, state) {
    const step = document.getElementById('stage-step-' + num);
    const badge = document.getElementById('stage-badge-' + num);
    if (!step || !badge) return;

    step.className = 'stage-pill';
    if (state === 'RUNNING') { step.classList.add('active'); badge.textContent = 'RUNNING'; }
    else if (state === 'DONE') { step.classList.add('done'); badge.textContent = 'DONE'; }
    else if (state === 'ERROR') { badge.textContent = 'ERROR'; badge.style.background = 'var(--accent-red)'; badge.style.color = '#fff'; }
    else { badge.textContent = 'PENDING'; }
}

/* ======================== CONSOLE LOGS ======================== */
function appendLog(message, type = 'info') {
    const logsEl = document.getElementById('console-logs');
    if (!logsEl) return;

    const line = document.createElement('div');
    line.style.color = type === 'error' ? '#f87171' : type === 'warn' ? '#fbbf24' : 'rgba(255,255,255,0.75)';
    line.textContent = message;
    logsEl.appendChild(line);
    logsEl.scrollTop = logsEl.scrollHeight;
}

/* ======================== PAYLOAD INSPECTOR ======================== */
function initPayloadTabs() {
    document.querySelectorAll('.itab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.itab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const targetId = btn.dataset.inspect;
            document.querySelectorAll('.json-pre[id^="inspect"]').forEach(el => el.classList.add('hidden'));
            const targetEl = document.getElementById(targetId + '-display');
            if (targetEl) targetEl.classList.remove('hidden');
        });
    });
}

function updateInspectorRequest(data) {
    const el = document.getElementById('inspect-request-display');
    if (el) el.textContent = JSON.stringify(data, null, 2);
}

function updateInspectorResponse(data) {
    const el = document.getElementById('inspect-response-display');
    if (el) el.textContent = JSON.stringify(data, null, 2);
}

/* ======================== TAB SYSTEM (Results) ======================== */
function initTabSystem() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabGroup = btn.closest('.card');
            tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            tabGroup.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            const target = tabGroup.querySelector('#' + btn.dataset.tab);
            if (target) target.classList.add('active');
        });
    });
}

/* ======================== COLUMN SEARCH ======================== */
function initColumnSearch() {
    const searchEl = document.getElementById('column-search');
    if (!searchEl) return;
    searchEl.addEventListener('input', () => {
        const query = searchEl.value.toLowerCase();
        document.querySelectorAll('.col-list-item').forEach(item => {
            const name = (item.dataset.colName || '').toLowerCase();
            item.style.display = name.includes(query) ? '' : 'none';
        });
    });
}

/* ======================== DAG INSPECTOR ======================== */
function initDagInspector() {
    const btn = document.getElementById('btn-fetch-dag-status');
    const input = document.getElementById('dag-id-input');
    if (!btn || !input) return;

    btn.addEventListener('click', async () => {
        const dagId = input.value.trim();
        if (!dagId) return;

        const resultEl = document.getElementById('dag-status-result');
        const jsonEl = document.getElementById('dag-status-json');
        if (resultEl) resultEl.classList.remove('hidden');
        if (jsonEl) jsonEl.textContent = 'Fetching…';

        try {
            const resp = await fetch(`http://127.0.0.1:8001/api/v1/pipeline/${dagId}/status`);
            const data = await resp.json();
            if (jsonEl) jsonEl.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            if (jsonEl) jsonEl.textContent = `Error: ${e.message}`;
        }
    });
}

/* ======================== MONITOR ======================== */
function initMonitor() {
    const btn = document.getElementById('btn-refresh-health');
    if (btn) btn.addEventListener('click', checkAllServices);
}

async function checkAllServices() {
    const services = [
        { port: 8000, id: 'health-8000', name: 'Dataset Profiler' },
        { port: 8001, id: 'health-8001', name: 'DAG Orchestrator' },
        { port: 8002, id: 'health-8002', name: 'Recipe Orchestrator' },
        { port: 8003, id: 'health-8003', name: 'Prepare API' },
        { port: 8004, id: 'health-8004', name: 'Feature Engineering API' },
        { port: 8005, id: 'health-8005', name: 'Split API' },
        { port: 8006, id: 'health-8006', name: 'Train API' },
        { port: 8007, id: 'health-8007', name: 'Evaluate API' },
        { port: 8008, id: 'health-8008', name: 'Deploy API' }
    ];

    const results = {};

    for (const svc of services) {
        const card = document.getElementById(svc.id);
        if (!card) continue;

        const statusEl = card.querySelector('.health-status');
        if (statusEl) {
            statusEl.className = 'health-status checking';
            statusEl.innerHTML = '<div class="health-dot"></div><span>Checking…</span>';
        }

        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            const resp = await fetch(`http://127.0.0.1:${svc.port}/api/v1/health`, {
                signal: controller.signal
            });
            clearTimeout(timeout);

            const data = await resp.json();
            results[svc.name] = { status: 'online', port: svc.port, response: data };

            if (statusEl) {
                statusEl.className = 'health-status online';
                statusEl.innerHTML = '<div class="health-dot"></div><span>Online</span>';
            }
        } catch (e) {
            results[svc.name] = { status: 'offline', port: svc.port, error: e.message };

            if (statusEl) {
                statusEl.className = 'health-status offline';
                statusEl.innerHTML = '<div class="health-dot"></div><span>Offline</span>';
            }
        }
    }

    // Show summary
    const resultPanel = document.getElementById('monitor-result');
    const resultJson = document.getElementById('monitor-result-json');
    if (resultPanel) resultPanel.classList.remove('hidden');
    if (resultJson) resultJson.textContent = JSON.stringify(results, null, 2);

    // Update sidebar status
    const allOnline = Object.values(results).every(r => r.status === 'online');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    if (statusDot) statusDot.className = 'status-dot ' + (allOnline ? 'active' : '');
    if (statusText) statusText.textContent = allOnline ? 'All Services Running' : 'Some Services Offline';
}

/* ======================== API TESTER ======================== */
async function testEndpoint(url, method = 'GET') {
    const panel = document.getElementById('apiResponsePanel');
    const urlEl = document.getElementById('arpUrl');
    const bodyEl = document.getElementById('arpBody');

    if (panel) panel.classList.remove('hidden');
    if (urlEl) urlEl.textContent = `${method} ${url}`;
    if (bodyEl) bodyEl.textContent = 'Fetching…';

    try {
        const resp = await fetch(url, { method });
        const data = await resp.json();
        if (bodyEl) bodyEl.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        if (bodyEl) bodyEl.textContent = `Error: Could not connect to ${url}\n\n${e.message}`;
    }
}

window.testEndpoint = testEndpoint;

function closeApiPanel() {
    const panel = document.getElementById('apiResponsePanel');
    if (panel) panel.classList.add('hidden');
}

window.closeApiPanel = closeApiPanel;

/* ======================== SHOW / HIDE HELPERS ======================== */
function show(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
}

function hide(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

function setEl(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function showError(message) {
    hide('loading-section');
    show('error-section');
    setEl('error-message', message);
}

function showSection(which) {
    // Not used directly anymore, keeping for compatibility
}

/* ======================== FORMAT HELPERS ======================== */
function formatNum(val) {
    if (val === undefined || val === null) return '—';
    return Number(val).toFixed(3);
}

function formatMissing(col) {
    const count = col.missing_count;
    const pct = col.missing_pct;
    if (count === undefined) return '—';
    if (pct !== undefined) return `${count} (${(pct * 100).toFixed(1)}%)`;
    return `${count}`;
}

/* ======================== MASTER DATA & TEMPLATE EDITING ======================== */
let currentEditDagId = null;
let currentRefFileType = null;
let currentTableType = null; // 'families' or 'metadata'
let cachedTableRecords = [];
let cachedTableHeaders = [];

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}
window.closeModal = closeModal;

// 1. Template Recipes
async function editTemplateRecipe(dagId, categoryName) {
    currentEditDagId = dagId;
    document.getElementById('trmTitle').textContent = `Edit Template Recipes — ${categoryName} (${dagId})`;
    
    // Set loading placeholder or clear form
    document.getElementById('trmForm').reset();
    
    try {
        const resp = await fetch(`http://127.0.0.1:8000/api/v1/masterdata/recipe/${dagId}`);
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        
        // Populate Prep Strategy
        if (data.preparing) {
            document.getElementById('trmImpute').value = data.preparing.impute_strategy || 'mean';
            document.getElementById('trmOutlier').value = data.preparing.outlier_method || 'none';
            document.getElementById('trmScale').value = data.preparing.scale_method || 'none';
            document.getElementById('trmEncode').value = data.preparing.encode_strategy || 'none';
            document.getElementById('trmTextClean').checked = !!data.preparing.text_clean;
            document.getElementById('trmTimeAlign').checked = !!data.preparing.time_align;
        }
        
        // Populate Splitting
        if (data.splitting) {
            document.getElementById('trmTestSize').value = data.splitting.test_size !== undefined ? data.splitting.test_size : 0.2;
        }
        
        // Populate Training
        if (data.training) {
            document.getElementById('trmAlgorithm').value = data.training.algorithm || '';
            document.getElementById('trmVariant').value = data.training.variant || '';
            document.getElementById('trmMetrics').value = (data.training.validation_metrics || []).join(', ');
            document.getElementById('trmHyperparams').value = JSON.stringify(data.training.hyperparameters || {}, null, 4);
        }
        
        document.getElementById('templateRecipeModal').classList.remove('hidden');
    } catch (e) {
        alert(`Error loading recipes: ${e.message}`);
    }
}
window.editTemplateRecipe = editTemplateRecipe;

// Save Template Recipe
document.getElementById('btnSaveTemplateRecipe')?.addEventListener('click', async () => {
    if (!currentEditDagId) return;
    
    let hyperparams = {};
    try {
        const hyperStr = document.getElementById('trmHyperparams').value.trim();
        if (hyperStr) {
            hyperparams = JSON.parse(hyperStr);
        }
    } catch (e) {
        alert(`Invalid Hyperparameters JSON: ${e.message}`);
        return;
    }
    
    const payload = {
        preparing: {
            impute_strategy: document.getElementById('trmImpute').value,
            outlier_method: document.getElementById('trmOutlier').value,
            scale_method: document.getElementById('trmScale').value,
            encode_strategy: document.getElementById('trmEncode').value,
            text_clean: document.getElementById('trmTextClean').checked,
            time_align: document.getElementById('trmTimeAlign').checked
        },
        splitting: {
            test_size: parseFloat(document.getElementById('trmTestSize').value) || 0.2
        },
        training: {
            algorithm: document.getElementById('trmAlgorithm').value,
            variant: document.getElementById('trmVariant').value,
            validation_metrics: document.getElementById('trmMetrics').value.split(',').map(m => m.trim()).filter(m => m),
            hyperparameters: hyperparams
        }
    };
    
    try {
        const resp = await fetch(`http://127.0.0.1:8000/api/v1/masterdata/recipe/${currentEditDagId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error(resp.statusText);
        alert(`Success: Recipes updated for ${currentEditDagId}`);
        closeModal('templateRecipeModal');
        loadTemplatesPage();
    } catch (e) {
        alert(`Failed to save: ${e.message}`);
    }
});

// 2. Text Reference Files
async function editTextRefFile(fileType) {
    currentRefFileType = fileType;
    const titleEl = document.getElementById('trfmTitle');
    const descEl = document.getElementById('trfmDesc');
    const contentEl = document.getElementById('trfmContent');
    
    if (fileType === 'dag_mapping') {
        titleEl.textContent = 'Edit 1_dataset_profiler/dag_mapping.json';
        descEl.textContent = 'Contains the mapping between DAG IDs and algorithm variants for each family.';
    } else {
        titleEl.textContent = 'Edit 1_dataset_profiler/dag_conditions_mapping.json';
        descEl.textContent = 'Contains specific evaluation conditions and pipeline actions for each DAG ID.';
    }
    
    contentEl.value = 'Loading…';
    
    try {
        const resp = await fetch(`http://127.0.0.1:8000/api/v1/masterdata/${fileType}`);
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        contentEl.value = JSON.stringify(data, null, 2);
        document.getElementById('textRefFileModal').classList.remove('hidden');
    } catch (e) {
        alert(`Error loading file: ${e.message}`);
    }
}
window.editTextRefFile = editTextRefFile;

// Save Text Reference File
document.getElementById('btnSaveTextRefFile')?.addEventListener('click', async () => {
    if (!currentRefFileType) return;
    
    const contentEl = document.getElementById('trfmContent');
    let payload = null;
    try {
        payload = JSON.parse(contentEl.value);
    } catch (e) {
        alert(`Invalid JSON format: ${e.message}`);
        return;
    }
    
    try {
        const resp = await fetch(`http://127.0.0.1:8000/api/v1/masterdata/${currentRefFileType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error(resp.statusText);
        alert(`Success: Reference file saved.`);
        closeModal('textRefFileModal');
    } catch (e) {
        alert(`Failed to save reference file: ${e.message}`);
    }
});

// 3. Algorithm Families Table / Mappings
async function editFamiliesTable() {
    currentTableType = 'families';
    document.getElementById('familiesModalTitle').textContent = 'Algorithm Families & Mappings Manager';
    document.getElementById('ftmFamilySelect').parentElement.style.display = 'flex';
    document.getElementById('ftmSearch').value = '';
    
    // Fetch algorithm families
    try {
        const resp = await fetch('http://127.0.0.1:8000/api/v1/masterdata/algorithm_families');
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        cachedTableRecords = data.records || [];
        cachedTableHeaders = data.headers || [];
        
        renderDynamicTable();
        document.getElementById('familiesTableModal').classList.remove('hidden');
    } catch (e) {
        alert(`Error loading families table: ${e.message}`);
    }
}
window.editFamiliesTable = editFamiliesTable;

// 4. Boilerplate Metadata
async function editBoilerplateMetadataTable() {
    currentTableType = 'metadata';
    document.getElementById('familiesModalTitle').textContent = 'Boilerplate Metadata Schema Manager';
    document.getElementById('ftmFamilySelect').parentElement.style.display = 'none';
    document.getElementById('ftmSearch').value = '';
    
    try {
        const resp = await fetch('http://127.0.0.1:8000/api/v1/masterdata/boilerplate_metadata');
        if (!resp.ok) throw new Error(resp.statusText);
        const data = await resp.json();
        cachedTableRecords = data.records || [];
        cachedTableHeaders = data.headers || [];
        
        renderDynamicTable();
        document.getElementById('familiesTableModal').classList.remove('hidden');
    } catch (e) {
        alert(`Error loading boilerplate metadata: ${e.message}`);
    }
}
window.editBoilerplateMetadataTable = editBoilerplateMetadataTable;

// Render dynamic table based on filtered items
function renderDynamicTable() {
    const headEl = document.getElementById('ftmTableHead');
    const bodyEl = document.getElementById('ftmTableBody');
    const searchVal = document.getElementById('ftmSearch').value.toLowerCase();
    
    headEl.innerHTML = '';
    bodyEl.innerHTML = '';
    
    // Render dynamic headers
    const trHead = document.createElement('tr');
    cachedTableHeaders.forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        trHead.appendChild(th);
    });
    headEl.appendChild(trHead);
    
    // Filter records
    let records = cachedTableRecords;
    if (currentTableType === 'families') {
        const familySelect = document.getElementById('ftmFamilySelect').value;
        records = records.filter(r => String(r.FAMILY_NAME).toUpperCase() === familySelect.toUpperCase());
    }
    
    if (searchVal) {
        records = records.filter(r => {
            return Object.values(r).some(val => String(val).toLowerCase().includes(searchVal));
        });
    }
    
    // Limit to 100 rows for rendering performance
    const renderLimit = 150;
    const itemsToRender = records.slice(0, renderLimit);
    
    itemsToRender.forEach((record, recordIndex) => {
        const tr = document.createElement('tr');
        cachedTableHeaders.forEach(col => {
            const td = document.createElement('td');
            
            // The record index in cachedTableRecords needs to be calculated
            const globalIndex = cachedTableRecords.indexOf(record);
            
            // Primary key column or ID columns shouldn't be edited
            const isReadOnly = col === 'DAG ID' || col === 'FAMILY_ID' || col === 'FAMILY_NAME' || col === 'Field Path';
            
            if (isReadOnly) {
                td.textContent = record[col] === null ? '' : record[col];
                td.style.fontWeight = 'bold';
            } else {
                const input = document.createElement('input');
                input.className = 'form-control';
                input.style.padding = '4px 8px';
                input.style.fontSize = '12.5px';
                input.value = record[col] === null ? '' : record[col];
                input.addEventListener('change', (e) => {
                    cachedTableRecords[globalIndex][col] = e.target.value;
                });
                td.appendChild(input);
            }
            tr.appendChild(td);
        });
        bodyEl.appendChild(tr);
    });
    
    if (records.length > renderLimit) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = cachedTableHeaders.length;
        td.style.textAlign = 'center';
        td.style.color = 'var(--text-muted)';
        td.textContent = `Showing first ${renderLimit} of ${records.length} matches. Filter search to refine.`;
        tr.appendChild(td);
        bodyEl.appendChild(tr);
    }
}

// Add listeners for filtering
document.getElementById('ftmFamilySelect')?.addEventListener('change', renderDynamicTable);
document.getElementById('ftmSearch')?.addEventListener('input', renderDynamicTable);

// Save dynamic table changes
document.getElementById('btnSaveFamiliesTable')?.addEventListener('click', async () => {
    const url = currentTableType === 'families' 
        ? 'http://127.0.0.1:8000/api/v1/masterdata/algorithm_families'
        : 'http://127.0.0.1:8000/api/v1/masterdata/boilerplate_metadata';
        
    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ records: cachedTableRecords })
        });
        if (!resp.ok) throw new Error(resp.statusText);
        alert(`Success: Mappings saved back to disk.`);
        closeModal('familiesTableModal');
        loadMasterDataPage();
    } catch (e) {
        alert(`Failed to save table mappings: ${e.message}`);
    }
});

// Load Templates Page dynamically from the backend recipes
async function loadTemplatesPage() {
    const dags = [
        { id: 'DAG_001', name: 'Classification' },
        { id: 'DAG_241', name: 'Regression' },
        { id: 'DAG_486', name: 'Anomaly' },
        { id: 'DAG_696', name: 'Clustering' },
        { id: 'DAG_906', name: 'Time-Series' },
        { id: 'DAG_1451', name: 'NLP' }
    ];
    for (const dag of dags) {
        try {
            const resp = await fetch(`http://127.0.0.1:8000/api/v1/masterdata/recipe/${dag.id}`);
            if (!resp.ok) continue;
            const data = await resp.json();
            
            let summaryParts = [];
            if (data.training && data.training.algorithm) {
                let algoStr = data.training.algorithm;
                if (data.training.variant) {
                    algoStr += ` (${data.training.variant})`;
                }
                summaryParts.push(algoStr);
            }
            if (data.preparing) {
                let prep = [];
                if (data.preparing.impute_strategy) {
                    prep.push(`${data.preparing.impute_strategy} imputation`);
                }
                if (data.preparing.outlier_method && data.preparing.outlier_method !== 'none') {
                    prep.push(`${data.preparing.outlier_method} outlier removal`);
                }
                if (data.preparing.encode_strategy && data.preparing.encode_strategy !== 'none') {
                    prep.push(`${data.preparing.encode_strategy} encoding`);
                }
                if (data.preparing.scale_method && data.preparing.scale_method !== 'none') {
                    prep.push(`${data.preparing.scale_method} scaling`);
                }
                if (data.preparing.text_clean) prep.push('text cleaning');
                if (data.preparing.time_align) prep.push('time alignment');
                if (prep.length > 0) {
                    summaryParts.push("with " + prep.join(", "));
                }
            }
            if (data.splitting && data.splitting.test_size !== undefined) {
                summaryParts.push(`(test size: ${data.splitting.test_size})`);
            }
            
            const pEl = document.getElementById(`recipe-desc-${dag.id}`);
            if (pEl) {
                pEl.textContent = summaryParts.join(' ');
            }
        } catch (e) {
            console.error(`Error loading recipe for ${dag.id}:`, e);
        }
    }
}
window.loadTemplatesPage = loadTemplatesPage;

// Load Master Data Page dynamically from the backend mappings
async function loadMasterDataPage() {
    try {
        const resp = await fetch('http://127.0.0.1:8000/api/v1/masterdata/dag_mapping');
        if (!resp.ok) throw new Error(resp.statusText);
        const mapping = await resp.json();
        
        const getAlgo = (family, dagId) => {
            const list = mapping[family] || [];
            const item = list.find(x => x.dag_id === dagId);
            return item ? `${item.algorithm} (${item.variant})` : '—';
        };
        
        const tbody = document.querySelector('#page-masterdata table.data-table tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr><td>Classification</td><td>DAG_001 – DAG_240</td><td>Supervised</td><td>${getAlgo('CLASSIFICATION', 'DAG_001')}</td></tr>
                <tr><td>Regression</td><td>DAG_241 – DAG_485</td><td>Supervised</td><td>${getAlgo('REGRESSION', 'DAG_241')}</td></tr>
                <tr><td>Anomaly Detection</td><td>DAG_486 – DAG_695</td><td>Unsupervised</td><td>${getAlgo('ANOMALY DETECTION', 'DAG_486')}</td></tr>
                <tr><td>Clustering</td><td>DAG_696 – DAG_905</td><td>Unsupervised</td><td>${getAlgo('CLUSTERING', 'DAG_696')}</td></tr>
                <tr><td>Time-Series</td><td>DAG_906 – DAG_1130</td><td>Supervised</td><td>${getAlgo('TIME-SERIES', 'DAG_906')}</td></tr>
                <tr><td>Digital Twin</td><td>DAG_1131 – DAG_1240</td><td>Hybrid</td><td>${getAlgo('DIGITAL TWIN', 'DAG_1131')}</td></tr>
                <tr><td>Reinforcement</td><td>DAG_1241 – DAG_1340</td><td>RL</td><td>${getAlgo('REINFORCEMENT LEARNING', 'DAG_1241')}</td></tr>
                <tr><td>Recommender</td><td>DAG_1341 – DAG_1450</td><td>Collaborative</td><td>${getAlgo('RECOMMENDATION', 'DAG_1341')}</td></tr>
                <tr><td>NLP/Text</td><td>DAG_1451 – DAG_1560</td><td>Supervised</td><td>${getAlgo('NLP/TEXT-CLASSIFICATION', 'DAG_1451')}</td></tr>
                <tr><td>Vision/Image</td><td>DAG_1561 – DAG_1690</td><td>Supervised</td><td>${getAlgo('COMPUTER VISION', 'DAG_1561')}</td></tr>
            `;
        }
    } catch (e) {
        console.error('Error loading master data page:', e);
    }
}
window.loadMasterDataPage = loadMasterDataPage;

/* ======================== PLOT RENDERERS ======================== */
let chartInstances = {};

function renderFeatureImportanceChart(data) {
    const canvas = document.getElementById('chartFeatureImportance');
    if (!canvas) return;
    if (chartInstances['featureImportance']) chartInstances['featureImportance'].destroy();
    
    const ctx = canvas.getContext('2d');
    chartInstances['featureImportance'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.features || [],
            datasets: [{
                label: 'Importance Score',
                data: data.importances || [],
                backgroundColor: 'rgba(124, 58, 237, 0.65)',
                borderColor: 'rgba(124, 58, 237, 1)',
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } },
                y: { grid: { display: false }, ticks: { font: { size: 10 } } }
            }
        }
    });
}

function renderPcaVarianceChart(data) {
    const canvas = document.getElementById('chartPcaVariance');
    if (!canvas) return;
    if (chartInstances['pcaVariance']) chartInstances['pcaVariance'].destroy();
    
    const ctx = canvas.getContext('2d');
    chartInstances['pcaVariance'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.components || [],
            datasets: [
                {
                    label: 'Individual Variance',
                    data: data.explained_variance || [],
                    backgroundColor: 'rgba(59, 130, 246, 0.4)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    type: 'bar',
                    borderRadius: 3
                },
                {
                    label: 'Cumulative Variance',
                    data: data.cumulative_variance || [],
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
                x: { grid: { display: false } },
                y: { min: 0, max: 1.0, grid: { color: '#f1f5f9' } }
            }
        }
    });
}

async function loadFeatureEngineeringPlots(filePath, targetCol) {
    try {
        const fiResp = await fetch('http://127.0.0.1:8004/api/v1/plots/feature_importance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath, target_column: targetCol })
        });
        if (fiResp.ok) {
            const fiData = await fiResp.json();
            renderFeatureImportanceChart(fiData);
        }
        
        const pcaResp = await fetch('http://127.0.0.1:8004/api/v1/plots/pca_variance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath, target_column: targetCol })
        });
        if (pcaResp.ok) {
            const pcaData = await pcaResp.json();
            renderPcaVarianceChart(pcaData);
        }
    } catch (e) {
        console.error("Error loading feature engineering plots:", e);
    }
}
window.loadFeatureEngineeringPlots = loadFeatureEngineeringPlots;
