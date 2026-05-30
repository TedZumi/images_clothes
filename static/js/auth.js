class DinamicTaskAuth {
    constructor() {
        this.passwordInput = document.getElementById('password');
        this.placeholder = document.getElementById('placeholder');
        this.emailInput = document.getElementById('email');
        
        this.init();
    }
    
    init() {
        // Инициализация для страницы с формулой
        if (this.passwordInput && this.placeholder) {
            this.taskInput();
        }
        
        // Инициализация для страницы ввода email
        if (this.emailInput) {
            this.emailInput();
        }
    }
    
    taskInput() {
        // Фокусировка на поле ввода
        this.passwordInput.focus();
        
        // Функция для обновления видимости плейсхолдера
        const updatePlaceholder = () => {
            if (this.passwordInput.value.trim() === '') {
                this.placeholder.classList.remove('hidden');
            } else {
                this.placeholder.classList.add('hidden');
            }
        };
        
        // Инициализация плейсхолдера
        updatePlaceholder();
        
        // События для поля ввода
        this.passwordInput.addEventListener('input', updatePlaceholder);
        this.passwordInput.addEventListener('change', updatePlaceholder);
        
        // Фокус по клику на плейсхолдер
        this.placeholder.addEventListener('click', () => {
            this.passwordInput.focus();
        });
        
        // Динамическая ширина поля ввода
        this.passwordInput.style.width = '420px';
        
        // Анимация при фокусе
        this.passwordInput.addEventListener('focus', () => {
            this.passwordInput.style.borderColor = '#FBB03B';
            this.passwordInput.style.boxShadow = '0 0 5px rgba(251, 176, 59, 0.3)';
        });
        
        this.passwordInput.addEventListener('blur', () => {
            this.passwordInput.style.boxShadow = 'none';
        });
    }
    
    emailInput() {
        // Валидация формы входа
        const form = document.querySelector('form.reg');
        if (form) {
            form.addEventListener('submit', (e) => {
                const email = this.emailInput.value.trim();
                if (!email) {
                    e.preventDefault();
                    this.sh_error('Введите email');
                    return false;
                }
                
                // Простая валидация email
                if (!this.val_em(email)) {
                    e.preventDefault();
                    this.sh_error('Введите корректный email');
                    return false;
                }
                
                return true;
            });
        }
        
        // Фокусировка на поле email
        this.emailInput.focus();
    }
    
    val_em(email) {
        // Простая проверка email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    sh_error(message) {
        // Показываем ошибку
        alert(message);
    }
    
    // Дополнительные методы при необходимости
    clearInput() {
        if (this.passwordInput) {
            this.passwordInput.value = '';
            this.placeholder.classList.remove('hidden');
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем, есть ли элементы аутентификации на странице
    const authForm = document.querySelector('form.reg');
    if (authForm) {
        new DinamicTaskAuth();
    }
    
    // Дополнительные обработчики событий
    initAnimations();
});

// Анимации и дополнительные эффекты
function initAnimations() {
    // Анимация кнопок
    const buttons = document.querySelectorAll('.button');
    buttons.forEach(button => {
        button.addEventListener('mousedown', () => {
            button.style.transform = 'translateY(2px)';
        });
        
        button.addEventListener('mouseup', () => {
            button.style.transform = 'translateY(0)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
        });
    });
    
    // Плавное появление элементов
    const fadeInElements = document.querySelectorAll('.formula-display, .user-info');
    fadeInElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(10px)';
        el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 100);
    });
}

// Утилиты для работы с DOM
const DOMUtils = {
    createElement(tag, className, text = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text) element.textContent = text;
        return element;
    },
    
    showNotification(message, type = 'info') {
        const notification = this.createElement('div', `notification notification-${type}`);
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Удаление через 3 секунды
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
};

// Экспорт для возможного использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FormulaAuth: DinamicTaskAuth, DOMUtils };
}