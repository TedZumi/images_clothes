// sequence.js - для регистрации
let sequenceOrder = [1, 2, 3, 4];
let sequenceRotations = [0, 0, 0, 0];
let sequenceInitialized = false;

// Проверить, все ли изображения загружены
function checkAllImagesLoaded() {
    let loadedCount = 0;
    
    for (let i = 1; i <= 4; i++) {
        const preview = document.getElementById(`preview${i}`);
        if (preview && preview.style.display !== 'none') {
            loadedCount++;
        }
    }
    
    if (loadedCount === 4) {
        document.getElementById('sequenceSection').style.display = 'block';
        
        // Инициализируем только ОДИН РАЗ
        if (!sequenceInitialized) {
            console.log('ПЕРВИЧНАЯ инициализация последовательности');
            loadImagesToSequence();
            initSequence();
            sequenceInitialized = true;
        }
    } else {
        document.getElementById('sequenceSection').style.display = 'none';
    }
}

// Загрузка изображений в последовательность - КОПИРУЕМ ИЗОБРАЖЕНИЯ
function loadImagesToSequence() {
    console.log('Загрузка изображений в последовательность');
    
    for (let i = 0; i < 4; i++) {
        const sourcePreview = document.getElementById(`preview${i + 1}`);
        const sequenceItem = document.querySelector(`#sequenceContainer [data-index="${i}"]`);
        
        if (sourcePreview && sequenceItem && sourcePreview.src) {
            const img = sequenceItem.querySelector('img');
            if (img) {
                // КОПИРУЕМ src из первого блока
                img.src = sourcePreview.src;
                img.alt = `Изображение ${i + 1}`;
                console.log(`Изображение ${i+1} скопировано, src:`, sourcePreview.src.substring(0, 50));
            }
            
            // Сохраняем номер изображения
            sequenceItem.dataset.imageNumber = sequenceOrder[i];
        }
    }
}

// Инициализация начального порядка из DOM
function initSequenceOrderFromDOM() {
    document.querySelectorAll('#sequenceContainer .image-square-horizontal').forEach((square, index) => {
        const imageNumber = parseInt(square.dataset.imageNumber) || (index + 1);
        sequenceOrder[index] = imageNumber;
    });
}

// Инициализация последовательности
function initSequence() {
    // Инициализируем порядок из DOM
    initSequenceOrderFromDOM();
    
    // Перетаскивание
    if (typeof initDragAndDrop === 'function') {
        initDragAndDrop('sequenceContainer', function(fromIndex, toIndex) {
            console.log(`Перетаскивание: ${fromIndex} -> ${toIndex}`);
            
            // Обновляем массивы
            const movedNumber = sequenceOrder[fromIndex];
            const movedRotation = sequenceRotations[fromIndex];
            
            sequenceOrder.splice(fromIndex, 1);
            sequenceRotations.splice(fromIndex, 1);
            
            sequenceOrder.splice(toIndex, 0, movedNumber);
            sequenceRotations.splice(toIndex, 0, movedRotation);
            
            console.log('Новый порядок:', sequenceOrder);
            
            // КРИТИЧНО ВАЖНО: Обновляем src изображений после перетаскивания
            updateImageSrcAfterDrag();
            updateSequenceHiddenFields();
        });
    }
    
    // Кнопки поворота
    if (typeof initRotationButtons === 'function') {
        initRotationButtons('sequenceContainer', function(index) {
            rotateSequenceImage(index);
        });
    } else {
        document.querySelectorAll('#sequenceContainer .image-remove-btn-horizontal').forEach(btn => {
            if (btn.textContent === '×') btn.textContent = '↻';
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                rotateSequenceImage(index);
            });
        });
    }
    
    updateSequenceHiddenFields();
}

// ОБНОВЛЯЕМ src изображений после перетаскивания
function updateImageSrcAfterDrag() {
    console.log('Обновление src изображений после перетаскивания');
    
    document.querySelectorAll('#sequenceContainer .image-square-horizontal').forEach((item, index) => {
        // Получаем номер изображения на этой позиции
        const imageNumber = sequenceOrder[index];
        
        // Находим исходное изображение с таким номером
        const sourcePreview = document.getElementById(`preview${imageNumber}`);
        
        if (sourcePreview && sourcePreview.src) {
            const img = item.querySelector('img');
            if (img) {
                // Устанавливаем правильный src
                img.src = sourcePreview.src;
                img.alt = `Изображение ${imageNumber}`;
                console.log(`Позиция ${index}: установлено изображение ${imageNumber}`);
            }
        }
        
        // Обновляем data-image-number
        item.dataset.imageNumber = imageNumber;
    });
}

// Поворот изображения
function rotateSequenceImage(index) {
    sequenceRotations[index] = (sequenceRotations[index] + 90) % 360;
    
    const element = document.querySelector(`#sequenceContainer [data-index="${index}"]`);
    
    if (element) {
        const img = element.querySelector('img');
        const rotationElement = element.querySelector('.image-rotation');
        
        if (img) img.style.transform = `rotate(${sequenceRotations[index]}deg)`;
        if (rotationElement) rotationElement.textContent = `${sequenceRotations[index]}°`;
    }
    
    updateSequenceHiddenFields();
}

// Обновление скрытых полей
function updateSequenceHiddenFields() {
    document.getElementById('imageOrderInput').value = JSON.stringify(sequenceOrder);
    document.getElementById('imageRotationsInput').value = JSON.stringify(sequenceRotations);
}

// Валидация
function validateSequence() {
    const sorted = [...sequenceOrder].sort();
    return JSON.stringify(sorted) === JSON.stringify([1, 2, 3, 4]);
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    console.log('sequence.js: DOM загружен');
    
    // Проверяем загрузку изображений
    setInterval(checkAllImagesLoaded, 1000);
    
    // Валидация при отправке
    document.getElementById('registrationForm').addEventListener('submit', function(e) {
        if (!validateSequence()) {
            e.preventDefault();
            alert('Установите правильную последовательность изображений');
        }
    });
});