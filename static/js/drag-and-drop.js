/**
 * Инициализация перетаскивания для контейнера
 */
function initDragAndDrop(containerId, onDropCallback = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    console.log(`Инициализация перетаскивания для ${containerId}`);
    
    let draggedItem = null;
    
    container.addEventListener('dragstart', function(e) {
        const item = e.target.closest('.draggable-item');
        if (item) {
            draggedItem = item;
            item.classList.add('dragging');
            e.dataTransfer.setData('text/plain', item.dataset.index);
        }
    });
    
    container.addEventListener('dragend', function() {
        if (draggedItem) {
            draggedItem.classList.remove('dragging');
            draggedItem = null;
        }
    });
    
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    
    container.addEventListener('drop', function(e) {
        e.preventDefault();
        
        const fromIndex = parseInt(e.dataTransfer.getData('text/plain'));
        const toElement = e.target.closest('.draggable-item');
        
        if (toElement && !isNaN(fromIndex) && draggedItem) {
            const toIndex = parseInt(toElement.dataset.index);
            
            if (fromIndex === toIndex) return;
            
            console.log(`Перетаскивание с ${fromIndex} на ${toIndex}`);
            
            const parent = container;
            const items = Array.from(parent.querySelectorAll('.draggable-item'));
            
            // Находим элементы по их текущим позициям
            const fromElement = items[fromIndex];
            const toElementNode = items[toIndex];
            
            if (fromElement && toElementNode) {
                // Меняем местами в DOM
                if (fromIndex < toIndex) {
                    parent.insertBefore(fromElement, toElementNode.nextSibling);
                } else {
                    parent.insertBefore(fromElement, toElementNode);
                }
                
                // Обновляем индексы
                updateItemIndices(containerId);
                
                // Вызываем callback
                if (onDropCallback && typeof onDropCallback === 'function') {
                    onDropCallback(fromIndex, toIndex);
                }
            }
        }
    });
}

/**
 * Обновление индексов элементов
 */
function updateItemIndices(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const items = container.querySelectorAll('.draggable-item');
    
    items.forEach((item, newIndex) => {
        item.dataset.index = newIndex;
        
        // Обновляем data-index на кнопках
        const buttons = item.querySelectorAll('button[data-index]');
        buttons.forEach(button => {
            button.dataset.index = newIndex;
        });
    });
}

/**
 * Инициализация кнопок поворота
 */
function initRotationButtons(containerId, onRotateCallback = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Ищем ВСЕ кнопки поворота в контейнере
    const rotateButtons = container.querySelectorAll('.rotate-btn, .image-remove-btn-horizontal');
    
    rotateButtons.forEach(button => {
        // Если это кнопка удаления, меняем на поворот
        if (button.classList.contains('image-remove-btn-horizontal') && button.textContent === '×') {
            button.textContent = '↻';
            button.title = 'Повернуть на 90°';
        }
        
        // Удаляем старые обработчики
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Добавляем новый обработчик
        newButton.addEventListener('click', function(e) {
            e.stopPropagation();
            const index = parseInt(this.dataset.index);
            
            if (onRotateCallback && typeof onRotateCallback === 'function') {
                onRotateCallback(index);
            } else {
                // Базовая логика поворота
                rotateImageBasic(this);
            }
        });
    });
}

/**
 * Базовая логика поворота
 */
function rotateImageBasic(button) {
    const index = parseInt(button.dataset.index);
    const container = button.closest('.draggable-item, .image-square-horizontal, .sequence-item');
    
    if (!container) return;
    
    const img = container.querySelector('img');
    const rotationElement = container.querySelector('.rotation-info, .image-rotation');
    
    if (img) {
        const currentRotation = parseInt(img.style.transform.replace('rotate(', '').replace('deg)', '')) || 0;
        const newRotation = (currentRotation + 90) % 360;
        img.style.transform = `rotate(${newRotation}deg)`;
        
        if (rotationElement) {
            rotationElement.textContent = `${newRotation}°`;
        }
        
        return newRotation;
    }
    
    return 0;
}

/**
 * Обновление индексов элементов
 */
function updateItemIndices(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const items = container.querySelectorAll('.draggable-item');
    
    items.forEach((item, newIndex) => {
        item.dataset.index = newIndex;
        
        // Обновляем data-index на кнопках
        const buttons = item.querySelectorAll('button[data-index]');
        buttons.forEach(button => {
            button.dataset.index = newIndex;
        });
    });
}