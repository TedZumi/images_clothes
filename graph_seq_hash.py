from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


pass_hash = PasswordHasher()

# Создание хеша
def hash_password(password: str) -> str:
    return pass_hash.hash(password)


# Проверка хеша
def verify_password(hashed: str, password: str) -> bool:
    try:
        pass_hash.verify(hashed, password)
        return True
    except VerifyMismatchError:
        return False
    

# Проверка обновления хеша
def needs_rehash(hashed: str) -> bool:
    return pass_hash.check_needs_rehash(hashed)