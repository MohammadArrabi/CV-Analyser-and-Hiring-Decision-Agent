import os
import sys
from pathlib import Path
import docx
import docx2txt

from dotenv import load_dotenv
from agents.cv_analyser_agent import CVAnalyserAgent
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
CVAnalyse_Agent = CVAnalyserAgent(store, llm_client)

def read_docx(file_path):
    """Opens a .docx file and converts its paragraphs into a single string."""
    doc = docx.Document(file_path)
    # Word files are split into paragraphs. We join them with newlines.
    full_text = [paragraph.text for paragraph in doc.paragraphs]
    return "\n".join(full_text)

print("Hello, Welcome to CV Analyser Agent!\n")
cvs_path = Path(input("As a first time insert the path to your docx/txt CV's files (e.g data/CVs): ").strip())

while not cvs_path.exists() or not cvs_path.is_dir():
    cvs_path = Path(input("\nOops, It's invalid path insert another valid path: ").strip())

print("A valid path is inserted. if we found docx cv file we create the new txt file for this cv.\n")

# Find all .docx files in the folder
for docx_path in Path(cvs_path).glob("*.docx"):
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

print("=== Check the cv files complete! Now running your indexing code ===\n")

print(f"***** Start indexing the CV's from {cvs_path} *****")
CVAnalyse_Agent.index_cv(cvs_path)

dict_of_cvs = {}

# 3. Check if the directory exists
if cvs_path.exists():
    # Loop through every .txt file in the folder, regardless of its name
    for file_path in cvs_path.glob("*.txt"):
        try:
            file_name_key = file_path.stem
            file_text = file_path.read_text(encoding="utf-8")

            dict_of_cvs[file_name_key] = file_text

            print(f"Loaded: {file_name_key}")
        except Exception as e:
            print(f"Could not read {file_path.name}: {e}")
else:
    print(f"Directory {cvs_path} not found.")

print("\n*/*/* Choose Selected CV */*/*\n")
cv_name = input("insert cv name: ").strip()
cv = dict_of_cvs[cv_name]

with CVAnalyse_Agent:
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
            cv_name = input("\ninsert new cv name to select: ").strip()
            cv = dict_of_cvs[cv_name]
            continue

        if user_input.lower() == "summary":
            answer = CVAnalyse_Agent.summary("summary this cv",cv)
            print(f"\nAgent answer: {answer}")
            continue

        if user_input.lower() == "skills":
            answer = CVAnalyse_Agent.extract_skills("Extract the technical and soft skills from this cv",cv)
            print(f"\nAgent answer: {answer}")
            continue

        if user_input.lower().startswith("improvement "):
            section = user_input[13:]
            answer = CVAnalyse_Agent.improvement(f"improvement in {section} in this cv",cv, section)
            print(f"\nAgent answer: {answer}")
            continue

        answer = CVAnalyse_Agent.chat(user_input, cv)
        print(f"\nAgent answer: {answer}")