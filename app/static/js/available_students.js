const token = localStorage.getItem('token');
const role = localStorage.getItem('role');
const userId = localStorage.getItem('id');

if (!token || !['mentor', 'teacher'].includes(role)) {
    window.location.href = '/';
}

loadAvailableStudents();

async function loadAvailableStudents() {
    const res = await fetch('/api/student-options', {
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    if (res.status === 401) {
        localStorage.clear();
        window.location.href = '/';
        return;
    }

    const data = await res.json();
    if (!res.ok) {
        renderAvailableStudents([], data.error || 'Erro ao carregar alunos.');
        return;
    }

    renderAvailableStudents(data.assignable_students, null);
}

function renderAvailableStudents(students, errorMessage) {
    const container = document.getElementById('availableStudentsList');
    if (errorMessage) {
        container.innerHTML = `<p class="list-empty">${errorMessage}</p>`;
        return;
    }

    if (!students.length) {
        container.innerHTML = '<p class="list-empty">Nenhum aluno disponível para vínculo.</p>';
        return;
    }

    container.innerHTML = students.map((student) => `
        <div class="student-option-row">
            <div>
                <strong>${student.name}</strong><br>
                <small>${student.email}</small>
            </div>
            <button type="button" onclick="linkStudent(${student.id})">Vincular</button>
        </div>
    `).join('');
}

async function linkStudent(studentId) {
    const res = await fetch('/api/assign-mentor', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            student_id: studentId,
            mentor_id: Number(userId)
        })
    });

    const data = await res.json();
    if (res.ok) {
        alert('Aluno vinculado com sucesso!');
        window.location.href = '/dashboard';
        return;
    }

    alert(data.error || 'Erro ao vincular aluno.');
}
