function createChatWidget(config) {
    const state = {
        threadId: null,
        lastMessageId: 0,
        pollHandle: null,
        initialized: false,
        isCollapsed: true,
        hasLoadedMessages: false,
    };

    const elements = {
        card: document.getElementById('chatCard'),
        launcher: document.getElementById('chatLauncher'),
        launcherBadge: document.getElementById('chatLauncherBadge'),
        panel: document.getElementById('chatPanel'),
        collapseButton: document.getElementById('chatCollapseButton'),
        status: document.getElementById('chatStatus'),
        unreadBadge: document.getElementById('chatUnreadBadge'),
        messages: document.getElementById('chatMessages'),
        composer: document.getElementById('chatComposer'),
        input: document.getElementById('chatMessageInput'),
        sendButton: document.getElementById('sendChatMessageButton'),
    };
    const storageKey = config.storageKey || 'chat_widget_state';

    function studentParam() {
        return config.studentId ? `?student_id=${config.studentId}` : '';
    }

    function requestStudentId() {
        return config.studentId ? { student_id: Number(config.studentId) } : {};
    }

    function toggleCard(shouldShow) {
        if (!elements.card) {
            return;
        }
        elements.card.classList.toggle('is-hidden', !shouldShow);
    }

    function hydrateCollapsedState() {
        try {
            const savedState = window.localStorage.getItem(storageKey);
            state.isCollapsed = savedState !== 'expanded';
        } catch {
            state.isCollapsed = true;
        }
    }

    function persistCollapsedState() {
        try {
            window.localStorage.setItem(storageKey, state.isCollapsed ? 'collapsed' : 'expanded');
        } catch {
            // no-op
        }
    }

    function applyDrawerState() {
        if (!elements.card || !elements.panel || !elements.launcher) {
            return;
        }

        elements.card.classList.toggle('is-collapsed', state.isCollapsed);
        elements.card.classList.toggle('is-expanded', !state.isCollapsed);
        elements.panel.setAttribute('aria-hidden', state.isCollapsed ? 'true' : 'false');
        elements.launcher.setAttribute('aria-expanded', state.isCollapsed ? 'false' : 'true');
    }

    async function openDrawer() {
        state.isCollapsed = false;
        persistCollapsedState();
        applyDrawerState();

        if (!state.hasLoadedMessages) {
            await loadMessages();
            state.hasLoadedMessages = true;
        }

        await markAsRead(true);
        if (elements.messages) {
            elements.messages.scrollTop = elements.messages.scrollHeight;
        }
        if (elements.input) {
            elements.input.focus();
        }
    }

    function closeDrawer() {
        state.isCollapsed = true;
        persistCollapsedState();
        applyDrawerState();
    }

    function setStatus(text) {
        if (elements.status) {
            elements.status.innerText = text;
        }
    }

    function setUnreadBadge(count) {
        if (!elements.unreadBadge || !elements.launcherBadge) {
            return;
        }

        if (!count) {
            elements.unreadBadge.classList.add('is-hidden');
            elements.unreadBadge.innerText = '0 novas';
            elements.launcherBadge.classList.add('is-hidden');
            elements.launcherBadge.innerText = '0';
            elements.launcher.classList.remove('has-unread');
            return;
        }

        elements.unreadBadge.classList.remove('is-hidden');
        elements.unreadBadge.innerText = `${count} nova${count > 1 ? 's' : ''}`;
        elements.launcherBadge.classList.remove('is-hidden');
        elements.launcherBadge.innerText = String(count);
        elements.launcher.classList.add('has-unread');
    }

    function renderEmptyMessage(message) {
        if (elements.messages) {
            elements.messages.innerHTML = `<p class="list-empty">${message}</p>`;
        }
    }

    function bubbleMeta(message) {
        const date = new Date(message.created_at);
        const formattedDate = Number.isNaN(date.getTime()) ? message.created_at : date.toLocaleString();
        return `${message.sender_name} • ${formattedDate}`;
    }

    function appendMessages(messages) {
        if (!elements.messages || !messages.length) {
            return;
        }

        const currentlyEmpty = elements.messages.querySelector('.list-empty');
        if (currentlyEmpty) {
            elements.messages.innerHTML = '';
        }

        const html = messages.map((message) => `
            <div class="chat-message ${message.is_mine ? 'is-mine' : ''}" data-message-id="${message.id}">
                <div class="chat-bubble">
                    <div class="chat-message-text">${escapeHtml(message.content)}</div>
                    <div class="chat-message-meta">${bubbleMeta(message)}</div>
                </div>
            </div>
        `).join('');

        elements.messages.insertAdjacentHTML('beforeend', html);
        state.lastMessageId = Math.max(state.lastMessageId, ...messages.map((message) => message.id));
        elements.messages.scrollTop = elements.messages.scrollHeight;
    }

    async function loadThread() {
        const res = await config.authFetch(`/api/chat/thread${studentParam()}`);
        if (res.status === 403 || res.status === 404) {
            toggleCard(false);
            stopPolling();
            return null;
        }

        const data = await res.json();
        if (!res.ok) {
            setStatus(data.error || 'Erro ao carregar o chat.');
            renderEmptyMessage(data.error || 'Não foi possível carregar a conversa.');
            return null;
        }

        state.threadId = data.thread.id;
        toggleCard(true);
        hydrateCollapsedState();
        applyDrawerState();
        setStatus(`Conversa com ${data.counterpart.name} (${getRoleLabelForChat(data.counterpart.role)})`);
        setUnreadBadge(data.unread_count);
        return data;
    }

    async function loadMessages({ afterId = null, silent = false } = {}) {
        const suffix = afterId ? `${studentParam() ? '&' : '?'}after_id=${afterId}` : '';
        const res = await config.authFetch(`/api/chat/messages${studentParam()}${suffix}`);
        const data = await res.json();
        if (!res.ok) {
            if (!silent) {
                renderEmptyMessage(data.error || 'Erro ao carregar mensagens.');
            }
            return [];
        }

        if (!afterId) {
            elements.messages.innerHTML = '';
            if (!data.messages.length) {
                renderEmptyMessage('Nenhuma mensagem ainda. Envie a primeira.');
            }
        }

        appendMessages(data.messages || []);
        setUnreadBadge(data.unread_count || 0);
        if (!state.isCollapsed && (data.messages || []).some((message) => !message.is_mine)) {
            await markAsRead(true);
        }
        return data.messages || [];
    }

    async function markAsRead(silent = false) {
        const res = await config.authFetch('/api/chat/read', {
            method: 'POST',
            body: JSON.stringify(requestStudentId())
        });
        const data = await res.json();
        if (!res.ok) {
            if (!silent) {
                window.alert(data.error || 'Erro ao marcar mensagens como lidas.');
            }
            return;
        }

        setUnreadBadge(0);
        elements.launcher.classList.remove('has-unread');
    }

    async function sendMessage() {
        const content = elements.input?.value.trim();
        if (!content) {
            return;
        }

        const res = await config.authFetch('/api/chat/messages', {
            method: 'POST',
            body: JSON.stringify({
                ...requestStudentId(),
                content
            })
        });
        const data = await res.json();
        if (!res.ok) {
            window.alert(data.error || 'Erro ao enviar mensagem.');
            return;
        }

        elements.input.value = '';
        appendMessages([data.chat_message]);
        if (!state.isCollapsed) {
            await markAsRead(true);
        }
    }

    async function pollNewMessages() {
        if (!state.threadId) {
            return;
        }

        await loadMessages({ afterId: state.lastMessageId, silent: true });
    }

    function startPolling() {
        stopPolling();
        state.pollHandle = window.setInterval(pollNewMessages, config.pollInterval || 3000);
    }

    function stopPolling() {
        if (state.pollHandle) {
            window.clearInterval(state.pollHandle);
            state.pollHandle = null;
        }
    }

    async function init() {
        if (!elements.card || !config.enabled || state.initialized) {
            toggleCard(false);
            return;
        }

        state.initialized = true;
        const thread = await loadThread();
        if (!thread) {
            return;
        }

        if (elements.sendButton) {
            elements.sendButton.addEventListener('click', sendMessage);
        }

        if (elements.launcher) {
            elements.launcher.addEventListener('click', async () => {
                if (state.isCollapsed) {
                    await openDrawer();
                    return;
                }
                closeDrawer();
            });
        }

        if (elements.collapseButton) {
            elements.collapseButton.addEventListener('click', closeDrawer);
        }

        if (elements.input) {
            elements.input.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            });
        }

        if (!state.isCollapsed) {
            await loadMessages();
            state.hasLoadedMessages = true;
            await markAsRead(true);
        } else {
            renderEmptyMessage('Abra o chat para visualizar as mensagens.');
        }
        startPolling();
        window.addEventListener('beforeunload', stopPolling);
    }

    return { init, stopPolling, openDrawer, closeDrawer };
}

function escapeHtml(value) {
    return value
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function getRoleLabelForChat(role) {
    if (role === 'teacher') return 'Professor';
    if (role === 'student') return 'Aluno';
    return 'Usuário';
}
