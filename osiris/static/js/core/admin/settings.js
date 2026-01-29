// Дополнительный JavaScript для страницы настроек
document.addEventListener('DOMContentLoaded', function() {
    // Подтверждение опасных действий
    const dangerousButtons = document.querySelectorAll('form[action*="clear_cache"], form[action*="send_test_email"]');

    dangerousButtons.forEach(form => {
        form.addEventListener('submit', function(e) {
            const action = this.querySelector('input[name="action"]').value;
            let message = '';

            if (action === 'clear_cache') {
                message = 'Вы уверены, что хотите очистить кэш?';
            } else if (action === 'send_test_email') {
                message = 'Отправить тестовое письмо?';
            }

            if (message && !confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Анимация кнопок при нажатии
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
});