from abc import ABC, abstractmethod

class CvAgentBase(ABC): # ההרשאה בפיתון נשיפ בסוגריים הקלאס שרוצים לרשות ממנו

    @abstractmethod
    def chat(self, user_input: str) -> str:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...

    def __enter__(self) -> "CvAgentBase":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.reset()