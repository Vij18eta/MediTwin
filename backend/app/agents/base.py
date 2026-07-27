from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> dict:
        raise NotImplementedError
