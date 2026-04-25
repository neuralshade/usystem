const token = localStorage.getItem('token');
const role = localStorage.getItem('role');
const studentId = window.STUDENT_ID;
let chatWidget = null;
const associationTitle = document.getElementById('associationTitle');
const associationSubtitle = document.getElementById('associationSubtitle');
const studyManagementCard = document.getElementById('studyManagementCard');

if (!token || !['mentor', 'teacher'].includes(role)) {
    window.location.href = '/';
}

const removeStudentLinkButton = document.getElementById('removeStudentLinkButton');
const createMeetingButton = document.getElementById('createMeetingButton');
const createPlanButton = document.getElementById('createPlanButton');
const createTaskButton = document.getElementById('createTaskButton');
const createExamButton = document.getElementById('createExamButton');
const createSharedLinkButton = document.getElementById('createSharedLinkButton');
const uploadFileButton = document.getElementById('uploadFileButton');

removeStudentLinkButton.addEventListener('click', removeStudentLink);
createPlanButton.addEventListener('click', createPlan);
createTaskButton.addEventListener('click', createTask);
createExamButton.addEventListener('click', createExamResult);
createSharedLinkButton.addEventListener('click', createSharedLink);
uploadFileButton.addEventListener('click', uploadFile);

if (createMeetingButton) {
    createMeetingButton.addEventListener('click', createMeeting);
}

if (studyManagementCard) {
    studyManagementCard.classList.remove('is-hidden');
}

loadAssociationPage();

async function authFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });

    if (response.status === 401) {
        localStorage.clear();
        window.location.href = '/';
    }

    return response;
}

async function loadAssociationPage() {
    await Promise.all([
        loadStudentOverview(),
        loadPlans(),
        loadProgress(),
        loadExamResults(),
        loadClasses(),
        loadMeetings(),
        loadFiles(),
        loadSharedLinks(),
    ]);

    if (!chatWidget) {
        chatWidget = createChatWidget({
            authFetch,
            enabled: role === 'teacher',
            studentId,
            pollInterval: 3000,
            storageKey: `chat_widget_teacher_student_${studentId}`
        });
        await chatWidget.init();
    }
}

async function loadStudentOverview() {
    const res = await authFetch(`/api/student-overview/${studentId}`);
    const data = await res.json();
    if (!res.ok) {
        if (associationTitle) {
            associationTitle.innerText = 'Não foi possível abrir esta página';
        }
        associationSubtitle.innerText = data.error || 'Houve um problema ao buscar os dados deste aluno.';
        return;
    }

    const mentorLabel = data.mentor ? `${data.mentor.name} (${getRoleLabel(data.mentor.role)})` : 'Sem responsável definido';
    if (associationTitle) {
        associationTitle.innerText = data.student.name;
    }
    associationSubtitle.innerText = `${data.student.email} • Responsável atual: ${mentorLabel}`;
    populatePlanSelect(data.plans || []);
}

function populatePlanSelect(plans) {
    const select = document.getElementById('taskPlanId');
    if (!select) {
        return;
    }

    if (!plans.length) {
        select.innerHTML = '<option value="">Selecione um cronograma</option>';
        return;
    }

    select.innerHTML = ['<option value="">Selecione um cronograma</option>']
        .concat(plans.map((plan) => `<option value="${plan.id}">${plan.title}</option>`))
        .join('');
}

async function createPlan() {
    const payload = {
        student_id: studentId,
        title: document.getElementById('planTitle').value,
        duration_months: Number(document.getElementById('planDuration').value),
        notes: document.getElementById('planNotes').value
    };

    const res = await authFetch('/api/plans', { method: 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui salvar o cronograma agora.');
        return;
    }
    alert('Cronograma salvo com sucesso.');
    loadAssociationPage();
}

async function createTask() {
    const planId = document.getElementById('taskPlanId').value;
    if (!planId) {
        alert('Selecione um cronograma.');
        return;
    }

    const payload = {
        week_number: Number(document.getElementById('taskWeekNumber').value),
        subject: document.getElementById('taskSubject').value,
        description: document.getElementById('taskDescription').value,
        due_date: document.getElementById('taskDueDate').value
    };

    const res = await authFetch(`/api/plans/${planId}/tasks`, { method: 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui salvar essa meta agora.');
        return;
    }
    alert('Meta salva com sucesso.');
    loadAssociationPage();
}

async function createExamResult() {
    const payload = {
        student_id: studentId,
        exam_title: document.getElementById('examTitle').value,
        score: Number(document.getElementById('examScore').value),
        date: document.getElementById('examDate').value,
        exam_type: 'mock_exam',
        correct_answers: optionalNumber(document.getElementById('examCorrectAnswers').value),
        total_questions: optionalNumber(document.getElementById('examTotalQuestions').value)
    };

    const res = await authFetch('/api/exam-results', { method: 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui guardar esse resultado agora.');
        return;
    }
    alert('Resultado guardado com sucesso.');
    loadAssociationPage();
}

async function createMeeting() {
    if (!document.getElementById('eventTitle').value || !document.getElementById('eventDate').value) {
        alert('Preencha pelo menos o título e a data da reunião.');
        return;
    }

    const payload = {
        student_id: studentId,
        title: document.getElementById('eventTitle').value,
        description: document.getElementById('eventDescription').value,
        datetime: document.getElementById('eventDate').value,
        link: document.getElementById('eventLink').value
    };

    const res = await authFetch('/api/meetings', { method: 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui salvar esse encontro agora.');
        return;
    }
    alert('Encontro salvo com sucesso.');
    document.getElementById('eventTitle').value = '';
    document.getElementById('eventDescription').value = '';
    document.getElementById('eventDate').value = '';
    document.getElementById('eventLink').value = '';
    loadAssociationPage();
}

async function createSharedLink() {
    const payload = {
        student_id: studentId,
        title: document.getElementById('sharedLinkTitle').value,
        url: document.getElementById('sharedLinkUrl').value
    };

    const res = await authFetch('/api/student-links', { method: 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui guardar esse link agora.');
        return;
    }
    alert('Link guardado com sucesso.');
    document.getElementById('sharedLinkTitle').value = '';
    document.getElementById('sharedLinkUrl').value = '';
    loadSharedLinks();
}

async function removeStudentLink() {
    const confirmed = window.confirm('Se você remover este vínculo, o histórico desta relação será apagado. Deseja continuar?');
    if (!confirmed) {
        return;
    }

    const res = await authFetch(`/api/assign-mentor/${studentId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui remover esse vínculo agora.');
        return;
    }
    alert(data.message || 'Vínculo removido com sucesso.');
    window.location.href = '/dashboard';
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput || fileInput.files.length === 0) {
        alert('Selecione um arquivo.');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('student_id', String(studentId));

    const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
    });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui enviar esse material agora.');
        return;
    }
    alert('Material enviado com sucesso.');
    loadFiles();
}

async function loadClasses() {
    const res = await authFetch('/api/classes');
    const classes = await res.json();
    const html = classes
        .filter((item) => item.event_type === 'collective_class')
        .map((item) => `
            <div class="list-row">
                <strong>${item.title}</strong><br>
                <small>Professor: ${item.teacher_name || 'Não informado'}</small><br>
                ${item.description ? `<small>${item.description}</small><br>` : ''}
                <small>${formatDate(item.datetime)}</small><br>
                <a class="list-row-link" href="${item.link}" target="_blank" rel="noreferrer">Abrir aula</a>
            </div>
        `).join('');
    renderList('classList', html, 'Ainda não há aulas separadas para este momento.');
}

async function loadPlans() {
    const res = await authFetch(`/api/plans?student_id=${studentId}`);
    const plans = await res.json();
    const html = plans.map((plan) => `
        <div class="plan-row">
            <strong>${plan.title}</strong> <span class="tag">${plan.duration_months} meses</span><br>
            <small>Status: ${plan.status}</small><br>
            ${plan.notes ? `<small>${plan.notes}</small><br>` : ''}
            <div class="list-container">
                ${(plan.tasks || []).map((task) => `
                    <div class="list-row">
                        <strong>Semana ${task.week_number}</strong>${task.subject ? ` - ${task.subject}` : ''}<br>
                        <span>${task.description}</span><br>
                        <small>${task.due_date || 'Sem prazo'} • ${task.is_completed ? 'Concluída' : 'Pendente'}</small>
                        <br><button type="button" class="btn-secondary" onclick="toggleTask(${task.id})">Marcar andamento</button>
                    </div>
                `).join('') || '<p class="list-empty">Nenhuma meta foi adicionada a este cronograma ainda.</p>'}
            </div>
        </div>
    `).join('');
    renderList('planList', html, 'Ainda não há um cronograma montado para este aluno.');
}

async function loadProgress() {
    const res = await authFetch(`/api/progress?student_id=${studentId}`);
    const progress = await res.json();
    const html = `
        <div class="progress-row">
            <div class="progress-stat"><strong>Cronogramas em andamento:</strong> ${progress.plans_count}</div>
            <div class="progress-stat"><strong>Metas concluídas:</strong> ${progress.tasks_completed}/${progress.tasks_total}</div>
            <div class="progress-stat"><strong>Avanço geral:</strong> ${progress.task_completion_rate}%</div>
            <div class="progress-stat"><strong>Média em simulados:</strong> ${progress.average_score}</div>
        </div>
    `;
    renderList('progressSummary', html, 'Ainda não há progresso suficiente para mostrar aqui.');
}

async function loadExamResults() {
    const res = await authFetch(`/api/exam-results?student_id=${studentId}`);
    const exams = await res.json();
    const html = exams.map((item) => `
        <div class="list-row">
            <strong>${item.exam_title}</strong><br>
            <small>${item.date}</small><br>
            <span>Nota: ${item.score}</span>
        </div>
    `).join('');
    renderList('examList', html, 'Nenhum simulado foi registrado até aqui.');
}

async function loadMeetings() {
    const res = await authFetch(`/api/meetings?student_id=${studentId}`);
    const meetings = await res.json();
    const html = meetings.map((item) => `
        <div class="meeting-row">
            <div class="list-row-head">
                <div>
                    <strong>${item.title || item.description || 'Encontro'}</strong><br>
                    ${item.description ? `<small>${item.description}</small><br>` : ''}
                    <small>${formatDate(item.datetime)}</small>
                </div>
                <button type="button" class="btn-danger btn-inline" onclick="deleteMeeting(${item.id})">Excluir</button>
            </div>
            ${item.link ? `<a class="list-row-link" href="${item.link}" target="_blank" rel="noreferrer">Abrir link do encontro</a>` : '<small class="muted-text">O link deste encontro ainda não foi informado.</small>'}
        </div>
    `).join('');
    renderList('meetingList', html, 'Nenhum encontro foi marcado por enquanto.');
}

async function loadFiles() {
    const res = await authFetch(`/api/files?student_id=${studentId}`);
    const files = await res.json();
    const html = files.map((item) => `
        <div class="list-row file-row">
            <div>
                <strong>${item.filename}</strong><br>
                <small class="muted-text">Material disponível para este aluno.</small>
            </div>
            <a class="list-row-link" href="/api/files/download/${item.id}">Baixar</a>
        </div>
    `).join('');
    renderList('fileList', html, 'Nenhum material foi enviado ainda.');
}

async function loadSharedLinks() {
    const res = await authFetch(`/api/student-links?student_id=${studentId}`);
    const links = await res.json();
    const html = links.map((item) => `
        <div class="shared-link-row">
            <div class="list-row-head">
                <div>
                    <strong>${item.title}</strong><br>
                    <a class="list-row-link" href="${item.url}" target="_blank" rel="noreferrer">${item.url}</a>
                </div>
                <button type="button" class="btn-danger btn-inline" onclick="deleteSharedLink(${item.id})">Excluir</button>
            </div>
        </div>
    `).join('');
    renderList('sharedLinksList', html, 'Ainda não há links guardados para este aluno.');
}

async function deleteMeeting(meetingId) {
    const confirmed = window.confirm('Deseja excluir esta reunião individual?');
    if (!confirmed) {
        return;
    }

    const res = await authFetch(`/api/meetings/${meetingId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui excluir esse encontro agora.');
        return;
    }

    loadAssociationPage();
}

async function deleteSharedLink(linkId) {
    const confirmed = window.confirm('Deseja excluir este link compartilhado?');
    if (!confirmed) {
        return;
    }

    const res = await authFetch(`/api/student-links/${linkId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui excluir esse link agora.');
        return;
    }

    loadSharedLinks();
}

async function toggleTask(taskId) {
    const res = await authFetch(`/api/tasks/${taskId}/toggle`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
        alert(data.error || 'Não consegui atualizar o andamento desta meta.');
        return;
    }
    loadAssociationPage();
}

function renderList(elementId, html, emptyMessage) {
    const element = document.getElementById(elementId);
    if (!element) {
        return;
    }
    element.innerHTML = html || `<p class="list-empty">${emptyMessage}</p>`;
}

function optionalNumber(value) {
    if (value === '' || value == null) {
        return null;
    }
    return Number(value);
}

function getRoleLabel(currentRole) {
    if (currentRole === 'mentor') return 'Mentor';
    if (currentRole === 'teacher') return 'Professor';
    return 'Usuário';
}

function formatDate(value) {
    if (!value) return 'Data não informada';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}
