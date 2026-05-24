import json
import re
from pathlib import Path

from dataclasses import dataclass
from base.cv_agent_base import CvAgentBase
from services.document_store import DocumentStore
from services.llm_client import LlmClient
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
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


class CVAnalyserAgent(CvAgentBase):

    def __init__(
            self,
            document_store: DocumentStore,
            llm_client : LlmClient,
            data_cards: list[DataCard] | None = None,
    ) -> None:
        self.document_store = document_store
        self.llm = llm_client
        self._data_cards = data_cards or []
        self._history: list[BaseMessage] = []
        self._audit: list[dict] = []

    def index_cv(self, cvs_path : str) -> None:
        docs = []
        for path in Path(cvs_path).glob("*.txt"):
            file_docs = self.document_store.load_file(str(path))
            docs.extend(file_docs)
            print(f"Index  {path.name:<40}")
        self.document_store.index(docs)
        print(f"   Total chunks indexed: {len(docs)}\n")

    def chat(self, user_input: str, cv : str) -> str:
        clean = _redact_pii(user_input)
        SYSTEM = "You are a helpful AI aimed To Analyse CV of candidates."
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "question: {question}, cv: {CV}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "question": clean, "CV": cv})
        self._history.append(HumanMessage(content=user_input))
        self._history.append(AIMessage(content=response))

        self._audit.append({
            "timestamp": datetime.now().isoformat(),
            "user": clean,
            "response": response,
        })
        return response

    def summary(self, input : str, cv : str) -> str:
        SYSTEM = ("You are a helpful AI assistant aimed to structured summary of the candidate cv on demand."
                  "The summary contain : candidate's name, experience level, and top skills.")
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "input : {input}, cv : {CV}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "input": input,"CV": cv})
        self._history.append(HumanMessage(content=input))
        self._history.append(AIMessage(content=response))

        self._audit.append({
            "timestamp": datetime.now().isoformat(),
            "user": input,
            "response": response,
        })
        return response

    def extract_skills(self, input : str, cv : str) -> str:
        SYSTEM = ("You are a helpful AI assistant aimed to extract and return two lists of technical and soft skills from the loading cv."
                  "write Technical skill as title under that the Technical skills, after that Soft skills as title and the soft skills. (list of technical and soft skills)"
                  "return just two lists: list of technical skills and list of soft skills."
                  "example output : **Technical Skills**: (new line) all the technical skills as list (new line) **Soft Skills**: (new line) all the soft skills as list"
                  "before all one form the skills put -")

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "input : {input}, cv : {CV}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "input": input,"CV": cv})
        self._history.append(HumanMessage(content=input))
        self._history.append(AIMessage(content=response))

        self._audit.append({
            "timestamp": datetime.now().isoformat(),
            "user": input,
            "response": response,
        })
        return response

    def improvement(self, input : str, cv : str, section : str) -> str:
        SYSTEM = ("You are a helpful AI assistant aimed to suggested improvement in one section in the cv, You Suggest improve selected section in the cv."
                  "return the orginal section and the suggested improve for this section"
                  "example output : ==Orginal 'name the section'== : (new line) the orginal section content (new line) ==suggested improve 'name of section'== : (new line) suggested improve for this section.")
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "input : {input}, cv : {CV}, section : {SECTION}"),
        ])
        response: str = self.llm.build_chain(prompt).invoke({"history": self._history, "input" : input, "CV": cv, "SECTION": section})
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
        self.document_store.clear([])