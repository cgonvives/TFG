document.addEventListener('DOMContentLoaded', () => {
    const needsList = document.getElementById('needsList');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');
    const solveBtn = document.getElementById('solveBtn');
    const selectionCount = document.getElementById('selectionCount');
    const resultsSection = document.getElementById('resultsSection');

    let allNeedsData = [];

    // Load needs on startup
    fetchNeeds();

    async function fetchNeeds() {
        try {
            const response = await fetch('/needs');
            if (!response.ok) throw new Error('Failed to fetch needs');

            const data = await response.json();
            // Convert dictionary to array for sorting/display
            allNeedsData = Object.entries(data).map(([id, info]) => ({
                id,
                ...info
            }));

            renderNeeds(allNeedsData);
        } catch (error) {
            needsList.innerHTML = `<div class="error-msg">Error cargando necesidades: ${error.message}</div>`;
            console.error(error);
        }
    }

    function renderNeeds(needs) {
        needsList.innerHTML = '';
        needs.forEach(need => {
            const card = document.createElement('div');
            card.className = 'need-item glass-panel'; // reusing glass-panel style partially? No, let's use the .need-item style defined
            card.className = 'need-item';

            const urgencyClass = `urg-${need.urgencia}`;
            const urgencyText = getUrgencyLabel(need.urgencia);
            const importanceClass = `imp-${need.importancia}`;

            card.innerHTML = `
                <input type="checkbox" class="need-checkbox" data-id="${need.id}">
                <div class="need-content">
                    <span class="need-code">${need.id}</span>
                    <p class="need-text">${need.necesidad}</p>
                    <div class="badges">
                        <span class="badge ${urgencyClass}">Urg: ${need.urgencia}</span>
                        <span class="badge ${importanceClass}">Imp: ${need.importancia}</span>
                    </div>
                </div>
            `;

            // Toggle checkbox when clicking the card (but not the checkbox itself to avoid double toggle)
            card.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox') {
                    const checkbox = card.querySelector('.need-checkbox');
                    checkbox.checked = !checkbox.checked;
                    // Trigger change event manually
                    checkbox.dispatchEvent(new Event('change'));
                }
            });

            const checkbox = card.querySelector('.need-checkbox');
            checkbox.addEventListener('change', () => {
                updateSelectionState(card, checkbox.checked);
            });

            needsList.appendChild(card);
        });
    }

    function getUrgencyLabel(val) {
        if (val >= 3) return 'Muy Urgente';
        if (val === 2) return 'Urgente';
        return 'Regular';
    }

    function updateSelectionState(card, isChecked) {
        if (isChecked) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
        updateCount();
    }

    function updateCount() {
        const checked = document.querySelectorAll('.need-checkbox:checked').length;
        selectionCount.textContent = `${checked} seleccionados`;
    }

    // Buttons
    selectAllBtn.addEventListener('click', () => {
        document.querySelectorAll('.need-checkbox').forEach(cb => {
            cb.checked = true;
            updateSelectionState(cb.closest('.need-item'), true);
        });
    });

    clearAllBtn.addEventListener('click', () => {
        document.querySelectorAll('.need-checkbox').forEach(cb => {
            cb.checked = false;
            updateSelectionState(cb.closest('.need-item'), false);
        });
    });

    solveBtn.addEventListener('click', async () => {
        const selectedIds = Array.from(document.querySelectorAll('.need-checkbox:checked'))
            .map(cb => cb.dataset.id);

        if (selectedIds.length === 0) {
            alert('Por favor selecciona al menos una necesidad.');
            return;
        }

        // UI Loading State
        solveBtn.disabled = true;
        const originalText = solveBtn.innerHTML;
        solveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Optimizando...';
        resultsSection.classList.add('hidden');

        try {
            const response = await fetch('/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ selected_needs: selectedIds })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Optimization failed');
            }

            const result = await response.json();
            renderResults(result);
        } catch (error) {
            alert('Error al ejecutar el optimizador: ' + error.message);
        } finally {
            solveBtn.disabled = false;
            solveBtn.innerHTML = originalText;
        }
    });

    function renderResults(data) {
        const { objective_value, actions, assignments } = data;

        document.getElementById('objectiveValue').textContent = objective_value.toFixed(2);

        const actionsList = document.getElementById('actionsList');
        actionsList.innerHTML = '';
        actions.forEach(action => {
            const el = document.createElement('div');
            el.className = 'action-card';
            el.innerHTML = `
                <h4>Acción Recomendada</h4>
                <p><strong>${action.id}</strong>: ${action.description}</p>
            `;
            actionsList.appendChild(el);
        });

        const assignmentsList = document.getElementById('assignmentsList');
        assignmentsList.innerHTML = '';
        assignments.forEach(assign => {
            const el = document.createElement('div');
            el.className = 'assignment-item';
            el.innerHTML = `
                <span>${assign.need_id}</span>
                <i class="fa-solid fa-arrow-right arrow-icon"></i>
                <span>${assign.action_id}</span>
            `;
            assignmentsList.appendChild(el);
        });

        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
});
