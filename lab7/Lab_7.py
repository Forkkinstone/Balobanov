import inspect
from enum import Enum
from abc import ABC, abstractmethod
from sys import implementation
from typing import Any, Type, Dict, List
from contextlib import contextmanager


class LifeStyle(Enum):
    PER_REQUEST = 1
    SCOPED = 2
    SINGLETON = 3


class Injector:
    def __init__(self):
        self._registry = {}
        self._singletons = {}
        self._scope_stack: List[Dict[Any, Any]] = []

    def register(self, interface_type: Type, implementation: Any, life_style: LifeStyle = LifeStyle.PER_REQUEST,
                 params: Dict[str, Any] = None):

        if params is None:
            params = {}

        self._registry[interface_type] = {
            'impl': implementation,
            'style': life_style,
            'params': params
        }

    @contextmanager
    def scope(self):
        scope_cache = {}
        self._scope_stack.append(scope_cache)
        try:
            yield
        finally:
            self._scope_stack.pop()

    def get_instance(self, interface_type: Type) -> Any:
        if interface_type not in self._registry:
            raise ValueError(f"Интерфейс {interface_type.__name__} не зарегестрирован")

        reg_info = self._registry[interface_type]
        style = reg_info['style']

        if style == LifeStyle.SINGLETON:
            if interface_type in self._singletons:
                return self._singletons[interface_type]

            instance = self._create_instance(interface_type)
            self._singletons[interface_type] = instance
            return instance

        elif style == LifeStyle.SCOPED:
            if not self._scope_stack:
                raise RuntimeError(
                    "Попытка получить ограниченную зависимость вне контекста (с помощью injector.scope(): ...)")

            current_scope = self._scope_stack[-1]
            if interface_type in current_scope:
                return current_scope[interface_type]

            instance = self._create_instance(interface_type)
            current_scope[interface_type] = instance
            return instance

        else:
            return self._create_instance(interface_type)

    def _create_instance(self, interface_type: Type) -> Any:
        reg_info = self._registry[interface_type]
        impl = reg_info['impl']
        fixed_params = reg_info['params']

        if inspect.isfunction(impl) or inspect.ismethod(impl):
            return impl(**fixed_params)

        if inspect.isclass(impl):
            sig = inspect.signature(impl.__init__)
            constructor_args = {}

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                if param_name in fixed_params:
                    constructor_args[param_name] = fixed_params[param_name]
                    continue

                if param.annotation in self._registry:
                    constructor_args[param_name] = self.get_instance(param.annotation)

            return impl(**constructor_args)

        raise TypeError(f"Неизвестный тип реализации для {interface_type}")

    def test_interface(self, interface_type):
        print(f"\n --- Проверяем интерфейс: {interface_type.__name__} ---")

        if interface_type not in self._registry:
            print("Статус: этот интерфейс ещё не зарегестрирован.")
            return

        info = self._registry[interface_type]
        implementation = info['impl']
        fixed_params = info['params']

        print("Статус: Успешно зарегестрирован!")

        try:
            impl_name = implementation.__name__
        except AttributeError:
            impl_name = str(implementation)

        print(f"Реализуется через: {impl_name}")

        if fixed_params:
            print(f"Переданные вручную параметры: {fixed_params}")
        else:
            print("Переданные вручную параметры: нет.")

        if inspect.isclass(implementation):
            print("Автоматические зависимости для создания:")
            init_args = inspect.signature(implementation.__init__).parameters
            found_deps = False

            for arg_name, arg_data in init_args.items():
                if arg_name != 'self' and arg_name not in fixed_params:
                    try:
                        dep_type = arg_data.annotation.__name__
                    except AttributeError:
                        dep_type = "Тип не указан."
                    print(f" -> Нужно найти: {arg_name} (тип: {dep_type}).")
                    found_deps = True

            if not found_deps:
                print("-> Дополнительных зависимостей не требуется.")
        else:
            print("-> Это функция-фабрика, скрытые зависимости не проверяем.")


class ILogger(ABC):
    @abstractmethod
    def log(self, message: str): pass


class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"[Console] {message}")


class FileLoggerStub(ILogger):
    def __init__(self, filename: str = "default.log"):
        self.filename = filename

    def log(self, message: str):
        print(f"[Файл: {self.filename}] {message}")


class IDatabase(ABC):
    @abstractmethod
    def connect(self): pass


class PostgresDB(IDatabase):
    def __init__(self, connection_string: str):
        self.conn_str = connection_string
        print(f"-> Init PostgresDB ({id(self)})")

    def connect(self):
        return f"Connected to PG: {self.conn_str}"


class InMemoryDB(IDatabase):
    def __init__(self):
        print(f"-> Init InMemoryDB ({id(self)})")

    def connect(self):
        return "Connected to Memory"


class IAppService(ABC):
    @abstractmethod
    def run(self): pass


class BackendService(IAppService):
    def __init__(self, logger: ILogger, db: IDatabase, app_name: str = "Unknown"):
        self.logger = logger
        self.db = db
        self.app_name = app_name

    def run(self):
        self.logger.log(f"Starting {self.app_name}...")
        self.logger.log(f"DB Status: {self.db.connect()}")


class TestService(IAppService):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def run(self):
        self.logger.log("Запуск ТЕСТОВОГО режима без реальной базы данных")


def create_special_logger():
    l = ConsoleLogger()
    l.log("Фабрика создала этот регистратор!")
    return l


def run_config_release():
    print("\n--- КОНФИГУРАЦИЯ 1: ВЫПУСК (PROD) ---")
    di = Injector()

    di.register(ILogger, ConsoleLogger, LifeStyle.SINGLETON)

    di.register(IDatabase, PostgresDB, LifeStyle.SCOPED, params={'connection_string': '192.168.1.1'})

    di.register(IAppService, BackendService, LifeStyle.PER_REQUEST, params={'app_name': 'SuperApp v1.0'})

    print("\n--- ТЕСТ ИНТЕРФЕЙСОВ ---")
    di.test_interface(IAppService)
    di.test_interface(IDatabase)

    class IUnknown(ABC): pass

    di.test_interface(IUnknown)

    print("\n[Scope 1 начало работы]")
    with di.scope():
        svc1 = di.get_instance(IAppService)
        svc2 = di.get_instance(IAppService)


        svc1.run()

        print(f"Check Singleton Logger: {svc1.logger is svc2.logger}")
        print(f"Check Scoped DB:      {svc1.db is svc2.db}")
        print(f"Check PerRequest App: {svc1 is svc2}")

    print("\n[Scope 2 Start]")
    with di.scope():
        svc3 = di.get_instance(IAppService)
        print(f"Check Scoped DB (Diff Scopes): {svc1.db is svc3.db}")


def run_config_debug():
    print("\n--- КОНФИГУРАЦИЯ 2: ОТЛАДКА (ТЕСТИРОВАНИЕ) ---")
    di = Injector()

    di.register(ILogger, create_special_logger, LifeStyle.PER_REQUEST)

    di.register(IDatabase, InMemoryDB, LifeStyle.SINGLETON)

    di.register(IAppService, TestService, LifeStyle.PER_REQUEST)

    svc = di.get_instance(IAppService)
    svc.run()


if __name__ == "__main__":
    run_config_release()
    print("-" * 30)
    run_config_debug()
