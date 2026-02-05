import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, List, Optional, Sequence, Type

@dataclass
class User:
    id: int
    name: str
    login: str
    password: str = field(repr=False)
    email: Optional[str] = None
    address: Optional[str] = None

    def __lt__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.name < other.name

T = TypeVar('T')

class IDataRepository(ABC, Generic[T]):
    @abstractmethod
    def get_all(self) -> Sequence[T]: pass

    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[T]: pass

    @abstractmethod
    def add(self, item: T) -> None: pass

    @abstractmethod
    def update(self, item: T) -> None: pass

    @abstractmethod
    def delete(self, item: T) -> None: pass

class JsonDataRepository(IDataRepository[T]):
    def __init__(self, filename: str, model_type: Type[T]):
        self.filename = filename
        self.model_type = model_type
        self._data: List[T] = []
        self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    self._data = [self.model_type(**item) for item in raw_data]
            except (json.JSONDecodeError, TypeError):
                self._data = []
        else:
            self._data = []

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            data_to_save = [asdict(item) for item in self._data]
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)

    def get_all(self) -> Sequence[T]:
        return self._data

    def get_by_id(self, item_id: int) -> Optional[T]:
        for item in self._data:
            if hasattr(item, 'id') and getattr(item, 'id') == item_id:
                return item
        return None

    def add(self, item: T) -> None:
        self._data.append(item)
        self._save()

    def update(self, item: T) -> None:
        target_id = getattr(item, 'id', None)
        if target_id is not None:
            for i, stored_item in enumerate(self._data):
                if getattr(stored_item, 'id') == target_id:
                    self._data[i] = item
                    self._save()
                    return

    def delete(self, item: T) -> None:
        target_id = getattr(item, 'id', None)
        if target_id is not None:
            self._data = [i for i in self._data if getattr(i, 'id') != target_id]
            self._save()

class IUserRepository(IDataRepository[User], ABC):
    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]: pass

class UserRepository(JsonDataRepository[User], IUserRepository):
    def __init__(self, filename: str = "users_db.json"):
        super().__init__(filename, model_type=User)

    def get_by_login(self, login: str) -> Optional[User]:
        for user in self._data:
            if user.login == login:
                return user
        return None

class IAuthService(ABC):
    @abstractmethod
    def sign_in(self, user: User) -> None: pass

    @abstractmethod
    def sign_out(self) -> None: pass

    @property
    @abstractmethod
    def is_authorized(self) -> bool: pass

    @property
    @abstractmethod
    def current_user(self) -> Optional[User]: pass

class AuthService(IAuthService):
    def __init__(self, user_repo: IUserRepository, session_file: str = "session.json"):
        self.user_repo = user_repo
        self.session_file = session_file
        self._current_user: Optional[User] = None
        self._try_auto_login()

    def _try_auto_login(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_id = data.get("user_id")
                    if user_id is not None:
                        user = self.user_repo.get_by_id(user_id)
                        if user:
                            print(f"[System] Авторизация: восстановлен сеанс {user.name}")
                            self._current_user = user
            except (json.JSONDecodeError, AttributeError):
                print("[System] Ошибка сессии.")

    def sign_in(self, user: User) -> None:
        self._current_user = user
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump({"user_id": user.id}, f)
        print(f"[Auth] {user.login} вошел.")

    def sign_out(self) -> None:
        if self._current_user:
            print(f"[Auth] {self._current_user.login} вышел.")
        self._current_user = None
        if os.path.exists(self.session_file):
            os.remove(self.session_file)

    @property
    def is_authorized(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

def main():
    if os.path.exists("users_db.json"): os.remove("users_db.json")
    if os.path.exists("session.json"): os.remove("session.json")

    print("--- 1. Инициализация (JSON Backend) ---")
    user_repo = UserRepository("users_db.json")
    auth_service = AuthService(user_repo, "session.json")

    print("\n--- 2. Добавление пользователей ---")
    u1 = User(id=1, name="Forkkinston", login="fork", password="123", email="fork@mail.com")
    u2 = User(id=2, name="Alex", login="alex", password="321", address="Moscow")

    user_repo.add(u1)
    user_repo.add(u2)

    print("\n--- 3. Авторизация ---")
    found = user_repo.get_by_login("fork")
    if found:
        auth_service.sign_in(found)

    print("\n--- 4. Обновление данных ---")
    current = auth_service.current_user
    if current:
        current.address = "New York"
        user_repo.update(current)
        print(f"Адрес обновлен: {user_repo.get_by_id(1).address}")

    print("\n--- 5. Проверка авто-входа (эмуляция перезапуска) ---")
    new_repo = UserRepository("users_db.json")
    new_auth = AuthService(new_repo, "session.json")

    if new_auth.is_authorized:
        print(f"Авто-вход успешен для: {new_auth.current_user.name}")
    else:
        print("Авто-вход не сработал")

if __name__ == "__main__":
    main()
