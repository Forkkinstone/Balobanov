from abc import ABC, abstractmethod
from pathlib import Path
import json
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field, asdict


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


class TextBuffer:
    def __init__(self, logger: 'DualLogger'):
        self._content = ""
        self._logger = logger

    def append(self, char: str) -> None:
        self._content += char
        self._logger.log(self._content)

    def remove_last(self) -> None:
        if self._content:
            self._content = self._content[:-1]
        self._logger.log(self._content)

    @property
    def content(self) -> str:
        return self._content

    def replace(self, new_content: str) -> None:
        self._content = new_content
        self._logger.log(self._content)


class PrintableCommand(Command):
    def __init__(self, key: str, buffer: TextBuffer):
        self.key = key
        self.buffer = buffer

    def execute(self) -> None:
        self.buffer.append(self.key)

    def undo(self) -> None:
        self.buffer.remove_last()


class VolumeUpCommand(Command):
    def execute(self) -> None:
        print("volume increased +20%")

    def undo(self) -> None:
        print("volume decreased -20%")


class VolumeDownCommand(Command):
    def execute(self) -> None:
        print("volume decreased -20%")

    def undo(self) -> None:
        print("volume increased +20%")


class MediaPlayerCommand(Command):
    def execute(self) -> None:
        print("media player launched")

    def undo(self) -> None:
        print("media player closed")


class DualLogger:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str) -> None:
        print(message)
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except(PermissionError, OSError, FileNotFoundError) as e:
            print(f"Критическая ошибка записи в файл: {e}")


@dataclass
class CommandData:
    type: str
    args: Dict[str, Any]


@dataclass
class KeyboardMemento:
    printed_sq: str
    undo_stack: List[str]
    redo_stack: List[str]
    commands: Dict[str, CommandData] = field(default_factory=dict)


class KeyboardStateSaver:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def save(self, memento: KeyboardMemento) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(memento), f, indent=4, ensure_ascii=False)
        except PermissionError:
            print(f"Ошибка доступа: нет прав на запись в файл {self.file_path}")
        except (OSError, IOError) as e:
            print(f"Системная ошибка при сохранении файла: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка при сохранении: {e}")

    def load(self) -> Optional[KeyboardMemento]:
        if not self.file_path.exists():
            return None
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            return KeyboardMemento(
                printed_sq=raw_data.get("printed_sq", ""),
                undo_stack=raw_data.get("undo_stack", []),
                redo_stack=raw_data.get("redo_stack", []),
                commands={
                    key: CommandData(**cmd)
                    for key, cmd in raw_data.get("commands", {}).items()
                }
            )
        except json.JSONDecodeError:
            print(f"Ошибка: Файл {self.file_path} поврежден или имеет неверный формат JSON.")
        except TypeError as e:
            print(f"Ошибка: Данные в файле не соответствуют структуре программы: {e}")
        except Exception as e:
            print(f"Не удалось восстановить состояние: {e}")

        return None


class CommandRegistry:
    def __init__(self):
        self._type_names: Dict[Type[Command], str] = {}
        self._creators: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Command]] = {}
        self._serializers: Dict[Type[Command], Callable[[Command], Dict[str, Any]]] = {}

    def register(
            self,
            name: str,
            cls: Type[Command],
            creator: Callable[[Dict[str, Any], Dict[str, Any]], Command],
            serializer: Callable[[Command], Dict[str, Any]]) -> None:

        self._type_names[cls] = name
        self._creators[name] = creator
        self._serializers[cls] = serializer

    def get_type_name(self, cmd: Command) -> str:
        cmd_type = type(cmd)
        if cmd_type not in self._type_names:
            raise ValueError(f"Unregistered command type: {cmd_type}")
        return self._type_names[cmd_type]

    def serialize_args(self, cmd: Command) -> Dict[str, Any]:
        cmd_type = type(cmd)
        if cmd_type not in self._serializers:
            raise ValueError(f"No serializer for: {cmd_type}")
        return self._serializers[cmd_type](cmd)

    def create(self, type_name: str, args: Dict[str, Any], context: Dict[str, Any]) -> Command:
        if type_name not in self._creators:
            raise ValueError(f"Unknown command type: {type_name}")
        return self._creators[type_name](args, context)


class VirtualKeyboard:
    def __init__(self, log_file: str, registry: CommandRegistry):
        self.logger = DualLogger(log_file)
        self.buffer = TextBuffer(self.logger)
        self.commands: Dict[str, Command] = {}
        self.undo_stack: List[str] = []
        self.redo_stack: List[str] = []
        self.state_saver = KeyboardStateSaver(log_file.replace(".txt", ".json"))
        self._registry = registry
        self._context = {"buffer": self.buffer}

    def bind(self, key_combo: str, command: Command) -> None:
        self.commands[key_combo] = command

    def press(self, key_combo: str) -> None:
        if key_combo not in self.commands:
            self.logger.log(f"Command '{key_combo}' not found")
            return
        cmd = self.commands[key_combo]
        cmd.execute()
        self.undo_stack.append(key_combo)
        self.redo_stack.clear()

    def undo(self) -> None:
        if not self.undo_stack:
            self.logger.log("Nothing to undo")
            return
        key_combo = self.undo_stack.pop()
        self.commands[key_combo].undo()
        self.redo_stack.append(key_combo)

    def redo(self) -> None:
        if not self.redo_stack:
            self.logger.log("Nothing to redo")
            return
        key_combo = self.redo_stack.pop()
        self.commands[key_combo].execute()
        self.undo_stack.append(key_combo)

    def save_state(self) -> None:
        command_data: Dict[str, CommandData] = {}
        for key, cmd in self.commands.items():
            try:
                type_name = self._registry.get_type_name(cmd)
                args = self._registry.serialize_args(cmd)
                command_data[key] = CommandData(type=type_name, args=args)
            except ValueError as e:
                self.logger.log(f"Skipping unregistered command '{key}': {e}")

        memento = KeyboardMemento(
            printed_sq=self.buffer.content,
            undo_stack=self.undo_stack.copy(),
            redo_stack=self.redo_stack.copy(),
            commands=command_data
        )
        self.state_saver.save(memento)

    def restore_state(self) -> bool:
        memento = self.state_saver.load()
        if not memento:
            return False

        self.buffer.replace(memento.printed_sq)
        self.undo_stack = memento.undo_stack.copy()
        self.redo_stack = memento.redo_stack.copy()

        restored_commands: Dict[str, Command] = {}
        for key, cmd_info in memento.commands.items():
            try:
                cmd = self._registry.create(cmd_info.type, cmd_info.args, self._context)
                restored_commands[key] = cmd
            except ValueError as e:
                self.logger.log(f"Failed to restore command '{key}': {e}")

        self.commands = restored_commands
        return True


def main():
    LOG_FILE = "keyboard_output.txt"
    Path(LOG_FILE).write_text("", encoding="utf-8")

    registry = CommandRegistry()

    registry.register(
        name="PrintableCommand",
        cls=PrintableCommand,
        creator=lambda args, ctx: PrintableCommand(args["key"], ctx["buffer"]),
        serializer=lambda cmd: {"key": cmd.key}
    )

    registry.register(
        name="VolumeUpCommand",
        cls=VolumeUpCommand,
        creator=lambda args, ctx: VolumeUpCommand(),
        serializer=lambda cmd: {}
    )

    registry.register(
        name="VolumeDownCommand",
        cls=VolumeDownCommand,
        creator=lambda args, ctx: VolumeDownCommand(),
        serializer=lambda cmd: {}
    )

    registry.register(
        name="MediaPlayerCommand",
        cls=MediaPlayerCommand,
        creator=lambda args, ctx: MediaPlayerCommand(),
        serializer=lambda cmd: {}
    )

    k = VirtualKeyboard(LOG_FILE, registry)

    for ch in "abcdef":
        k.bind(ch, PrintableCommand(ch, k.buffer))

    k.bind("ctrl++", VolumeUpCommand())
    k.bind("ctrl+-", VolumeDownCommand())
    k.bind("ctrl+p", MediaPlayerCommand())

    # Тестирование
    k.press('a')
    k.press('b')
    k.press('c')
    k.undo()
    k.undo()
    k.redo()
    k.press('ctrl++')
    k.undo()
    k.press('ctrl+-')
    k.undo()
    k.press('ctrl+p')
    k.undo()
    k.press('d')
    k.undo()
    k.undo()
    k.press('f')

    k.save_state()

    # Восстановление
    new_k = VirtualKeyboard(LOG_FILE, registry)
    if new_k.restore_state():
        new_k.logger.log("== Restored state ==")
        new_k.logger.log(f"Buffer: '{new_k.buffer.content}'")
        new_k.logger.log(f"Undo stack: {new_k.undo_stack}")
    else:
        new_k.logger.log("No saved state found.")


if __name__ == "__main__":
    main()
