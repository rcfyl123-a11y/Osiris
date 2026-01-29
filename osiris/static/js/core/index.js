// path: src/osiris/static/js/core/index.js
// Функциональность для главной страницы

(function() {
    'use strict';

    // Элементы DOM
    const healthStatusEl = document.getElementById('health-status');

    // Конфигурация
    const HEALTH_CHECK_URL = '/health/';
    const CHECK_INTERVAL = 30000; // 30 секунд

    /**
     * Проверка состояния здоровья системы
     */
    async function checkHealth() {
        try {
            updateHealthStatus('loading', 'Проверяем состояние системы...');

            const response = await fetch(HEALTH_CHECK_URL, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Предполагаем, что healthcheck возвращает {status: "ok", details: {...}}
            if (data.status === 'ok' || data.status === 'healthy') {
                updateHealthStatus('success', 'Система работает стабильно');

                // Показываем детали, если есть
                if (data.details) {
                    console.log('Health check details:', data.details);
                }
            } else {
                throw new Error(data.message || 'Неизвестная ошибка здоровья системы');
            }

        } catch (error) {
            console.error('Health check failed:', error);
            updateHealthStatus('error', `Ошибка: ${error.message}`);
        }
    }

    /**
     * Обновление отображения статуса здоровья
     */
    function updateHealthStatus(status, message) {
        if (!healthStatusEl) return;

        // Очищаем текущее состояние
        healthStatusEl.innerHTML = '';
        healthStatusEl.className = '';

        // Базовые классы
        healthStatusEl.classList.add('d-inline-flex', 'align-items-center', 'gap-2', 'px-3', 'py-2', 'rounded-3');

        let icon, statusClass;

        switch (status) {
            case 'success':
                statusClass = 'health-status-success';
                icon = `<svg width="16" height="16" fill="currentColor" class="flex-shrink-0">
                    <use href="#icon-check"/>
                </svg>`;
                break;
            case 'error':
                statusClass = 'health-status-error';
                icon = `<svg width="16" height="16" fill="currentColor" class="flex-shrink-0">
                    <use href="#icon-x"/>
                </svg>`;
                break;
            case 'loading':
            default:
                statusClass = 'health-status-loading';
                icon = `<div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>`;
                break;
        }

        healthStatusEl.classList.add(statusClass);
        healthStatusEl.innerHTML = `
            ${icon}
            <span class="small">${message}</span>
        `;
    }

    /**
     * Инициализация главной страницы
     */
    function initIndexPage() {
        console.log('Initializing Osiris index page...');

        // Первоначальная проверка здоровья
        checkHealth();

        // Периодическая проверка здоровья
        setInterval(checkHealth, CHECK_INTERVAL);

        // Обработчики для интерактивных элементов
        initEventListeners();
    }

    /**
     * Инициализация обработчиков событий
     */
    function initEventListeners() {
        // Пример: обработка кликов по карточкам возможностей
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('click', () => {
                card.classList.add('feature-card-active');
                setTimeout(() => {
                    card.classList.remove('feature-card-active');
                }, 200);
            });
        });

        // Ручная проверка здоровья по клику на статус
        if (healthStatusEl) {
            healthStatusEl.addEventListener('click', checkHealth);
            healthStatusEl.style.cursor = 'pointer';
            healthStatusEl.title = 'Нажмите для повторной проверки';
        }
    }

    // Инициализация при загрузке DOM
    document.addEventListener('DOMContentLoaded', initIndexPage);

    // Экспорт для глобального доступа (если нужно)
    window.OsirisIndex = {
        checkHealth,
        updateHealthStatus
    };


})();