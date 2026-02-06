import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, List, Optional, Sequence, Type, Protocol, Callable

# Исправлено: в User поле называется id, поэтому в Protocol тоже должно быть id
class HasID(Protocol):
    id: int

T = TypeVar('T', bound=HasID)

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

# --- Интерфейсы ---

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

class IUserRepository(IDataRepository[User], ABC):
    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]: pass

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

# --- Реализация ---

class DataRepository(IDataRepository[T]):
    def __init__(self, filepath: str, converter: Callable[[dict], T]):
        self._filepath = filepath
        self._converter = converter
        self._data: List[T] = []
        self._load_json()

    def _load_json(self):
        try:
            if not os.path.exists(self._filepath):
                self._data = []
                return
                
            with open(self._filepath, 'r', encoding="UTF-8") as f:
                raw_data = json.load(f)
                # TODO Сделано: конвертация сырых данных в объекты нужного типа
                self._data = [self._converter(item) for item in raw_data]
        except (json.JSONDecodeError, FileNotFoundError):
            self._data = []
        except Exception as e:
            print(f"[Error] Ошибка загрузки: {e}")
            self._data = []

    def _save_json(self):
        with open(self._filepath, 'w', encoding='utf-8') as f:
            # Превращаем объекты в словари для сохранения
            data_to_save = [asdict(item) for item in self._data]
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)

    def get_all(self) -> Sequence[T]:
        return self._data

    def get_by_id(self, item_id: int) -> Optional[T]:
        return next((item for item in self._data if item.id == item_id), None)

    def add(self, item: T) -> None:
        if self.get_by_id(item.id):
            self.update(item)
        else:
            self._data.append(item)
            self._save_json()

    def update(self, item: T) -> None:
        # TODO Сделано: обновление существующего элемента
        for i, existing_item in enumerate(self._data):
            if existing_item.id == item.id:
                self._data[i] = item
                self._save_json()
                return

    def delete(self, item: T) -> None:
        # TODO Сделано: удаление элемента
        initial_len = len(self._data)
        self._data = [i for i in self._data if i.id != item.id]
        if len(self._data) != initial_len:
            self._save_json()

class UserRepository(DataRepository[User], IUserRepository):
    def __init__(self, filepath: str = "users_db.json"):
        # TODO Сделано: лямбда для распаковки словаря в dataclass User
        super().__init__(
            filepath,
            lambda data: User(**data)
        )

    def get_by_login(self, login: str) -> Optional[User]:
        return next((u for u in self._data if u.login == login), None)

class AuthService(IAuthService):
    def __init__(self, user_repo: IUserRepository, session_filepath: str = "session.json"):
        self.user_repo = user_repo
        self.session_filepath = session_filepath
        self._current_user: Optional[User] = None
        self._try_auto_login()

    def _try_auto_login(self):
        if not os.path.exists(self.session_filepath):
            return

        try:
            with open(self.session_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_id = data.get("user_id")
                if user_id is not None:
                    user = self.user_repo.get_by_id(user_id)
                    if user is not None:
                        self._current_user = user
                        print(f"[System] Авторизация: восстановлен сеанс {user.name}")
        except Exception:
            print("[System] Не удалось восстановить сеанс")

    def sign_in(self, user: User) -> None:
        self._current_user = user
        with open(self.session_filepath, 'w', encoding='utf-8') as f:
            json.dump({"user_id": user.id}, f)
        print(f"[Auth] {user.login} вошел.")

    def sign_out(self) -> None:
        if self._current_user is None:
            return

        name = self._current_user.login
        self._current_user = None
        
        if os.path.exists(self.session_filepath):
            os.remove(self.session_filepath)
        print(f"[Auth] {name} вышел.")

    @property
    def is_authorized(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

# --- Main ---

def main():
    # Очистка файлов для теста
    for f in ["users_db.json", "session.json"]:
        if os.path.exists(f): os.remove(f)

    print("--- 1. Инициализация ---")
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
        updated_user = user_repo.get_by_id(1)
        print(f"Адрес в БД обновлен: {updated_user.address if updated_user else 'Error'}")

    print("\n--- 5. Проверка авто-входа ---")
    # Эмуляция нового запуска: создаем новые объекты, которые должны подтянуть данные из файлов
    new_repo = UserRepository("users_db.json")
    new_auth = AuthService(new_repo, "session.json")

    if new_auth.is_authorized:
        print(f"Авто-вход успешен для: {new_auth.current_user.name}")
    else:
        print("Авто-вход не сработал")

if __name__ == "__main__":
    main()
