import inspect
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Any, Type, Dict, List
from contextlib import contextmanager


class LifeStyle(Enum):
	PER_REQUEST = auto()
	SCOPED = auto()
	SINGLETON = auto()


class Injector:
	def __init__(self):
		self._registry = {}
		self._singletons = {}
		self._scope_stack: List[Dict[Any, Any]] = []

	def register(self, interface_type: Type, implementation: Any, life_style: LifeStyle = LifeStyle.PER_REQUEST, params: Dict[str, Any] = None):

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
			raise ValueError(f"Interface {interface_type.__name__} is not registered")

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
				raise RuntimeError("Trying to get a Scoped dependency out of context (with injector.scope(): ...)")

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

		raise TypeError(f"Unknown implementation type for {interface_type}")


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
		print(f"[File: {self.filename}] {message}")


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
		self.logger.log("Running TEST mode without real DB")


def create_special_logger():
	l = ConsoleLogger()
	l.log("Factory Created This Logger!")
	return l


def run_config_release():
	print("\n--- CONFIGURATION 1: RELEASE (PROD) ---")
	di = Injector()

	di.register(ILogger, ConsoleLogger, LifeStyle.SINGLETON)

	di.register(IDatabase, PostgresDB, LifeStyle.SCOPED, params={'connection_string': '192.168.1.1'})

	di.register(IAppService, BackendService, LifeStyle.PER_REQUEST, params={'app_name': 'SuperApp v1.0'})

	print("\n[Scope 1 Start]")
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
	print("\n--- CONFIGURATION 2: DEBUG (TEST) ---")
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
