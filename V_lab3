from abc import ABC, abstractmethod
from enum import IntEnum
from datetime import datetime
import re


class LogLevel(IntEnum):
    INFO = 1
    WARN = 2
    ERROR = 3


class ILogFilter(ABC):
    @abstractmethod
    def match(self, log_level: LogLevel, text: str) -> bool:
        ...


class LevelFilter(ILogFilter):
    def __init__(self, min_level: LogLevel):
        self.min_level = min_level

    def match(self, log_level: LogLevel, text: str) -> bool:
        return log_level >= self.min_level


class SimpleLogFilter(ILogFilter):
    def __init__(self, pattern: str):
        self.pattern = pattern

    def match(self, log_level: LogLevel, text: str) -> bool:
        return self.pattern in text


class ReLogFilter(ILogFilter):
    def __init__(self, pattern: str):
        try:
            self.pattern = re.compile(pattern)
        except re.error:
            self.pattern = None

    def match(self, log_level: LogLevel, text: str) -> bool:
        if self.pattern is None:
            return False
        return bool(self.pattern.search(text))


class ILogHandler(ABC):
    @abstractmethod
    def handle(self, log_level: LogLevel, text: str) -> None:
        ...


class ConsoleHandler(ILogHandler):
    def handle(self, log_level: LogLevel, text: str) -> None:
        print(text)


class FileHandler(ILogHandler):
    def __init__(self, filename: str):
        self.filename = filename

    def handle(self, log_level: LogLevel, text: str) -> None:
        try:
            with open(self.filename, "a", encoding="utf-8") as file:
                file.write(text + "\n")
        except (PermissionError, FileNotFoundError, OSError) as e:
            print(f"Ошибка записи лога: {e}")



class SocketHandler(ILogHandler):
    def handle(self, log_level: LogLevel, text: str) -> None:
        print(f"[SOCKET] Отправка сообщения: {text}")


class SyslogHandler(ILogHandler):
    def handle(self, log_level: LogLevel, text: str) -> None:
        print(f"[SYSLOG] {text}")


class FtpHandler(ILogHandler):
    def handle(self, log_level: LogLevel, text: str) -> None:
        print(f"[FTP] Запись лога: {text}")


class ILogFormatter(ABC):
    @abstractmethod
    def format(self, log_level: LogLevel, text: str) -> str:
        ...


class DaniilLogFormatter(ILogFormatter):
    def format(self, log_level: LogLevel, text: str) -> str:
        return f"(Daniil) {text}"


class DefaultLogFormatter(ILogFormatter):
    def __init__(self, time_format: str = "%Y.%m.%d %H:%M:%S"):
        self.time_format = time_format

    def format(self, log_level: LogLevel, text: str) -> str:
        current_time = datetime.now().strftime(self.time_format)
        return f"[{log_level.name}] [{current_time}] {text}"


class Logger:
    def __init__(
        self,
        log_filters: ILogFilter | list[ILogFilter],
        log_formatters: ILogFormatter | list[ILogFormatter],
        log_handlers: ILogHandler | list[ILogHandler]
    ):
        self.filters = log_filters if isinstance(log_filters, list) else [log_filters]
        self.formatters = log_formatters if isinstance(log_formatters, list) else [log_formatters]
        self.handlers = log_handlers if isinstance(log_handlers, list) else [log_handlers]

    def log(self, log_level: LogLevel, text: str) -> None:
        for log_filter in self.filters:
            if not log_filter.match(log_level, text):
                return

        for formatter in self.formatters:
            text = formatter.format(log_level, text)

        for handler in self.handlers:
            handler.handle(log_level, text)

    def log_info(self, text: str) -> None:
        self.log(LogLevel.INFO, text)

    def log_warn(self, text: str) -> None:
        self.log(LogLevel.WARN, text)

    def log_error(self, text: str) -> None:
        self.log(LogLevel.ERROR, text)

filters = [
    LevelFilter(LogLevel.WARN),
    SimpleLogFilter("error"),
    # ReLogFilter("adgasdgsa['///asdsak/\\")
]

formatters = [
    DefaultLogFormatter("%d.%m.%Y %H:%M:%S"),
    DaniilLogFormatter()
]

handlers = [
    ConsoleHandler(),
    FileHandler("result.log"),
    SyslogHandler(),
    FtpHandler()
]

logger = Logger(filters, formatters, handlers)

logger.log_info("this is info message")
logger.log_warn("warning without error")
logger.log_error("critical error happened")
