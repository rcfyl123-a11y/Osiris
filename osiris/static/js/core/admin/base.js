// path: src/osiris/static/js/core/admin/base.js
// Назначение: поведение кастомной админки Osiris (сайдбар + мелочи).
// Темой управляет общий js/app.js.

document.addEventListener('DOMContentLoaded', function() {
    // Тосты: если общий app.js уже этим занимается, этот блок можно удалить.
    const toastElList = [].slice.call(document.querySelectorAll('.message-toast'));
    const toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl);
    });
    toastList.forEach(toast => toast.show());

    // Элементы для управления сайдбаром
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.admin-sidebar');
    const mainContent = document.querySelector('.admin-main');

    function applySidebarState(collapsed) {
        if (!sidebar || !mainContent) {
            return;
        }
        if (collapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        }
    }

    // Клик по кнопке "бургер"
    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                // Мобильное поведение: выезжающее меню
                sidebar.classList.toggle('mobile-open');
            } else {
                // Десктоп: складывание сайдбара
                const willCollapse = !sidebar.classList.contains('collapsed');
                applySidebarState(willCollapse);
                localStorage.setItem('sidebarCollapsed', String(willCollapse));
            }
        });

        // Восстановление состояния сайдбара на десктопе
        const stored = localStorage.getItem('sidebarCollapsed');
        if (stored !== null && window.innerWidth > 768) {
            applySidebarState(stored === 'true');
        }
    }

    // Обработка изменения размера окна
    window.addEventListener('resize', function() {
        if (!sidebar || !mainContent) {
            return;
        }

        if (window.innerWidth <= 768) {
            // На мобильных — всегда полноразмерный сайдбар, но скрыт по умолчанию
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        } else {
            // На десктопе восстанавливаем сохранённое состояние
            const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            applySidebarState(collapsed);
            // Убираем мобильный класс
            sidebar.classList.remove('mobile-open');
        }
    });
});
