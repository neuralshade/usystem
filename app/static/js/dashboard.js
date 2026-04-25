const token = localStorage.getItem('token');
const role = localStorage.getItem('role');
const name = localStorage.getItem('name');

if (!token) {
    window.location.href = '/';
}

const isEducator = role === 'mentor' || role === 'teacher';
const isStudent = role === 'student';

const userName = document.getElementById('userName');
const userRole = document.getElementById('userRole');
const educatorPanel = document.getElementById('educatorPanel');
const mentorCard = document.getElementById('mentorCard');
const chatCard = document.getElementById('chatCard');
const studyManagementCard = document.getElementById('studyManagementCard');
const progressCard = document.getElementById('progressCard');
const planCard = document.getElementById('planCard');
const examCard = document.getElementById('examCard');
const linksCard = document.getElementById('linksCard');
const classesCard = document.getElementById('classesCard');
const officeHoursCard = document.getElementById('officeHoursCard');
const officeHoursForm = document.getElementById('officeHoursForm');
const meetingsCard = document.getElementById('meetingsCard');
const filesCard = document.getElementById('filesCard');
const fileUploadControls = document.getElementById('fileUploadControls');
const createOfficeHoursButton = document.getElementById('createOfficeHoursButton');
let managedStudentsCache = [];
let teacherChatSummaryPoll = null;

document.getElementById('logoutButton').addEventListener('click', logout);
if (createOfficeHoursButton) {
    createOfficeHoursButton.addEventListener('click', createOfficeHours);
}

userName.innerText = name || 'Usuario';
userRole.innerText = getRoleLabel(role);

applyRoleVisibility();
loadDashboard();

function applyRoleVisibility() {
    toggleElement(educatorPanel, isEducator);
    toggleElement(mentorCard, isStudent);
    toggleElement(chatCard, isStudent);
    toggleElement(studyManagementCard, false);
    toggleElement(progressCard, isStudent);
    toggleElement(planCard, isStudent);
    toggleElement(examCard, isStudent);
    toggleElement(linksCard, isStudent);
    toggleElement(classesCard, isStudent);
    toggleElement(officeHoursCard, true);
    toggleElement(officeHoursForm, role === 'teacher');
    toggleElement(meetingsCard, isStudent);
    toggleElement(filesCard, isStudent);

    if (fileUploadControls) {
        fileUploadControls.classList.toggle('is-hidden', !isEducator);
    }
}

function toggleElement(element, shouldShow) {
    if (!element) {
        return;
    }
    element.classList.toggle('is-hidden', !shouldShow);
}

function getRoleLabel(currentRole) {
    if (currentRole === 'mentor') return 'Mentor';
    if (currentRole === 'teacher') return 'Professor';
    if (currentRole === 'student') return 'Aluno';
    return 'Usuario';
}

function logout() {
    localStorage.clear();
    window.location.href = '/';
}

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
        logout();
    }

    return response;
}

async function loadDashboard() {
    if (isEducator) {
        await loadManagedStudents();
        await loadOfficeHours();
        if (role === 'teacher' && !teacherChatSummaryPoll) {
            teacherChatSummaryPoll = window.setInterval(loadManagedStudents, 5000);
            window.addEventListener('beforeunload', () => {
                if (teacherChatSummaryPoll) {
                    window.clearInterval(teacherChatSummaryPoll);
                }
            });
        }
        return;
    }

    await Promise.all([
        loadMyMentor(),
        loadPlans(),
        loadProgress(),
        loadExamResults(),
        loadSharedLinks(),
        loadClasses(),
        loadOfficeHours(),
        loadMeetings(),
        loadFiles(),
    ]);

    const chatWidget = createChatWidget({
        authFetch,
        enabled: isStudent,
        pollInterval: 3000,
        storageKey: 'chat_widget_student_dashboard'
    });
    await chatWidget.init();
}

async function loadManagedStudents() {
    const [studentsRes, unreadRes] = await Promise.all([
        authFetch('/api/student-options'),
        role === 'teacher' ? authFetch('/api/chat/unread-summary') : Promise.resolve(null)
    ]);
    const data = await studentsRes.json();
    if (!studentsRes.ok) {
        renderList('managedStudentsTable', '', data.error || 'Erro ao carregar alunos.');
        return;
    }

    managedStudentsCache = data.managed_students || [];
    let unreadMap = {};
    if (unreadRes) {
        const unreadData = await unreadRes.json();
        unreadMap = Object.fromEntries(unreadData.map((item) => [item.student_id, item.unread_count]));
    }

    const students = managedStudentsCache;
    const html = students.map((student) => `
        <a class="student-link-row" href="/students/${student.id}">
            <div>
                <strong>${student.name}</strong>
                <br>
                <small>${student.email}</small>
            </div>
            <div>
                ${unreadMap[student.id] ? `<span class="chat-badge chat-badge-inline">${unreadMap[student.id]} nova${unreadMap[student.id] > 1 ? 's' : ''}</span>` : '<span class="tag">Sem novas mensagens</span>'}
            </div>
        </a>
    `).join('');

    renderList('managedStudentsTable', html, 'Nenhum aluno vinculado no momento.');
}

async function loadMyMentor() {
    const res = await authFetch('/api/my-mentor');
    if (res.status === 404) {
        renderList('mentorInfo', '', 'Nenhum mentor vinculado.');
        return;
    }

    const mentor = await res.json();
    const html = `
        <div class="mentor-row">
            <strong>${mentor.name}</strong><br>
            <small>${getRoleLabel(mentor.role)}</small>
            ${mentor.whatsapp ? `<br><small>WhatsApp: ${mentor.whatsapp}</small>` : ''}
        </div>
    `;
    renderList('mentorInfo', html, 'Nenhum mentor vinculado.');
}

async function loadPlans() {
    const res = await authFetch('/api/plans');
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
                        <small>${task.due_date || 'Sem prazo'} • ${task.is_completed ? 'Concluida' : 'Pendente'}</small>
                    </div>
                `).join('') || '<p class="list-empty">Nenhuma meta cadastrada.</p>'}
            </div>
        </div>
    `).join('');
    renderList('planList', html, 'Nenhum cronograma cadastrado.');
}

async function loadProgress() {
    const res = await authFetch('/api/progress');
    const progress = await res.json();
    const html = `
        <div class="progress-row">
            <div class="progress-stat"><strong>Cronogramas:</strong> ${progress.plans_count}</div>
            <div class="progress-stat"><strong>Metas concluidas:</strong> ${progress.tasks_completed}/${progress.tasks_total}</div>
            <div class="progress-stat"><strong>Conclusao:</strong> ${progress.task_completion_rate}%</div>
            <div class="progress-stat"><strong>Media em simulados:</strong> ${progress.average_score}</div>
        </div>
    `;
    renderList('progressSummary', html, 'Sem progresso registrado.');
}

async function loadExamResults() {
    const res = await authFetch('/api/exam-results');
    const exams = await res.json();
    const html = exams.map((item) => `
        <div class="list-row">
            <strong>${item.exam_title}</strong> <span class="tag">Simulado</span><br>
            <small>${item.date}</small><br>
            <span>Nota: ${item.score}</span>
        </div>
    `).join('');
    renderList('examList', html, 'Nenhum simulado registrado.');
}

async function loadSharedLinks() {
    const res = await authFetch('/api/student-links');
    const links = await res.json();
    const html = links.map((item) => `
        <div class="shared-link-row">
            <strong>${item.title}</strong><br>
            <a class="list-row-link" href="${item.url}" target="_blank" rel="noreferrer">${item.url}</a>
        </div>
    `).join('');
    renderList('sharedLinksList', html, 'Nenhum link compartilhado.');
}

async function loadClasses() {
    const res = await authFetch('/api/classes');
    const classes = await res.json();
    const html = classes
        .filter((item) => item.event_type === 'collective_class')
        .map((item) => `
            <div class="list-row">
                <strong>${item.title}</strong><br>
                ${item.description ? `<small>${item.description}</small><br>` : ''}
                <small>${formatDate(item.datetime)}</small><br>
                <a class="list-row-link" href="${item.link}" target="_blank" rel="noreferrer">Acessar Aula</a>
            </div>
        `).join('');
    renderList('classList', html, 'Nenhuma aula agendada.');
}

async function loadOfficeHours() {
    const res = await authFetch('/api/classes');
    const classes = await res.json();
    const html = classes
        .filter((item) => item.event_type === 'office_hours')
        .map((item) => `
            <div class="meeting-row">
                <div class="list-row-head">
                    <div>
                        <strong>${item.title}</strong><br>
                        <small>Professor: ${item.teacher_name || 'Não informado'}</small><br>
                        ${item.description ? `<small>${item.description}</small><br>` : ''}
                        <small>${formatDate(item.datetime)}</small>
                    </div>
                    ${role === 'teacher' && Number(item.teacher_id) === Number(localStorage.getItem('id')) ? `<button type="button" class="btn-danger btn-inline" onclick="deleteOfficeHours(${item.id})">Excluir</button>` : ''}
                </div>
                ${item.link ? `<a class="list-row-link" href="${item.link}" target="_blank" rel="noreferrer">Entrar no plantao</a>` : '<small class="muted-text">Link ainda não informado.</small>'}
            </div>
        `).join('');
    renderList('officeHoursList', html, 'Nenhum plantao agendado.');
}

async function createOfficeHours() {
    const title = document.getElementById('officeHoursTitle')?.value.trim();
    const description = document.getElementById('officeHoursDescription')?.value.trim();
    const datetime = document.getElementById('officeHoursDate')?.value;
    const link = document.getElementById('officeHoursLink')?.value.trim();

    if (!title || !datetime) {
        window.alert('Preencha pelo menos o titulo e a data do plantao.');
        return;
    }

    const res = await authFetch('/api/classes', {
        method: 'POST',
        body: JSON.stringify({
            title,
            description,
            datetime,
            link,
            event_type: 'office_hours'
        })
    });
    const data = await res.json();
    if (!res.ok) {
        window.alert(data.error || 'Erro ao criar plantao.');
        return;
    }

    document.getElementById('officeHoursTitle').value = '';
    document.getElementById('officeHoursDescription').value = '';
    document.getElementById('officeHoursDate').value = '';
    document.getElementById('officeHoursLink').value = '';
    loadOfficeHours();
}

async function deleteOfficeHours(id) {
    const confirmed = window.confirm('Deseja excluir este plantao tira-duvidas?');
    if (!confirmed) {
        return;
    }

    const res = await authFetch(`/api/classes/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
        window.alert(data.error || 'Erro ao excluir plantao.');
        return;
    }

    loadOfficeHours();
}

async function loadMeetings() {
    const res = await authFetch('/api/meetings');
    const meetings = await res.json();
    const html = meetings.map((item) => `
        <div class="meeting-row">
            <strong>${item.title || item.description || 'Reuniao'}</strong><br>
            ${item.description ? `<small>${item.description}</small><br>` : ''}
            <small>${formatDate(item.datetime)}</small><br>
            <a class="list-row-link" href="${item.link}" target="_blank" rel="noreferrer">Link da Reuniao</a>
        </div>
    `).join('');
    renderList('meetingList', html, 'Nenhuma reuniao marcada.');
}

async function loadFiles() {
    const res = await authFetch('/api/files');
    const files = await res.json();
    const html = files.map((item) => `
        <div class="list-row file-row">
            <div>
                <strong>${item.filename}</strong>
                <br>
                <small class="muted-text">Arquivo compartilhado na sua biblioteca.</small>
            </div>
            <a class="list-row-link" href="/api/files/download/${item.id}">Baixar</a>
        </div>
    `).join('');
    renderList('fileList', html, 'Nenhum arquivo disponivel.');
}

function renderList(elementId, html, emptyMessage) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.innerHTML = html || `<p class="list-empty">${emptyMessage}</p>`;
}

function formatDate(value) {
    if (!value) return 'Data nao informada';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}
