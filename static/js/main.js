
/**
 * main.js - Hlavní JavaScript soubor pro aplikaci kancelářské automatizace
 * 
 * Tento soubor obsahuje všechny JavaScriptové funkce potřebné
 * pro interaktivitu na front-endu aplikace.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Inicializace všech komponent
    initializeTasks();
    initializeDocuments();
    initializeUsers();
    setupTheme();

    // Globální zpracování zpětné vazby a upozornění
    setupFeedback();
});

/**
 * Inicializuje funkce související s úlohami
 */
function initializeTasks() {
    // Detekce, zda jsme na stránce s úlohami
    const tasksTable = document.getElementById('tasks-table-body');
    if (!tasksTable) return;

    // Proměnná pro uložení ID aktuálně zpracovávané úlohy
    let currentTaskId = null;

    // Modální okno pro potvrzení smazání
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteTaskModal'), {
        keyboard: false
    });

    // Tlačítka pro smazání úlohy
    const deleteButtons = document.querySelectorAll('.delete-task-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function () {
            const taskRow = this.closest('tr');
            currentTaskId = taskRow.dataset.taskId;
            deleteModal.show();
        });
    });

    // Potvrzení smazání úlohy
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function () {
            if (currentTaskId) {
                deleteTask(currentTaskId, deleteModal);
            }
        });
    }

    // Tlačítka pro spuštění úlohy
    const runButtons = document.querySelectorAll('.run-task-btn');
    runButtons.forEach(button => {
        button.addEventListener('click', function () {
            const taskRow = this.closest('tr');
            const taskId = taskRow.dataset.taskId;
            runTask(taskId, this);
        });
    });

    // Filtrování úloh
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', filterTasks);
    }
}

/**
 * Smaže úlohu podle ID
 * @param {string} taskId - ID úlohy ke smazání
 * @param {Object} modal - Instance modálního okna Bootstrap
 */
function deleteTask(taskId, modal) {
    fetch(`/tasks/${taskId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Odstranění řádku z tabulky
                const taskRow = document.querySelector(`tr[data-task-id="${taskId}"]`);
                if (taskRow) {
                    taskRow.remove();
                }

                // Kontrola, zda je tabulka prázdná
                const tableBody = document.getElementById('tasks-table-body');
                if (tableBody.children.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="9" class="text-center">Žádné úlohy nebyly nalezeny</td></tr>';
                }

                // Zobrazení zpětné vazby
                showFeedback('success', 'Úloha byla úspěšně smazána');
            } else {
                showFeedback('error', `Chyba: ${data.message}`);
            }

            // Zavření modálního okna
            if (modal) modal.hide();
        })
        .catch(error => {
            console.error('Chyba při mazání úlohy:', error);
            showFeedback('error', 'Došlo k chybě při mazání úlohy');
            if (modal) modal.hide();
        });
}

/**
 * Spustí úlohu podle ID
 * @param {string} taskId - ID úlohy ke spuštění
 * @param {HTMLElement} button - Tlačítko, které bylo stisknuto
 */
function runTask(taskId, button) {
    // Vizuální zpětná vazba - tlačítko se změní na spinner
    const originalButtonText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Spouštění...';
    button.disabled = true;

    // Odeslání požadavku na server
    fetch(`/tasks/${taskId}/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Aktualizace stavu úlohy v tabulce
            const taskRow = document.querySelector(`tr[data-task-id="${taskId}"]`);
            if (taskRow) {
                const statusCell = taskRow.querySelector('td:nth-child(5)');
                if (statusCell) {
                    if (data.task.status === 'completed') {
                        statusCell.innerHTML = '<span class="badge bg-success">Dokončeno</span>';
                        showFeedback('success', 'Úloha byla úspěšně dokončena');
                    } else if (data.task.status === 'failed') {
                        statusCell.innerHTML = '<span class="badge bg-danger">Chyba</span>';
                        showFeedback('error', `Chyba: ${data.task.error || 'Úloha selhala'}`);
                    } else {
                        statusCell.innerHTML = `<span class="badge bg-secondary">${data.task.status}</span>`;
                    }
                }

                // Odstranění tlačítka "Spustit"
                button.remove();
            }
        })
        .catch(error => {
            console.error('Chyba při spouštění úlohy:', error);
            showFeedback('error', 'Došlo k chybě při spouštění úlohy');

            // Vrácení tlačítka do původního stavu
            button.innerHTML = originalButtonText;
            button.disabled = false;
        });
}

/**
 * Filtruje úlohy podle vybraných kritérií
 */
function filterTasks() {
    // Získání hodnot filtrů
    const statusFilter = document.getElementById('status-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const priorityFilter = document.getElementById('priority-filter').value;

    // Sestavení URL pro filtrování
    let url = '/tasks/api/list?';
    if (statusFilter) url += `status=${statusFilter}&`;
    if (categoryFilter) url += `category=${categoryFilter}&`;
    if (priorityFilter) url += `priority=${priorityFilter}&`;

    // Odstranění posledního znaku '&', pokud existuje
    url = url.endsWith('&') ? url.slice(0, -1) : url;

    // Odeslání požadavku na server
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Aktualizace tabulky
                updateTasksTable(data.tasks);
            } else {
                showFeedback('error', `Chyba: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Chyba při filtrování úloh:', error);
            showFeedback('error', 'Došlo k chybě při filtrování úloh');
        });
}

/**
 * Aktualizuje tabulku úloh novými daty
 * @param {Array} tasks - Pole úloh
 */
function updateTasksTable(tasks) {
    const tableBody = document.getElementById('tasks-table-body');
    if (!tableBody) return;

    // Vyčištění tabulky
    tableBody.innerHTML = '';

    // Pokud nejsou žádné úlohy, zobrazíme informaci
    if (tasks.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center">Žádné úlohy nebyly nalezeny</td></tr>';
        return;
    }

    // Naplnění tabulky novými daty
    tasks.forEach(task => {
        // Formátování data
        const createdAt = new Date(task.created_at);
        const formattedCreatedAt = createdAt.toLocaleString('cs-CZ');

        let scheduledFor = '-';
        if (task.scheduled_for) {
            const scheduledDate = new Date(task.scheduled_for);
            scheduledFor = scheduledDate.toLocaleString('cs-CZ');
        }

        // Stav úlohy
        let statusHtml = '';
        if (task.status === 'pending') {
            statusHtml = '<span class="badge bg-warning">Čeká</span>';
        } else if (task.status === 'running') {
            statusHtml = '<span class="badge bg-info">Běží</span>';
        } else if (task.status === 'completed') {
            statusHtml = '<span class="badge bg-success">Dokončeno</span>';
        } else if (task.status === 'failed') {
            statusHtml = '<span class="badge bg-danger">Chyba</span>';
        } else {
            statusHtml = `<span class="badge bg-secondary">${task.status}</span>`;
        }

        // Priorita úlohy
        let priorityHtml = '';
        if (task.priority === 1) {
            priorityHtml = '<span class="text-success">Nízká</span>';
        } else if (task.priority === 2) {
            priorityHtml = '<span class="text-warning">Střední</span>';
        } else if (task.priority === 3) {
            priorityHtml = '<span class="text-danger">Vysoká</span>';
        }

        // Tlačítka akcí
        let actionsHtml = `
            <div class="btn-group">
                <a href="/tasks/${task.id}" class="btn btn-sm btn-primary">Detail</a>
        `;

        if (task.status === 'pending') {
            actionsHtml += `<button class="btn btn-sm btn-success run-task-btn">Spustit</button>`;
        }

        actionsHtml += `<button class="btn btn-sm btn-danger delete-task-btn">Smazat</button>
            </div>
        `;

        // Vytvoření řádku tabulky
        const row = document.createElement('tr');
        row.dataset.taskId = task.id;
        row.innerHTML = `
            <td>${task.id}</td>
            <td>${task.name}</td>
            <td>${task.category}</td>
            <td>${task.type}</td>
            <td>${statusHtml}</td>
            <td>${priorityHtml}</td>
            <td>${formattedCreatedAt}</td>
            <td>${scheduledFor}</td>
            <td>${actionsHtml}</td>
        `;

        tableBody.appendChild(row);
    });

    // Přidání event listenerů k novým tlačítkům
    const newDeleteButtons = tableBody.querySelectorAll('.delete-task-btn');
    newDeleteButtons.forEach(button => {
        button.addEventListener('click', function () {
            const taskRow = this.closest('tr');
            currentTaskId = taskRow.dataset.taskId;
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteTaskModal'));
            deleteModal.show();
        });
    });

    const newRunButtons = tableBody.querySelectorAll('.run-task-btn');
    newRunButtons.forEach(button => {
        button.addEventListener('click', function () {
            const taskRow = this.closest('tr');
            const taskId = taskRow.dataset.taskId;
            runTask(taskId, this);
        });
    });
}

/**
 * Inicializuje funkce související s dokumenty
 */
function initializeDocuments() {
    // Detekce, zda jsme na stránce s dokumenty
    const uploadForm = document.getElementById('document-upload-form');
    if (!uploadForm) return;

    // Zpracování nahrávání dokumentů
    uploadForm.addEventListener('submit', function (event) {
        // Validace formuláře
        const fileInput = document.getElementById('file-input');
        if (fileInput.files.length === 0) {
            event.preventDefault();
            showFeedback('error', 'Vyberte soubor k nahrání');
            return;
        }

        // Kontrola velikosti souboru
        const maxSize = 50 * 1024 * 1024; // 50 MB
        if (fileInput.files[0].size > maxSize) {
            event.preventDefault();
            showFeedback('error', 'Soubor je příliš velký. Maximální velikost je 50 MB.');
            return;
        }

        // Zobrazení indikátoru nahrávání
        document.getElementById('upload-progress').classList.remove('d-none');
    });

    // Tlačítka pro smazání dokumentu
    const deleteDocButtons = document.querySelectorAll('.delete-document-btn');
    deleteDocButtons.forEach(button => {
        button.addEventListener('click', function () {
            const documentId = this.dataset.documentId;
            if (confirm('Opravdu chcete smazat tento dokument?')) {
                deleteDocument(documentId);
            }
        });
    });
}

/**
 * Smaže dokument podle ID
 * @param {string} documentId - ID dokumentu ke smazání
 */
function deleteDocument(documentId) {
    fetch(`/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Odstranění řádku z tabulky
                const documentRow = document.querySelector(`tr[data-document-id="${documentId}"]`);
                if (documentRow) {
                    documentRow.remove();
                }

                // Kontrola, zda je tabulka prázdná
                const tableBody = document.getElementById('documents-table-body');
                if (tableBody && tableBody.children.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Žádné dokumenty nebyly nalezeny</td></tr>';
                }

                showFeedback('success', 'Dokument byl úspěšně smazán');
            } else {
                showFeedback('error', `Chyba: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Chyba při mazání dokumentu:', error);
            showFeedback('error', 'Došlo k chybě při mazání dokumentu');
        });
}

/**
 * Inicializuje funkce související s uživateli
 */
function initializeUsers() {
    // Implementace funkcí pro správu uživatelů by byla podobná předchozím funkcím
}

/**
 * Nastavení tématu aplikace (světlé/tmavé)
 */
function setupTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    // Zjištění aktuálního tématu
    const currentTheme = localStorage.getItem('theme') || 'light';

    // Nastavení tématu podle uloženého stavu
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
        themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
    } else {
        themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
    }

    // Přepínání tématu
    themeToggle.addEventListener('click', function () {
        document.body.classList.toggle('dark-theme');

        if (document.body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
            themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
        } else {
            localStorage.setItem('theme', 'light');
            themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
        }
    });
}

/**
 * Nastavení zobrazování zpětné vazby a upozornění
 */
function setupFeedback() {
    // Vytvoření elementu pro zpětnou vazbu, pokud neexistuje
    if (!document.getElementById('feedback-container')) {
        const feedbackContainer = document.createElement('div');
        feedbackContainer.id = 'feedback-container';
        feedbackContainer.className = 'position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(feedbackContainer);
    }
}

/**
 * Zobrazí zpětnou vazbu uživateli
 * @param {string} type - Typ zpětné vazby ('success', 'error', 'warning', 'info')
 * @param {string} message - Zpráva k zobrazení
 */
function showFeedback(type, message) {
    // Mapování typů na třídy Bootstrap
    const typeClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };

    // Vytvoření ID pro toast
    const toastId = 'toast-' + Date.now();

    // Vytvoření HTML pro toast
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${typeClass[type] || 'bg-primary'} text-white border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Zavřít"></button>
            </div>
        </div>
    `;

    // Přidání toastu do kontejneru
    const feedbackContainer = document.getElementById('feedback-container');
    feedbackContainer.innerHTML += toastHtml;

    // Inicializace a zobrazení toastu
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    toast.show();

    // Odstranění toastu po skrytí
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}