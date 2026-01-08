from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Optional, Union, List
from dataclasses import dataclass

TEventArgs = TypeVar("TEventArgs")


class EventHandler(ABC, Generic[TEventArgs]):
    @abstractmethod
    def handle(self, sender: object, args: TEventArgs) -> None:
        ...


class Event(Generic[TEventArgs]):
    def __init__(self) -> None:
        self._subscribers: List[EventHandler[TEventArgs]] = []

    def __iadd__(self, handler: EventHandler[TEventArgs]) -> "Event[TEventArgs]":
        if handler not in self._subscribers:
            self._subscribers.append(handler)
        return self

    def __isub__(self, handler: EventHandler[TEventArgs]) -> "Event[TEventArgs]":
        if handler in self._subscribers:
            self._subscribers.remove(handler)
        return self

    def invoke(self, sender: object, args: TEventArgs) -> None:
        for handler in self._subscribers[:]:
            handler.handle(sender, args)

    __call__ = invoke


@dataclass
class PropertyChangedEventArgs:
    property_name: str


class PropertyChangedHandler(EventHandler[PropertyChangedEventArgs]):
    def handle(self, sender: object, args: PropertyChangedEventArgs) -> None:
        sender_type = sender.__class__.__name__
        print(f"[PropertyChanged] {sender_type}: property '{args.property_name}' was changed.")


@dataclass
class PropertyChangingEventArgs:
    property_name: str
    old_value: Any
    new_value: Any
    can_change: bool = True


class StringLengthValidator(EventHandler[PropertyChangingEventArgs]):
    def __init__(self, property_name: str, min_length: int = 0, max_length: Optional[int] = None):
        if min_length < 0:
            raise ValueError("min_length must be non-negative")
        if max_length is not None and max_length < min_length:
            raise ValueError("max_length must be >= min_length")
        self._property_name = property_name
        self._min_length = min_length
        self._max_length = max_length

    def handle(self, sender: object, args: PropertyChangingEventArgs) -> None:
        if args.property_name != self._property_name:
            return
        if not isinstance(args.new_value, str):
            print(f"[ERROR] '{self._property_name}' должно быть строкой.")
            args.can_change = False
            return
        length = len(args.new_value)
        if length < self._min_length:
            print(f"[ERROR] '{self._property_name}' слишком короткое (минимум {self._min_length} символов).")
            args.can_change = False
            return
        if self._max_length is not None and length > self._max_length:
            print(f"[ERROR] '{self._property_name}' слишком длинное (максимум {self._max_length} символов).")
            args.can_change = False


class NumericRangeValidator(EventHandler[PropertyChangingEventArgs]):
    def __init__(self, property_name: str, min_val: Optional[Union[int, float]] = None,
                 max_val: Optional[Union[int, float]] = None):
        if min_val is not None and max_val is not None and min_val > max_val:
            raise ValueError("min_val must be <= max_val")
        self._property_name = property_name
        self._min_val = min_val
        self._max_val = max_val

    def handle(self, sender: object, args: PropertyChangingEventArgs) -> None:
        if args.property_name != self._property_name:
            return

        if not isinstance(args.new_value, (int, float)):
            print(f"[ERROR] '{self._property_name}' должно быть числом.")
            args.can_change = False
            return

        value = args.new_value
        if self._min_val is not None and value < self._min_val:
            print(f"[ERROR] '{self._property_name}' слишком маленькое (минимум {self._min_val}).")
            args.can_change = False
            return

        if self._max_val is not None and value > self._max_val:
            print(f"[ERROR] '{self._property_name}' слишком большое (максимум {self._max_val}).")
            args.can_change = False


class ObservableObject:
    def __init__(self) -> None:
        self.property_changing: Event[PropertyChangingEventArgs] = Event()
        self.property_changed: Event[PropertyChangedEventArgs] = Event()

    def _set_property(self, name: str, value: Any) -> None:
        private_name = f"_{name}"
        if not hasattr(self, private_name):
            raise AttributeError(f"Свойство '{name}' не инициализировано в __init__")
        old_value = getattr(self, private_name)

        args = PropertyChangingEventArgs(property_name=name, old_value=old_value, new_value=value)
        self.property_changing(self, args)

        if not args.can_change:
            print(f"Change of '{name}' cancelled.\n")
            return

        setattr(self, private_name, value)
        self.property_changed(self, PropertyChangedEventArgs(property_name=name))


class Person(ObservableObject):
    def __init__(self, name: str, age: int, salary: float):
        super().__init__()
        self._name = name
        self._age = age
        self._salary = salary

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._set_property("name", value)

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        self._set_property("age", value)

    @property
    def salary(self) -> float:
        return self._salary

    @salary.setter
    def salary(self, value: float) -> None:
        self._set_property("salary", value)


class Product(ObservableObject):
    def __init__(self, title: str, price: float, quantity: int):
        super().__init__()
        self._title = title
        self._price = price
        self._quantity = quantity

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._set_property("title", value)

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self._set_property("price", value)

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        self._set_property("quantity", value)


if __name__ == "__main__":
    person = Person("Alice", 30, 60000.0)
    product = Product("Laptop", 1200.0, 10)

    printer = PropertyChangedHandler()

    name_validator = StringLengthValidator("name", min_length=2, max_length=50)
    age_validator = NumericRangeValidator("age", min_val=0, max_val=150)
    salary_validator = NumericRangeValidator("salary", min_val=0.0, max_val=200_000.0)

    title_validator = StringLengthValidator("title", min_length=3, max_length=100)
    price_validator = NumericRangeValidator("price", min_val=0.0, max_val=10_000.0)
    quantity_validator = NumericRangeValidator("quantity", min_val=0, max_val=100)

    person.property_changing += name_validator
    person.property_changing += age_validator
    person.property_changing += salary_validator
    person.property_changed += printer

    person.name = "A"                 # Ошибка: слишком короткое
    person.name = "Alexander"         # Успешно
    person.age = -5                   # Ошибка
    person.age = 25                   # Успешно
    person.salary = -1000             # Ошибка
    person.salary = 75000             # Успешно

    product.property_changing += title_validator
    product.property_changing += price_validator
    product.property_changing += quantity_validator
    product.property_changed += printer

    product.title = "TV"              # Ошибка: короче 3 символов
    product.title = "Gaming Laptop"   # Успешно
    product.price = -50               # Ошибка
    product.price = 999.99            # Успешно
    product.quantity = -1             # Ошибка
    product.quantity = 50             # Успешно
