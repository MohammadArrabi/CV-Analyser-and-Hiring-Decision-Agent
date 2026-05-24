import json
import re
from pathlib import Path

from dataclasses import dataclass
from services.document_store import DocumentStore
from services.llm_client import LlmClient
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from base.hiring_agent_base import HiringAgentBase
from datetime import datetime


@dataclass
class DataCard:
    source: str
    last_updated_date: str
    pii_risk: str
    purpose: str


def _redact_pii(text: str) -> str:
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.\w+\b", "[EMAIL]", text)
    text = re.sub(r"\b05\d[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]", text)
    return text

def dict_to_string(dict_of_cvs: dict[str, str]) -> str:
    formatted_cvs = []
    for name, cv_text in dict_of_cvs.items():
        # Create the separator sentence using the candidate's name
        header = f"Candidate {name}:\n{cv_text}"
        formatted_cvs.append(header)

    # Join all formatted CVs with a couple of newlines for clean separation
    return "\n\n".join(formatted_cvs)

class HiringAgent(HiringAgentBase):

    def __init__(
            self,
            document_store: DocumentStore,
            llm_client: LlmClient,
            data_cards: list[DataCard] | None = None,
    ) -> None:
        self.document_store = document_store
        self.llm = llm_client
        self._data_cards = data_cards or []
        self._history: list[BaseMessage] = []
        self._audit: list[dict] = []
        self.list_of_namespaces: list[str] = []

    def index_cvs(self, cvs_path: str) -> None:
        for path in Path(cvs_path).glob("*.txt"):
            file_docs = self.document_store.load_file(str(path))
            print(f"   {path.name:<40} {len(file_docs)} chunks(s)")
            name_space = self.document_store.index_by_namespace(file_docs,path.name)
            self.list_of_namespaces.append(name_space)


    def chat(self, user_input: str, dict_of_cvs : dict[str,str], description : str) -> str:
        clean = _redact_pii(user_input)
        all_cvs = dict_to_string(dict_of_cvs)
        SYSTEM = ("You are a helpful AI assistant, to hiring candidate to a job."
                  "You also get as input string that have the name of the candidate and his cv content, and job description")

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "question: {question}, all_cvs : {allCV}, description_job : {description}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "question": clean, "allCV": all_cvs, "description": description})
        self._history.append(HumanMessage(content=user_input))
        self._history.append(AIMessage(content=response))

        self._audit.append({
            "timestamp": datetime.now().isoformat(),
            "user": clean,
            "response": response,
        })
        return response


    def score(self, input: str, dict_of_cvs : dict[str,str], description : str):
        all_cvs = dict_to_string(dict_of_cvs)
        SYSTEM = ("You are a helpful AI assistant aimed to give score for all one from the cv against the description of the job, Score each candidate against the job description across multiple dimensions."
                  "you get as input string that have the name of the candidate and his cv content"
                  "return list of : name of the candidate(just his name) and his score. like : Alice : 9.5 ... not more any explain")

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "input : {input}, all_cvs : {allCV}, description_job : {description}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "input": input, "allCV": all_cvs, "description": description})
        self._history.append(HumanMessage(content=input))
        self._history.append(AIMessage(content=response))

        self._audit.append({
            "timestamp": datetime.now().isoformat(),
            "user": input,
            "response": response,
        })
        return response


    def final_recommendation(self, input: str, dict_of_cvs : dict[str,str], description : str) -> str:
        all_cvs = dict_to_string(dict_of_cvs)
        SYSTEM = ("You are a helpful AI assistant aimed to choose the best candidate recommendation to the job, you have the list cv's of the candidate and the job description, return best candidate to this job"
                  "return as output : the name of the best candidate, after that a short reason why she is the best.")

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "input : {input}, all_cvs : {allCV}, description_job : {description}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "input": input, "allCV": all_cvs, "description": description})
        self._history.append(HumanMessage(content=input))
        self._history.append(AIMessage(content=response))

        self._audit.append({
            "timestamp": datetime.now().isoformat(),
            "user": input,
            "response": response,
        })
        return response

    def _save_audit(self) -> None:
        if self._audit:
            Path("data").mkdir(exist_ok=True)
            Path("data/audit_log.json").write_text(
                json.dumps(self._audit, indent=2), encoding="utf-8"
            )
            print(f"\n[Audit log saved → data/audit_log.json ({len(self._audit)} entries)]")

    def reset(self) -> None:
        self._save_audit()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.reset()
        self.document_store.clear(self.list_of_namespaces)