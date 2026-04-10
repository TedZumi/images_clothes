# Простой тестовый скрипт
import psycopg2
import json

def test_old_code_works():
    # conn = psycopg2.connect("postgresql+psycopg2://postgres:PosRaf246@127.0.0.1/images_clothes")
    conn = psycopg2.connect("postgresql://postgres:PosRaf246@127.0.0.1:5432/images_clothes")
    cur = conn.cursor()
    
    # Пытаемся получить существующего пользователя
    cur.execute("SELECT person_id, name, email, password, wardrobe FROM person LIMIT 1")
    row = cur.fetchone()
    
    if row:
        print(f"Старый запрос работает. Найден пользователь: {row[1]}")
    else:
        print("Нет пользователей в БД")
    
    # Проверяем, что новые поля есть (но старый код их не запрашивает)
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'person' 
          AND column_name IN ('images', 'image_sequence')
    """)
    new_columns = cur.fetchall()
    print(f"Новые поля: {[col[0] for col in new_columns]}")
    
    cur.close()
    conn.close()


def test_two_factor_check():
    """Тестируем проверку двухфакторной аутентификации"""
    
    # Подключаемся к БД
    conn = psycopg2.connect("postgresql://postgres:PosRaf975@127.0.0.1:5432/images_clothes")
    cur = conn.cursor()
    
    # Проверяем тестового пользователя
    email = "test_2fa@example.com"
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM two_factor_auth tfa
            JOIN person p ON p.person_id = tfa.person_id
            WHERE p.email = %s
        )
    """, (email,))

    has_2fa = cur.fetchone()[0]
    print(f"Пользователь {email} имеет двухфакторку: {has_2fa}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    test_two_factor_check()