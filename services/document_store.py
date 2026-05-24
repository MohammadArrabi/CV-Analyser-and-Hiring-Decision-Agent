from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

from base.retriever_base import RetrieverBase, RetrievalResult
from services.embedding_service import EmbeddingService
from pinecone.openapi_support.exceptions import NotFoundException

# Dimension of Google gemini-embedding-001 output vectors.
_EMBEDDING_DIMENSION = 3072

@dataclass
class ChunkConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50 # that mean she take 50 word (if the all chunk is paragraph) from the previous chunk because maybe the current chunk is continue to the previous chunk, so if we take overlap is understand more.
    # also about overlap she see that chunk end in sentence and another chunks start with this same sentence so also she know from that to relative between the chunks. overlap correct give more information/content (because we expend the chunk but אין ברירה)
    separators: list[str] = field(
        default_factory=lambda: ["\n\n","\n",".", " ",""] # mean she check if can take chunk as paragraph if don't have take line (\n) if not end of the sentence (.) if not word word if not all the document as one chunk ("")
        )

@dataclass
class PineconeConfig:
    api_key:str
    index_name: str
    namespace: str = "tutorial_04"
    cload: str = "aws"
    region: str = "us-east-1"

class DocumentStore(RetrieverBase):

    def __init__(
            self,
            embedding_service: EmbeddingService,
            pinecone_config: PineconeConfig,
            chunk_config: ChunkConfig = ChunkConfig(),
            cleanup_on_exit: bool = False,
    ) -> None:

        if not pinecone_config.api_key:
            raise ValueError("Pinecone API key is required")
        if not pinecone_config.index_name:
            raise ValueError("Pinecone index name is required")
        if not pinecone_config.namespace:
            raise ValueError("Pinecone namespace is required")

        self._embedder = embedding_service
        self._pc_cfg = pinecone_config
        self._cleanup_on_exit = cleanup_on_exit
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_config.chunk_size,
            chunk_overlap=chunk_config.chunk_overlap,
            separators=chunk_config.separators,
        )
        self._store: PineconeVectorStore | None = None

        pc = Pinecone(api_key=pinecone_config.api_key)
        existing = [idx.name for idx in pc.list_indexes()] # with the pinecone that have list_index command that return all the index that we define in pinecone website, and here in existing that have list of names (understood in unique index names)
        if pinecone_config.index_name not in existing: # if my index fon't found so create them
            pc.create_index(
                name=pinecone_config.index_name,
                dimension=_EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud=pinecone_config.cload, region=pinecone_config.region),
            )

        self._pc_index = pc.Index(pinecone_config.index_name) # return the index (when i say index is mean the store/place/file that we save the data inside them). .Index is index by name to know what to return

# this function do the chunks
    def load_file(self, path: str, metadata: dict | None = None) -> list[Document]: # dict | None is mean and show to the developer that this parameter just can be from type dict ot None
      text = Path(path).read_text(encoding="utf-8")
      base_meta = {"source": Path(path).name, **(metadata or {})} # ** all metadata or {} if she None
      chunks = self._splitter.create_documents([text], metadatas=[base_meta]) # we before define the splitter in ChunkConfig so she know how to split/create the chunks
      for i, chunk in enumerate(chunks):
          chunk.metadata["chunk_index"] = i # for all chunk give id
      return chunks

# fuunction to save the chunks in index store (notice also she do the embedding) (simple is do indexing to the data) and return reference to them (the data that you save)
    def index(self, documents: list[Document]) -> None:
      self._store = PineconeVectorStore.from_documents(
          documents=documents, # the chunks
          embedding=self._embedder.get_model(), # the model to use to do embedding (is understood in index we save with vectors)
          index_name=self._pc_cfg.index_name, # name the index to save the data inside
          pinecone_api_key=self._pc_cfg.api_key,
          namespace=self._pc_cfg.namespace,
      )

    def index_by_namespace(self, documents: list[Document], filename : str) -> str:
      nmsp = f"{self._pc_cfg.namespace}-{filename}"
      self._store = PineconeVectorStore.from_documents(
          documents=documents, # the chunks
          embedding=self._embedder.get_model(), # the model to use to do embedding (is understood in index we save with vectors)
          index_name=self._pc_cfg.index_name, # name the index to save the data inside
          pinecone_api_key=self._pc_cfg.api_key,
          namespace=nmsp,
      )
      return nmsp

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievalResult]:
      if self._store is None:
          return []
      raw = self._store.similarity_search_with_score(query, k=top_k)
      return [RetrievalResult(document=doc, score=score) for doc, score in raw] # return list of the object from type RetrievalResult (raw have the k most relative)

    def retrieve_mmr(self, query: str, top_k: int = 4) -> list[RetrievalResult]: # also they use semantic/simalirity like regular retrieve above, but here is interesting more to devision (تنوع) between the chunks not interest to the simalirity. (in the pdf can see how is work).
      if self._store is None:
          return []
      docs = self._store.max_marginal_relevance_search(
          query, k=top_k, fetch_k=top_k * 4,
          namespace=self._pc_cfg.namespace,
      )
      return [RetrievalResult(document=doc, score=1.0) for doc in docs] # here score 1.0 because with mmr don't important the simalirity but important to take from another relative chunks.

    def clear(self, list_of_namespaces: list[str]) -> None:

      if not list_of_namespaces:
       self._pc_index.delete(delete_all=True, namespace=self._pc_cfg.namespace) # notice in pinecore we have some indexes nad inside the index we can have some namespaces so we remove just the namespace that we want to delete.
      else:
       for namespace in list_of_namespaces:
           self._pc_index.delete(delete_all=True, namespace=namespace)
      self._store = None # the store that was saved in my ram to return that to None


# enter and exit use him with command "with"
    def __enter__(self) -> "DocumnetStore":
      return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
      if self._cleanup_on_exit:
          self.clear()