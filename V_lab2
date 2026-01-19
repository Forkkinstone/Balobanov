import json
from enum import Enum

class Color(Enum):
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

class Printer:
    @staticmethod
    def load_font(path: str) -> dict:
        try:
            with open(path, "r", encoding="utf8") as f:
                return json.load(f)
        except:
            print("Failed to read the font file...")

    @staticmethod
    def _render_text(text: str, x: int, y: int, symbol: str, font: dict) -> None:
        all_characters = (font.values())
        first_character = list(all_characters)[0]
        height = len(first_character)

        print("\n" * (y - 1), end="")
        for row in range(height):
            print(" " * (x - 1), end="")
            for char in text:
                if char in font:
                    line = font[char][row].replace("*", symbol)
                else:
                    line = " "
                print(line, end="   ")
            print()

    @classmethod
    def print(cls, text: str, color: Color, position: tuple[int, int],
              symbol: str, font: dict) -> None:
        x, y = position
        print(color.value, end="")
        cls._render_text(text, x, y, symbol, font)
        print(Color.RESET.value, end="")

    def __init__(self, color: Color, position: tuple[int, int],
                 symbol: str, font: dict):
        self.color = color
        self.position = position
        self.symbol = symbol
        self.font = font

    def __enter__(self):
        print(self.color.value, end="")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(Color.RESET.value, end="")

    def print_(self, text: str) -> None:
        x, y = self.position
        self._render_text(text, x, y, self.symbol, self.font)


font5 = Printer.load_font("font5.json")
font7 = Printer.load_font("font7.json")

Printer.print(text="ANDREY", color=Color.MAGENTA, position=(2, 2), symbol="&", font=font5)

with Printer(color=Color.CYAN, position=(10, 2), symbol="@", font=font7) as pr:
    pr.print_("BOGDAN")
