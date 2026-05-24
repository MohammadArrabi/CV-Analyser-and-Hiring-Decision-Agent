import os
import sys
from pathlib import Path
import docx
import docx2txt

from dotenv import load_dotenv

from agents import hiring_agent
from agents.hiring_agent import HiringAgent
from services.document_store import DocumentStore, ChunkConfig, PineconeConfig
from services.embedding_service import EmbeddingService, EmbeddingConfig
from services.llm_client import LlmClient, LlmConfig

load_dotenv()

llm_client = LlmClient(
    LlmConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name=os.getenv("GEMINI_MODEL_NAME"),
        temperature=float(os.getenv("GEMINI_TEMPERATURE")),
    )
)

embedder = EmbeddingService(
    EmbeddingConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name=os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"),
    )
)

pc_config = PineconeConfig(
    api_key=os.getenv("PINECONE_API_KEY"),
    index_name=os.getenv("PINECONE_INDEX_NAME"),
    namespace=os.getenv("PINECONE_NAMESPACE"),
)

store = DocumentStore(embedder, pc_config, ChunkConfig(chunk_size=60, chunk_overlap=20))
Hiring_Agent = HiringAgent(store, llm_client)

def read_docx(file_path):
    """Opens a .docx file and converts its paragraphs into a single string."""
    doc = docx.Document(file_path)
    # Word files are split into paragraphs. We join them with newlines.
    full_text = [paragraph.text for paragraph in doc.paragraphs]
    return "\n".join(full_text)

def doc_to_text(path : str) -> None:
    # Find all .docx files in the folder
    for docx_path in Path(path).glob("*.docx"):
        # Create the new .txt file path (e.g., "document.docx" -> "document.txt")
        txt_path = docx_path.with_suffix(".txt")

        # Check if the .txt version already exists so you don't waste time re-converting
        if not txt_path.exists():
            try:
                # Extract text from docx
                text = docx2txt.process(docx_path)

                # Save it as a text file
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)

                print(f" Converted: {docx_path.name} -> {txt_path.name}")
            except Exception as e:
                print(f"❌ Failed to convert {docx_path.name}: {e}")
        else:
            print(f" Skip: {txt_path.name} already exists.")

def files_to_dict(path : str) -> dict[str, str]:
    dict = {}
    # 3. Check if the directory exists
    if path.exists():
        # Loop through every .txt file in the folder, regardless of its name
        for file_path in path.glob("*.txt"):
            try:
                file_name_key = file_path.stem
                file_text = file_path.read_text(encoding="utf-8")

                dict[file_name_key] = file_text

                print(f"Loaded: {file_name_key}")
            except Exception as e:
                print(f"Could not read {file_path.name}: {e}")
    else:
        print(f"Directory {path} not found.")
    return dict


print("Hello, Welcome to CV Hiring Agent!\n")
cvs_path = Path(input("As a first time insert the path to your docx/txt CV's files (e.g data/CVs): ").strip())

while not cvs_path.exists() or not cvs_path.is_dir():
    cvs_path = Path(input("\nOops, It's invalid path insert another valid path: ").strip())

print("\nA valid CV's path is inserted. if we found docx cv file we create the new txt file for this cv.\n")

doc_to_text(cvs_path)
print("=== Check the cv files complete! Now running your indexing code ===\n")

print(f"***** Start indexing the CV's from {cvs_path} *****")
Hiring_Agent.index_cvs(cvs_path)
dict_of_cvs = files_to_dict(cvs_path)

jds_path = Path(input("\nNow insert the path to your docx/txt Job Description files (e.g data/Job_Description): ").strip())
while not jds_path.exists() or not jds_path.is_dir():
    jds_path = Path(input("\nOops, It's invalid path insert another valid path: ").strip())

print("\nA valid Job Description path is inserted. if we found docx cv file we create the new txt file for this Job Description.\n")

doc_to_text(jds_path)
dict_of_jds = files_to_dict(jds_path)
jd_name = input("\ninsert job description name: ").strip()
jd = dict_of_jds[jd_name]

with Hiring_Agent:
    while True:
        try:
            user_input = input("\nUser question/command: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!\n")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!\n")
            sys.exit(0)

        if user_input.lower() == "select":
            jd_name = input("insert new job description name to select: ").strip()
            jd = dict_of_jds[jd_name]
            continue

        if user_input.lower().strip() == "score":
          candidate_scores = Hiring_Agent.score("give score for all one from the candidate cv against the description of the job",dict_of_cvs,jd)
          print("\nAgent answer: List of Candidate Name with His Score:\n")
          print(candidate_scores)
          #for cv_name, score in dict_of_scores.items():
          #    print(f"{cv_name}: {score}")
          continue

        if user_input.lower().strip() == "comparison":
            continue

        if user_input.lower() == "recommendation":
          result = Hiring_Agent.final_recommendation("Return the best recommendation candidate to this job.",dict_of_cvs,jd)
          print(f"\nAgent answer: Best Recommendation Candidate to this description is : {result}\n")
          continue

        answer = Hiring_Agent.chat(user_input,dict_of_cvs, jd)
        print(f"\nAgent answer: {answer}")