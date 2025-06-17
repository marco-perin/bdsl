from enum import Enum


class Colors(Enum):
    HEADER = '\033[95m'
    FAIL = '\033[91m'
    RED = '\033[31m'
    BRIGHTRED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WARNING = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[35m'
    BRIGHTMAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BRIGHTCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    FAINT = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK_SLOW = '\033[5m'
    BLINK_FAST = '\033[6m'
    REVERSE = '\033[7m'

    def get_text(self, text: str | int | float):
        return f'{self.value}{text}{Colors.ENDC.value}'

    def __call__(self, text: str | int | float):
        return self.get_text(text)


c = Colors
