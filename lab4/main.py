from typing import TypeVar, Generic, Any
from abc import ABC, abstractmethod

class EventArgs:
    pass

TEventArgs = TypeVar('TEventArgs', bound=EventArgs)


class EventHandler(ABC, Generic[TEventArgs]):
    @abstractmethod
    def handle(self, sender: Any, args: TEventArgs) -> None:
        """Метод для обработки события"""
        pass


class Event(Generic[TEventArgs]):
    def __init__(self):
        self.handlers: list[EventHandler[TEventArgs]] = []

    def __iadd__(self, handler: EventHandler[TEventArgs]):
        if handler not in self.handlers:
            self.handlers.append(handler)
        return self

    def __isub__(self, handler: EventHandler[TEventArgs]):
        if handler in self.handlers:
            self.handlers.remove(handler)
        return self

    def invoke(self, sender: Any, args: TEventArgs) -> None:
        for handler in self.handlers:
            handler.handle(sender, args)


class PropertyChangedEventArgs(EventArgs):
    def __init__(self, property_name: str):
        self.property_name = property_name


class ConsoleLogger(EventHandler[PropertyChangedEventArgs]):
    def handle(self, sender: Any, args: PropertyChangedEventArgs) -> None:
        # Получаем новое значение свойства через getattr
        new_value = getattr(sender, args.property_name)
        print(
            f"[LOG]: У объекта {sender.__class__.__name__} изменено свойство '{args.property_name}' на значение {new_value}.")


class PropertyChangingEventArgs(EventArgs):
    def __init__(self, property_name: str, old_value: Any, new_value: Any):
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.can_change = True  # Флаг, разрешающий изменение


class Validator(EventHandler[PropertyChangingEventArgs]):
    def handle(self, sender: Any, args: PropertyChangingEventArgs) -> None:

        if isinstance(args.new_value, (int, float)) and args.new_value < 0:
            print(
                f"[ОШИБКА]: Свойство '{args.property_name}' не может быть меньше 0! Попытка установить {args.new_value} отклонена.")
            args.can_change = False

        elif isinstance(args.new_value, str) and args.new_value.strip() == "":
            print(f"[ОШИБКА]: Свойство '{args.property_name}' не может быть пустым! Изменение отклонено.")
            args.can_change = False


class Student:
    def __init__(self, name: str, age: int, gpa: float):
        self.property_changing = Event[PropertyChangingEventArgs]()
        self.property_changed = Event[PropertyChangedEventArgs]()

        self._name = name
        self._age = age
        self._gpa = gpa

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        # 1. Создаем аргументы для события ДО изменения
        args = PropertyChangingEventArgs("name", self._name, value)
        # 2. Оповещаем подписчиков 
        self.property_changing.invoke(self, args)
        # 3. Проверяем, не отменил ли кто-то изменение
        if args.can_change:
            self._name = value
            # 4. Вызываем событие ПОСЛЕ изменения
            self.property_changed.invoke(self, PropertyChangedEventArgs("name"))

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int):
        args = PropertyChangingEventArgs("age", self._age, value)
        self.property_changing.invoke(self, args)
        if args.can_change:
            self._age = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("age"))

    @property
    def gpa(self) -> float:
        return self._gpa

    @gpa.setter
    def gpa(self, value: float):
        args = PropertyChangingEventArgs("gpa", self._gpa, value)
        self.property_changing.invoke(self, args)
        if args.can_change:
            self._gpa = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("gpa"))


class Product:
    def __init__(self, title: str, price: float, quantity: int):
        self.property_changing = Event[PropertyChangingEventArgs]()
        self.property_changed = Event[PropertyChangedEventArgs]()

        self._title = title
        self._price = price
        self._quantity = quantity

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        args = PropertyChangingEventArgs("title", self._title, value)
        self.property_changing.invoke(self, args)
        if args.can_change:
            self._title = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("title"))

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float):
        args = PropertyChangingEventArgs("price", self._price, value)
        self.property_changing.invoke(self, args)
        if args.can_change:
            self._price = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("price"))

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int):
        args = PropertyChangingEventArgs("quantity", self._quantity, value)
        self.property_changing.invoke(self, args)
        if args.can_change:
            self._quantity = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("quantity"))


if __name__ == "__main__":
    # Создаем обработчики
    logger = ConsoleLogger()
    validator = Validator()


    print("--- Тестирование класса Student ---")
    student = Student("Алексей", 20, 4.5)

    student.property_changing += validator
    student.property_changed += logger

    student.name = "Иван"
    student.age = 21

    student.age = -5
    student.name = "   "
    print(f"Текущий возраст остался: {student.age}, Имя осталось: {student.name}\n")

    print("--- Тестирование класса Product ---")
    product = Product("Ноутбук", 50000.0, 10)

    product.property_changing += validator
    product.property_changed += logger

    product.price = 45000.0

    product.price = -100.0
    print(f"Текущая цена осталась: {product.price}")
