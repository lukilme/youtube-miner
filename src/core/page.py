from dataclasses import dataclass
from typing import Callable


@dataclass
class Page:
    name: str
    icon: str
    render: Callable
