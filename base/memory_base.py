from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class MemoryEntry:
    role: str
    content: str
    embedding: list[float] = field(default_factory=list) # IN THIS WAY INSTEAD OF TO DO = [], NEW IN THIS WAY THIS DO NEW FIELD SO IN ALL TIME WHO CALL MEMORY ENTERY THAT HAVE HIS OWN FIELD, but with [] in all time we have same list but we want field for all one alone (althoght all change can לדרוס מה היה קודם).


class MemoryBase(ABC):

    @abstractmethod
    def add(self, role: str, content: str) -> None:
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> list[MemoryEntry]:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...