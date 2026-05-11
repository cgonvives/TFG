/**
 * admin.js — Frontend logic for the AsFin Administration Panel.
 *
 * Handles:
 *   1. Data upload (drag & drop + file picker)
 *   2. ML pipeline execution & progress polling
 *   3. LLM provider selection & API key management
 */

document.addEventListener('DOMContentLoaded', () => {

    // ── DOM References ─────────────────────────────────────────────
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadResult = document.getElementById('uploadResult');
    const uploadFilename = document.getElementById('uploadFilename');
    const uploadDetails = document.getElementById('uploadDetails');
    const trainBtn = document.getElementById('trainBtn');
    const pipelineStatus = document.getElementById('pipelineStatus');
    const progressFill = document.getElementById('progressFill');
    const pipelineStep = document.getElementById('pipelineStep');
    const pipelinePercent = document.getElementById('pipelinePercent');
    const pipelineResult = document.getElementById('pipelineResult');

    const providerCards = document.querySelectorAll('.provider-card');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const toggleKeyVisibility = document.getElementById('toggleKeyVisibility');
    const apiKeyPreview = document.getElementById('apiKeyPreview');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const testLlmBtn = document.getElementById('testLlmBtn');
    const llmStatus = document.getElementById('llmStatus');
    const llmStatusIcon = document.getElementById('llmStatusIcon');
    const llmStatusText = document.getElementById('llmStatusText');

    let selectedProvider = 'gemini';
    let pollingInterval = null;

    // ── Initialization ─────────────────────────────────────────────
    loadDataInfo();
    loadSettings();

    // ════════════════════════════════════════════════════════════════
    //  DATA UPLOAD
    // ════════════════════════════════════════════════════════════════

    // Click to open file picker
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag & Drop events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) uploadFile(files[0]);
    });

    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
    });

    async function uploadFile(file) {
        if (!file.name.endsWith('.xlsx')) {
            showUploadError('Solo se aceptan archivos .xlsx');
            return;
        }

        // Show uploading state
        dropZone.classList.add('uploading');
        const dropText = dropZone.querySelector('.drop-text');
        const origText = dropText.textContent;
        dropText.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Subiendo archivo…';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload-data', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Error subiendo archivo');
            }

            // Show success
            uploadResult.classList.remove('hidden');
            uploadResult.className = 'upload-result success';
            uploadResult.querySelector('.upload-result-icon i').className = 'fa-solid fa-circle-check';
            uploadFilename.textContent = data.filename;
            uploadDetails.textContent = `${data.size_kb} KB · Hojas: ${data.sheets.join(', ')}`;

            // Refresh data info
            loadDataInfo();

        } catch (err) {
            showUploadError(err.message);
        } finally {
            dropZone.classList.remove('uploading');
            dropText.textContent = origText;
            dropText.innerHTML = 'Arrastra un archivo .xlsx aquí o <span class="drop-link">selecciona un archivo</span>';
        }
    }

    function showUploadError(msg) {
        uploadResult.classList.remove('hidden');
        uploadResult.className = 'upload-result error';
        uploadResult.querySelector('.upload-result-icon i').className = 'fa-solid fa-circle-xmark';
        uploadFilename.textContent = 'Error';
        uploadDetails.textContent = msg;
    }

    async function loadDataInfo() {
        try {
            const resp = await fetch('/api/data/info');
            const info = await resp.json();

            document.getElementById('currentFilename').textContent =
                info.original_filename || 'Datos iniciales';
            document.getElementById('lastUpload').textContent =
                info.last_upload_date ? formatDate(info.last_upload_date) : 'Nunca';
            document.getElementById('lastTraining').textContent =
                info.last_training_date ? formatDate(info.last_training_date) : 'Nunca';
            document.getElementById('dataStats').textContent =
                info.num_needs > 0
                    ? `${info.num_needs} necesidades · ${info.num_plans} planes`
                    : 'Sin datos';
        } catch (e) {
            console.error('Error loading data info:', e);
        }
    }

    // ════════════════════════════════════════════════════════════════
    //  ML PIPELINE
    // ════════════════════════════════════════════════════════════════

    trainBtn.addEventListener('click', async () => {
        trainBtn.disabled = true;
        pipelineStatus.classList.remove('hidden');
        pipelineResult.classList.add('hidden');
        progressFill.style.width = '0%';
        pipelineStep.textContent = 'Iniciando…';
        pipelinePercent.textContent = '0%';

        try {
            const resp = await fetch('/api/pipeline/run', { method: 'POST' });
            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.detail || 'Error iniciando pipeline');
            }

            // Start polling
            startPolling();

        } catch (err) {
            showPipelineResult('error', err.message);
            trainBtn.disabled = false;
        }
    });

    function startPolling() {
        pollingInterval = setInterval(async () => {
            try {
                const resp = await fetch('/api/pipeline/status');
                const status = await resp.json();

                const pct = Math.round(status.progress * 100);
                progressFill.style.width = pct + '%';
                pipelineStep.textContent = status.current_step;
                pipelinePercent.textContent = pct + '%';

                if (status.status === 'completed') {
                    stopPolling();
                    showPipelineResult('success', 'Modelos actualizados correctamente.');
                    trainBtn.disabled = false;
                    loadDataInfo();
                } else if (status.status === 'error') {
                    stopPolling();
                    showPipelineResult('error', status.error_message || 'Error desconocido');
                    trainBtn.disabled = false;
                }
            } catch (e) {
                console.error('Polling error:', e);
            }
        }, 2000);
    }

    function stopPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    function showPipelineResult(type, message) {
        pipelineResult.classList.remove('hidden');
        if (type === 'success') {
            pipelineResult.className = 'pipeline-result success';
            pipelineResult.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${message}`;
        } else {
            pipelineResult.className = 'pipeline-result error';
            pipelineResult.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${message}`;
        }
    }

    // ════════════════════════════════════════════════════════════════
    //  LLM CONFIGURATION
    // ════════════════════════════════════════════════════════════════

    // Provider card selection
    providerCards.forEach(card => {
        card.addEventListener('click', () => {
            providerCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            selectedProvider = card.dataset.provider;
        });
    });

    // Toggle API key visibility
    toggleKeyVisibility.addEventListener('click', () => {
        const isPassword = apiKeyInput.type === 'password';
        apiKeyInput.type = isPassword ? 'text' : 'password';
        toggleKeyVisibility.querySelector('i').className =
            isPassword ? 'fa-solid fa-eye-slash' : 'fa-solid fa-eye';
    });

    // Save settings
    saveSettingsBtn.addEventListener('click', async () => {
        saveSettingsBtn.disabled = true;
        const origHTML = saveSettingsBtn.innerHTML;
        saveSettingsBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Guardando…';

        try {
            const body = { llm_provider: selectedProvider };
            if (apiKeyInput.value.trim()) {
                body.api_key = apiKeyInput.value.trim();
            }

            const resp = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || 'Error guardando');
            }

            showLlmStatus('success', 'Configuración guardada correctamente.');
            apiKeyInput.value = '';  // Clear after save
            loadSettings();  // Refresh preview

        } catch (err) {
            showLlmStatus('error', err.message);
        } finally {
            saveSettingsBtn.disabled = false;
            saveSettingsBtn.innerHTML = origHTML;
        }
    });

    // Test LLM connection
    testLlmBtn.addEventListener('click', async () => {
        testLlmBtn.disabled = true;
        const origHTML = testLlmBtn.innerHTML;
        testLlmBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Probando…';

        try {
            const body = { provider: selectedProvider };
            if (apiKeyInput.value.trim()) {
                body.api_key = apiKeyInput.value.trim();
            }

            const resp = await fetch('/api/settings/test-llm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            const result = await resp.json();
            showLlmStatus(result.success ? 'success' : 'error', result.message);

        } catch (err) {
            showLlmStatus('error', 'Error de red: ' + err.message);
        } finally {
            testLlmBtn.disabled = false;
            testLlmBtn.innerHTML = origHTML;
        }
    });

    async function loadSettings() {
        try {
            const resp = await fetch('/api/settings');
            const settings = await resp.json();

            // Set active provider
            selectedProvider = settings.llm_provider || 'gemini';
            providerCards.forEach(card => {
                card.classList.toggle('active', card.dataset.provider === selectedProvider);
            });

            // Show key preview
            apiKeyPreview.textContent =
                settings.api_key_preview || 'No configurada';

        } catch (e) {
            console.error('Error loading settings:', e);
        }
    }

    function showLlmStatus(type, message) {
        llmStatus.classList.remove('hidden');
        llmStatus.className = 'llm-status ' + type;
        if (type === 'success') {
            llmStatusIcon.className = 'fa-solid fa-circle-check';
        } else {
            llmStatusIcon.className = 'fa-solid fa-circle-xmark';
        }
        llmStatusText.textContent = message;
    }

    // ── Helpers ─────────────────────────────────────────────────────
    function formatDate(isoString) {
        try {
            const d = new Date(isoString);
            return d.toLocaleDateString('es-ES', {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch {
            return isoString;
        }
    }
});
