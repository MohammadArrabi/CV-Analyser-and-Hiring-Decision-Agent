from abc import ABC, abstractmethod

class AgentBase(ABC): # ההרשאה בפיתון נשיפ בסוגריים הקלאס שרוצים לרשות ממנו

    @abstractmethod
    def chat(self, user_input: str) -> str:
        ... # this function don't implemented yet (היורשה יממש), חייב היורש לממש אותה אחרת שגיאה

    @abstractmethod
    def reset(self) -> None:
        ...

# i have things in summary about this two function in first the summary
# here we but str the type of return and this str is "AgentBase", this mean : we see AgentBase is the same type of the class so that mean maybe (we alredy inside the class we create and work) the object already don't complate so we put "AgentBase" to say aware and implement/run this (here enter function) when the object complate created
    def __enter__(self) -> "AgentBase":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.reset()