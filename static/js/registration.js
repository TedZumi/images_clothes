// registration.js - ТОЛЬКО загрузка изображений
let imageFilesMap = {};

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация кликов на квадраты
    for (let i = 1; i <= 4; i++) {
        const square = document.querySelector(`.image-square-horizontal[data-index="${i}"]`);
        const input = document.getElementById(`imageInput${i}`);
        
        square.addEventListener('click', function() {
            input.click();
        });
        
        input.addEventListener('change', function(e) {
            handleImageSelect(e, i);
        });
    }
    
    // Обработка удаления
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('image-remove-btn-horizontal')) {
            const index = parseInt(e.target.dataset.index);
            removeImage(index);
        }
    });
    
    // Обновление имен файлов при изменении email
    document.getElementById('email').addEventListener('input', updateImageNames);
    
    // ВАЖНО: Вызываем при загрузке страницы, чтобы инициализировать значения
    updateImageNames();
    
    console.log('registration.js инициализирован');
});

// Обработка выбора файла
function handleImageSelect(event, index) {
    const file = event.target.files[0];
    if (!file || !file.type.startsWith('image/')) {
        showNotification('Выберите изображение', 'error');
        event.target.value = '';
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        showNotification('Изображение должно быть меньше 5MB', 'error');
        event.target.value = '';
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.src = e.target.result;
        img.onload = function() {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = 150;
            canvas.height = 150;
            
            const size = Math.min(img.width, img.height);
            const sx = (img.width - size) / 2;
            const sy = (img.height - size) / 2;
            
            ctx.drawImage(img, sx, sy, size, size, 0, 0, 150, 150);
            
            canvas.toBlob(function(blob) {
                // Сохраняем файл
                const fileName = `image${index}.jpg`;
                const fileObj = new File([blob], fileName, { type: 'image/jpeg' });
                imageFilesMap[index] = fileObj;
                
                // Обновляем превью
                updatePreview(index, URL.createObjectURL(blob));
                
                // Обновляем валидацию
                validateImages();
                
                showNotification('Изображение добавлено', 'success');
            }, 'image/jpeg', 0.8);
        };
    };
    reader.readAsDataURL(file);
}

// Обновление превью
function updatePreview(index, imageUrl) {
    const preview = document.getElementById(`preview${index}`);
    const container = document.getElementById(`imageContainer${index}`);
    const removeBtn = container.parentNode.querySelector('.image-remove-btn-horizontal');
    const emptyState = container.querySelector('.empty-state-horizontal');
    
    if (preview) {
        preview.src = imageUrl;
        preview.style.display = 'block';
    }
    
    if (emptyState) emptyState.style.display = 'none';
    if (removeBtn) removeBtn.style.display = 'block';
}

// Удаление изображения
function removeImage(index) {
    const preview = document.getElementById(`preview${index}`);
    const container = document.getElementById(`imageContainer${index}`);
    const input = document.getElementById(`imageInput${index}`);
    const removeBtn = container.parentNode.querySelector('.image-remove-btn-horizontal');
    const emptyState = container.querySelector('.empty-state-horizontal');
    
    if (preview) {
        preview.src = '';
        preview.style.display = 'none';
    }
    
    if (input) input.value = '';
    delete imageFilesMap[index];
    
    if (emptyState) emptyState.style.display = 'flex';
    if (removeBtn) removeBtn.style.display = 'none';
    
    validateImages();
    showNotification('Изображение удалено', 'info');
}

// Валидация изображений
function validateImages() {
    const validation = document.getElementById('imagesValidation');
    const count = Object.keys(imageFilesMap).length;
    
    if (count === 4) {
        validation.textContent = 'Все изображения выбраны';
        validation.classList.add('valid');
        return true;
    } else {
        validation.textContent = `Выбрано ${count} из 4 изображений`;
        validation.classList.remove('valid');
        return false;
    }
}

// Обновление имен файлов
function updateImageNames() {
    console.log('Вызов updateImageNames()');
    
    const email = document.getElementById('email').value.trim();
    console.log('Текущий email:', email);
    
    let username = 'user';
    
    if (email) {
        const emailParts = email.split('@');
        if (emailParts[0]) {
            username = emailParts[0].replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
        }
    }
    
    const imageNames = [
        `${username}_img1.jpg`,
        `${username}_img2.jpg`,
        `${username}_img3.jpg`,
        `${username}_img4.jpg`
    ];
    
    const imageNamesInput = document.getElementById('imageNamesInput');
    
    if (imageNamesInput) {
        console.log('Найден элемент imageNamesInput');
        imageNamesInput.value = JSON.stringify(imageNames);
        console.log('Установлены имена файлов:', imageNames);
        console.log('Значение поля:', imageNamesInput.value);
    } else {
        console.error('Элемент imageNamesInput не найден! Проверьте HTML');
    }
}

// Показ уведомлений
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 8px;
        color: white;
        z-index: 1000;
        opacity: 0;
        transform: translateX(100px);
        transition: opacity 0.3s ease, transform 0.3s ease;
        background-color: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#2ecc71' : '#3498db'};
        border-left: 4px solid ${type === 'error' ? '#c0392b' : type === 'success' ? '#27ae60' : '#2980b9'};
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}