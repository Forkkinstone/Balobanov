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


class PatternValidator(EventHandler[PropertyChangingEventArgs]):
    def __init__(self, target_property: str, pattern: str):
        self.target_property = target_property
        self.pattern = pattern

    def handle(self, sender: Any, args: PropertyChangingEventArgs) -> None:

        if args.property_name != self.target_property:
            return

        if not isinstance(args.new_value, str):
            print(f"[ERROR]: Свойство '{args.property_name}' должно быть текстом!")
            args.can_change = False
            return

        word = args.new_value

        if len(word) != len(self.pattern):
            print(f"[ERROR VAL]: Слово '{word}' не подходит. Ожидается {len(self.pattern)} букв.")
            args.can_change = False
            return

        for i in range(len(self.pattern)):
            if self.pattern[i] == "_":
                continue

            if self.pattern[i].lower() != word[i].lower():
                print(f"[ERROR VAL]: Буква '{word[i]}' на позиции {i+1} не совпадает с шаблоном '{self.pattern[i]}'.")
                args.can_change = False
                return

        print(f"[O_MY_GOD]: Слово '{word}' идеально подошло под шаблон '{self.pattern}'!")


class ObservableObject:
    def __init__(self):
        self.property_changing = Event[PropertyChangingEventArgs]()
        self.property_changed = Event[PropertyChangedEventArgs]()

    def _set_property(self, prop_name: str, private_attr_name: str, value: Any):
        # 1. Берем старое значение через getattr
        old_value = getattr(self, private_attr_name)

        # 2. Создаем конверт и запускаем проверку
        args = PropertyChangingEventArgs(prop_name, old_value, value)
        self.property_changing.invoke(self, args)

        # 3. Если никто не против
        if args.can_change:
            setattr(self, private_attr_name, value)  # Меняем значение
            # 4. Сообщаем, что всё готово
            self.property_changed.invoke(self, PropertyChangedEventArgs(prop_name))


class Student(ObservableObject):
    def __init__(self, name: str, age: int, gpa: float):
        super().__init__()

        self._name = name
        self._age = age
        self._gpa = gpa

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._set_property("name", "_name", value)

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int):
        self._set_property("age", "_age", value)

    @property
    def gpa(self) -> float:
        return self._gpa

    @gpa.setter
    def gpa(self, value: float):
        self._set_property("gpa", "_gpa", value)


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
    def title(self, value: str):
        self._set_property("title", "_title", value)

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float):
        self._set_property("price", "_price", value)

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int):
        self._set_property("quantity", "_quantity", value)


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
    print(f"Текущая цена осталась: {product.price}\n")

    #Проверка фирменного валидатора "Поле чудес)"
    student = Student("Алексей", 20, 4.5)

    logger = ConsoleLogger()
    validator = Validator()
    pattern_checker = PatternValidator(target_property="name", pattern="Н_Ч___")

    student.property_changing += validator
    student.property_changing += pattern_checker
    student.property_changed += logger

    print("=== Попытка 1: Неправильное слово (не по паттерну) ===")
    student.name = "Николай"

    student.name = "Никола"

    print("\n=== Попытка 2: Правильное слово ===")
    student.name = "Ничего"

    print("\n=== Попытка 3: Другое свойство (проверка возраста) ===")
    student.age = -5


