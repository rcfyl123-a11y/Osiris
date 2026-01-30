// path: src/osiris/static/js/app.js
(function () {
    'use strict';

    /**
     * Константы для управления темами
     */
    const THEME_KEY = 'osiris_theme';
    const THEME_LABELS = {
        auto: 'Авто',
        light: 'Светлая',
        dark: 'Тёмная',
        contrast: 'Высокий контраст',
    };

    const root = document.documentElement;
    root.classList.add('js-enabled');

    /**
     * Применяет выбранную тему к документу
     * @param {string} mode - Режим темы: auto, light, dark, contrast
     */
    function applyTheme(mode) {
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        let effectiveTheme = mode;

        // Определяем актуальную тему для auto режима
        if (mode === 'auto') {
            effectiveTheme = prefersDark ? 'dark' : 'light';
        }

        root.setAttribute('data-bs-theme', effectiveTheme);

        // Обновляем label темы если есть
        const themeLabel = document.getElementById('theme-label');
        if (themeLabel) {
            themeLabel.textContent = THEME_LABELS[mode] || mode;
        }
    }

    /**
     * Инициализирует систему тем
     */
    function initTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY) || 'auto';
        applyTheme(savedTheme);

        // Слушаем изменения системной темы для auto режима
        const mediaQuery = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
        if (mediaQuery && mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', () => {
                const currentTheme = localStorage.getItem(THEME_KEY) || 'auto';
                if (currentTheme === 'auto') {
                    applyTheme('auto');
                }
            });
        }

        // Обработчики для кнопок выбора темы
        document.querySelectorAll('.theme-select').forEach(button => {
            button.addEventListener('click', () => {
                const themeMode = button.getAttribute('data-theme') || 'auto';
                localStorage.setItem(THEME_KEY, themeMode);
                applyTheme(themeMode);
            });
        });
    }

    /**
     * Инициализирует toast-уведомления
     */
    function initToasts() {
        const toastElements = document.querySelectorAll('.toast');

        toastElements.forEach(toastElement => {
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: 6000
            });
            toast.show();

            // Увеличиваем время показа при наведении
            toastElement.addEventListener('mouseenter', () => {
                toast._config.delay = 10000;
            });

            toastElement.addEventListener('mouseleave', () => {
                toast._config.delay = 6000;
            });
        });
    }

    /**
     * Включает Bootstrap tooltips
     */
    function enableTooltips() {
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(element => {
            new bootstrap.Tooltip(element);
        });
    }

    /**
     * Включает Bootstrap popovers
     */
    function enablePopovers() {
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(element => {
            new bootstrap.Popover(element);
        });
    }

    /**
     * Основная инициализация при загрузке DOM
     */
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        enableTooltips();
        enablePopovers();
        initToasts();

        // Плавное появление страницы
        setTimeout(() => {
            document.body.classList.add('loaded');
        }, 100);
    });

})();
