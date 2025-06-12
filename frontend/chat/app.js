// app.js (HTTP Polling Version)
document.addEventListener('DOMContentLoaded', () => {

    // --- НАСТРОЙКИ ---
    const API_BASE_URL = 'http://localhost:8001'; // ИЗМЕНИТЕ, ЕСЛИ ВАШ БЭКЕНД НА ДРУГОМ АДРЕСЕ

    // --- Элементы DOM ---
    const loginScreen = document.getElementById('login-screen');
    const chatScreen = document.getElementById('chat-screen');
    const loginForm = document.getElementById('login-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginError = document.getElementById('login-error');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const messageList = document.getElementById('message-list');
    const logoutBtn = document.getElementById('logout-btn');
    const typingIndicator = document.getElementById('typing-indicator');

    // --- Состояние приложения ---
    let jwtToken = localStorage.getItem('jwtToken');
    let sessionId = null; // Будет устанавливаться после первого сообщения
    let isLoading = false; // Флаг для предотвращения отправки нескольких сообщений одновременно

    // --- Функции ---

    /**
     * Показывает нужный экран (логин или чат)
     */
    function showScreen(screenName) {
        loginScreen.classList.add('hidden');
        chatScreen.classList.add('hidden');
        
        if (screenName === 'login') {
            loginScreen.classList.remove('hidden');
        } else if (screenName === 'chat') {
            chatScreen.classList.remove('hidden');
        }
    }
    
    /**
     * Полностью перерисовывает историю чата на основе массива сообщений
     * @param {Array} messages - Массив объектов сообщений от сервера
     */
    function renderChatHistory(messages) {
        messageList.innerHTML = ''; // Очищаем старые сообщения
        messages.forEach(msg => {
            const messageElement = document.createElement('div');
            // В sender_type у вас 'user' или 'agent', что идеально подходит для имени класса
            messageElement.classList.add('message', `${msg.sender_type}-message`);
            
            // Форматируем текст, заменяя переносы строк и экранируя HTML
            const escapedText = msg.content.replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">");
            messageElement.innerHTML = escapedText.replace(/\n/g, '<br>');

            messageList.appendChild(messageElement);
        });
        messageList.scrollTop = messageList.scrollHeight; // Автопрокрутка вниз
    }

    /**
     * Показывает/скрывает индикатор "печатает..."
     * @param {boolean} show
     */
    function showTypingIndicator(show) {
        typingIndicator.classList.toggle('hidden', !show);
        if (show) {
             messageList.scrollTop = messageList.scrollHeight;
        }
    }

    /**
     * Функция выхода из системы
     */
    function logout() {
        jwtToken = null;
        sessionId = null;
        isLoading = false;
        localStorage.removeItem('jwtToken');
        messageList.innerHTML = ''; // Очищаем чат
        showScreen('login');
    }

    // --- Обработчики событий ---

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.textContent = '';
        const email = emailInput.value;
        const password = passwordInput.value;

        // 1. Создаем JSON-объект для отправки
        const loginData = {
            username: email,
            password: password
        };

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                // 2. Указываем правильный заголовок
                headers: { 
                    'Content-Type': 'application/json' 
                },
                // 3. Преобразуем объект в JSON-строку и отправляем в теле
                body: JSON.stringify(loginData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Неверные учетные данные');
            }

            const data = await response.json();
            jwtToken = data.access_token;
            localStorage.setItem('jwtToken', jwtToken);

            showScreen('chat');

        } catch (error) {
            loginError.textContent = error.message;
            console.error('Ошибка входа:', error);
        }
    });

    // Обработка отправки сообщения
    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (isLoading) return; // Не отправлять, если уже ждем ответ

        const messageText = messageInput.value.trim();
        if (!messageText) return;

        isLoading = true;
        showTypingIndicator(true);
        const originalMessage = messageInput.value;
        messageInput.value = ''; // Очищаем поле ввода сразу

        const payload = {
            content: messageText
        };
        // Если у нас уже есть ID сессии, добавляем его
        if (sessionId) {
            payload.session_id = sessionId;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${jwtToken}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                // Если токен истек или невалиден (401 Unauthorized)
                if (response.status === 401) {
                    alert('Ваша сессия истекла. Пожалуйста, войдите снова.');
                    logout();
                    return;
                }
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка отправки сообщения');
            }
            
            // Ответ сервера содержит всю историю чата
            const chatData = await response.json();

            // Обновляем ID сессии
            sessionId = chatData.session_id;

            // Перерисовываем весь чат
            renderChatHistory(chatData.messages);

        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);
            // Показываем ошибку в чате и возвращаем текст в поле ввода
            const errorElement = document.createElement('div');
            errorElement.className = 'message agent-message';
            errorElement.style.backgroundColor = '#d9534f';
            errorElement.style.color = 'white';
            errorElement.textContent = `Ошибка: ${error.message}`;
            messageList.appendChild(errorElement);
            messageList.scrollTop = messageList.scrollHeight;
            messageInput.value = originalMessage; // Возвращаем текст
        } finally {
            // В любом случае убираем индикатор и разрешаем отправку
            isLoading = false;
            showTypingIndicator(false);
        }
    });
    
    // Кнопка выхода
    logoutBtn.addEventListener('click', logout);

    // --- Инициализация ---
    if (jwtToken) {
        console.log('Найден токен, показываем экран чата.');
        showScreen('chat');
    } else {
        showScreen('login');
    }
});