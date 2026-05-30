let sequenceOrder = [1, 2, 3, 4];
let sequenceRotations = [0, 0, 0, 0];

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initSequenceOrderFromPage();
    initGraphicAuth();
});

// Инициализация начального порядка
function initSequenceOrderFromPage() {
    document.querySelectorAll('.image-square-horizontal').forEach((square, index) => {
        const imageNumber = parseInt(square.dataset.imageNumber) || (index + 1);
        sequenceOrder[index] = imageNumber;
    });
}

// Инициализация графической аутентификации
function initGraphicAuth() {
    // Перетаскивание
    if (typeof initDragAndDrop === 'function') {
        initDragAndDrop('imagesGrid', function(fromIndex, toIndex) {
            // Обновляем массивы
            const movedNumber = sequenceOrder[fromIndex];
            const movedRotation = sequenceRotations[fromIndex];
            
            sequenceOrder.splice(fromIndex, 1);
            sequenceRotations.splice(fromIndex, 1);
            
            sequenceOrder.splice(toIndex, 0, movedNumber);
            sequenceRotations.splice(toIndex, 0, movedRotation);
            
            updateSequenceHiddenFields();
            updateGraphicPositions();
        });
    }
    
    // Кнопки поворота
    if (typeof initRotationButtons === 'function') {
        initRotationButtons('imagesGrid', function(index) {
            rotateImage(index);
        });
    } else {
        // Резервная инициализация
        document.querySelectorAll('.image-remove-btn-horizontal').forEach(btn => {
            if (btn.textContent === '×') btn.textContent = '↻';
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                rotateImage(index);
            });
        });
    }
    
    // Валидация при отправке
    document.getElementById('graphicAuthForm').addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showNotification('Проверьте последовательность', 'error');
        }
    });
    
    updateSequenceHiddenFields();
}

// Поворот изображения
function rotateImage(index) {
    sequenceRotations[index] = (sequenceRotations[index] + 90) % 360;
    
    const rotationElement = document.querySelector(`[data-index="${index}"] .image-rotation`);
    const img = document.querySelector(`[data-index="${index}"] img`);
    
    if (rotationElement) rotationElement.textContent = `${sequenceRotations[index]}°`;
    if (img) img.style.transform = `rotate(${sequenceRotations[index]}deg)`;
    
    updateSequenceHiddenFields();
}

// Обновление позиций
function updateGraphicPositions() {
    document.querySelectorAll('.image-square-horizontal').forEach((item, index) => {
        const positionElement = item.querySelector('.image-position');
        if (positionElement) {
            positionElement.textContent = `Позиция ${index + 1}`;
        }
    });
}

// Обновление скрытых полей
function updateSequenceHiddenFields() {
    document.getElementById('imageOrderInput').value = JSON.stringify(sequenceOrder);
    document.getElementById('imageRotationsInput').value = JSON.stringify(sequenceRotations);
}

// Валидация
function validateForm() {
    const sorted = [...sequenceOrder].sort();
    if (JSON.stringify(sorted) !== JSON.stringify([1, 2, 3, 4])) {
        return false;
    }
    
    for (let rotation of sequenceRotations) {
        if (![0, 90, 180, 270].includes(rotation)) {
            return false;
        }
    }
    
    return true;
}

// Показ уведомлений (можно использовать общую функцию)
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
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}