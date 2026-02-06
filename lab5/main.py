import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import TypeVar, Generic, List, Optional, Sequence, Type, Protocol 


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

class HasID(Protocol):
    user_id: int

T = TypeVar('T', bound=HasID)  # TODO make required field <id>


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


class DataRepository(IDataRepository[T]):
    def __init__(self, filepath: str, converter):  # TODO annotate converter
        self._filepath = filepath
        self._data: List[T] = []
        self._converter = None  # TODO annotate converter

    def _load_json(self):
        try:
            with open(self._filepath, 'r', encoding="UTF-8") as f:
                raw_data = json.load(f)
            # TODO convert raw_data to list[User] (use converter func)
        except FileNotFoundError:
            self._data = []
        except Exception:
            self._data = []

    def _save_json(self):
        with open(self._filepath, 'w', encoding='utf-8') as f:
            data_to_save = [asdict(item) for item in self._data]  # TODO make simple
            json.dump(data_to_save, f)

    def get_all(self) -> Sequence[T]:
        return self._data

    def get_by_id(self, item_id: int) -> Optional[T]:
        for item in self._data:
            if item.id == item_id:
                return item
        return None

    def add(self, item: T) -> None:
        self._data.append(item)
        self._save_json()

    def update(self, item: T) -> None:
        pass # TODO write this

    def delete(self, item: T) -> None:
        pass  # TODO write this


class UserRepository(DataRepository[User], IUserRepository):
    def __init__(self, filepath: str = "users_db.json"):
        super().__init__(
            filepath,
            lambda: ...  # TODO write converter lambda func
        )

    def get_by_login(self, login: str) -> Optional[User]:
        for user in self._data:
            if user.login == login:
                return user
        return None


class AuthService(IAuthService):
    def __init__(self, user_repo: IUserRepository, session_filepath: str = "session.json"):
        self.user_repo = user_repo
        self.session_filepath = session_filepath
        self._current_user: Optional[User] = None
        self._try_auto_login()

    def _try_auto_login(self):
        try:
            with open(self.session_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_id = data.get("user_id")
                if user_id is not None:
                    user = self.user_repo.get_by_id(user_id)
                    if user is not None:
                        self._current_user = user
                        print(f"[System] Авторизация: восстановлен сеанс {user.name}")
        except (json.JSONDecodeError, AttributeError):
            print("[System] Не удалось восстановить сеанс")

    def sign_in(self, user: User) -> None:
        self._current_user = user
        with open(self.session_filepath, 'w', encoding='utf-8') as f:
            json.dump({"user_id": user.id}, f)
        print(f"[Auth] {user.login} вошел.")

    def sign_out(self) -> None:
        if self.current_user is None:
            return

        user_id = self._current_user

        self._current_user = None
        print(f"[Auth] {user_id} вышел.")

        try:
            os.remove(self.session_filepath)
        except FileNotFoundError:
            pass
        except Exception:
            print(f"Не удалось удалить файл сессии для {user_id}")

    @property
    def is_authorized(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user


def main():
    if os.path.exists("users_db.json"):
        os.remove("users_db.json")

    if os.path.exists("session.json"):
        os.remove("session.json")

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
