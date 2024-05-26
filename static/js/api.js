// api.js
const apiBaseUrl = '/api/v1'; // Базовый URL вашего API


// Функция для проверки авторизации
async function checkAuth() {
  return new Promise((resolve, reject) => {
    fetch('/api/v1/auth')
      .then(response => {
        if (!response.ok) {
          reject(new Error(`API Error: ${response.status} - ${response.statusText}`));
        }
        return response.json();
      })
      .then(data => {
        resolve(data.authenticated);
      })
      .catch(error => {
        reject(error);
      });
  });
}

// Функция для отправки запросов к API
async function fetchApi(endpoint, method = 'GET', body = null, headers = {}) {
  // Проверяем авторизацию перед выполнением запроса
  const isAuthenticated = await checkAuth();

  if (isAuthenticated) {
    // Пользователь авторизован - выполняем запрос
    headers['Authorization'] = `Bearer ${getAuthToken()}`; // Добавьте заголовок Authorization
    const response = await fetch(`${apiBaseUrl}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return await response.json();
  } else {
    // Пользователь не авторизован - перенаправляем на страницу входа
    window.location.href = '/login';
    return null;
  }
}


// Экспорт функций
export async function getUserInfo(userId) {
  try {
    const data = await fetchApi(`/users/${userId}`);
    return data;
  } catch (error) {
    console.error('Ошибка при получении информации о пользователе:', error);
    // Добавьте обработку ошибок здесь (например, отображение сообщения об ошибке)
  }
}

export async function addNewUser(name, email, password) {
  try {
    const data = await fetchApi('/users', 'POST', { name, email, password });
    return data;
  } catch (error) {
    console.error('Ошибка при добавлении пользователя:', error);
    // Добавьте обработку ошибок здесь
  }
}

// ... (Другие функции для работы с API)