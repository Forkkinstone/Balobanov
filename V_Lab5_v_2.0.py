import json #для работы с json файлами
import os #проверка существования файлов, удаление
from abc import ABC, abstractmethod #работа с абстрактными методами и классами
from dataclasses import dataclass, field, asdict #создание классов - хранилищ данных
from typing import TypeVar, Generic, List, Optional, Sequence, Type #типизация


# ---------------------------------------------------------
# 1. Класс User
# ---------------------------------------------------------

@dataclass
class User:
    id: int #поле - id, имя, логин
    name: str
    login: str
    password: str = field(repr=False) #безопасность логов, не показывает пароль
    email: Optional[str] = None #по дефолту стоит None, т.к. email может не быть
    address: Optional[str] = None

    def __lt__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.name < other.name


# ---------------------------------------------------------
# 2. Интерфейс репозитория (Generic)
# Остается без изменений
# ---------------------------------------------------------

T = TypeVar('T') #объявляем переменную типа T, это заглушка и потом может быть User, Product, Order


class IDataRepository(ABC, Generic[T]): #ABC - нельзя создавать экземпляры класса, Generic[T] - умеет работать с любыми типами T
    @abstractmethod
    def get_all(self) -> Sequence[T]: pass #вернуть список объектов типа T

    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[T]: pass #Найти один объект T по id

    @abstractmethod
    def add(self, item: T) -> None: pass #добавить объект T

    @abstractmethod
    def update(self, item: T) -> None: pass #обновить объект T

    @abstractmethod
    def delete(self, item: T) -> None: pass #удалить объект T


# ---------------------------------------------------------
# 3. Реализация Generic Репозитория на JSON
# ---------------------------------------------------------

class JsonDataRepository(IDataRepository[T]):
    """
    Реализация репозитория на основе JSON.
    Важно: требует передачи типа класса (model_type) в конструктор,
    чтобы знать, в какой объект превращать данные из JSON.
    """

    def __init__(self, filename: str, model_type: Type[T]): # filename: - имя файла, куда сохранять; model_type - т.к. json хранит просто текст/словари,
                                                            # нам нужно передать ссылку на класс, чтобы знать, в какой оъект сохранять прочитанные данные
        self.filename = filename
        self.model_type = model_type  # Сохраняем класс (например, User)
        self._data: List[T] = []
        self._load()

    def _load(self):
        if os.path.exists(self.filename): #если файл существует
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    # Загружаем список словарей
                    raw_data = json.load(f)
                    # Превращаем словари обратно в объекты класса T (User)
                    # Используем распаковку словаря (**item)
                    self._data = [self.model_type(**item) for item in raw_data] #берём каждый словарь item и "распаковываем" его в конструктор класса model_type
            except (json.JSONDecodeError, TypeError):
                self._data = []
        else:
            self._data = []

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            # Превращаем список объектов в список словарей с помощью asdict
            # JSON не умеет сохранять классы, только словари/списки
            data_to_save = [asdict(item) for item in self._data] #asdict(item) - превращает объект User обратно в словарь, чтобы json мог его понять
            json.dump(data_to_save, f, indent=4, ensure_ascii=False) #dump записывает данные в файл, indent делает красивый отступ, ensure_ascii = False кранирует неизвестные символы вне ascii

    def get_all(self) -> Sequence[T]: #отдаём список
        return self._data

    def get_by_id(self, item_id: int) -> Optional[T]: #получить id
        for item in self._data: #пробегаемся по словарю
            if hasattr(item, 'id') and getattr(item, 'id') == item_id: #если есть объект поля и он совпадает с пришедшим
                return item #возвращаем его
        return None

    def add(self, item: T) -> None:
        self._data.append(item)
        self._save()

    def update(self, item: T) -> None:
        target_id = getattr(item, 'id', None) #берём объект item и пытаемся достать его id
        if target_id is not None:
            for i, stored_item in enumerate(self._data):
                if getattr(stored_item, 'id') == target_id:
                    self._data[i] = item #меняем
                    self._save() #сохраняем
                    return

    def delete(self, item: T) -> None:
        target_id = getattr(item, 'id', None)
        if target_id is not None:
            self._data = [i for i in self._data if getattr(i, 'id') != target_id] #пересобираем список: оставляем только те элементы, у которых id НЕ совпадает с удаляемым
            self._save()


# ---------------------------------------------------------
# 2 (часть 2) & 4. User Repository
# ---------------------------------------------------------

class IUserRepository(IDataRepository[User], ABC):
    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]: pass


class UserRepository(JsonDataRepository[User], IUserRepository):
    def __init__(self, filename: str = "users_db.json"):
        # Передаем класс User в родительский конструктор
        super().__init__(filename, model_type=User)

    def get_by_login(self, login: str) -> Optional[User]:
        for user in self._data:
            if user.login == login:
                return user
        return None


# ---------------------------------------------------------
# 5. Интерфейс Auth Service (без изменений)
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# 6. Реализация Auth Service (с JSON сессией)
# ---------------------------------------------------------

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
                    user_id = data.get("user_id")  # Получаем ID из словаря
                    if user_id is not None:
                        user = self.user_repo.get_by_id(user_id)
                        if user:
                            print(f"[System] Авторизация: восстановлен сеанс {user.name}")
                            self._current_user = user
            except (json.JSONDecodeError, AttributeError):
                print("[System] Ошибка сессии.")

    def sign_in(self, user: User) -> None:
        self._current_user = user
        # Сохраняем не просто число, а красивый JSON-объект
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


# ---------------------------------------------------------
# 7. Демонстрация
# ---------------------------------------------------------

def main():
    # Чистим старые файлы JSON
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
    print("Пользователи сохранены в .json файл. Можешь открыть его и проверить!")

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
