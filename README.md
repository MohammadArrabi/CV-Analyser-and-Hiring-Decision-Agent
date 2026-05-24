⚠️ **Project Status: Active Development**

# CV-Analyser-and-Hiring-Decision-Agent

Dual-agent AI system for interactive CV analysis and automated, multi-dimensional candidate hiring decisions.

An advanced, production-ready AI recruiting assistant built to streamline the hiring workflow. This project leverages an agentic architecture to seamlessly move from deep, interactive candidate profiling to automated, multi-dimensional candidate evaluation.

The system is split into two distinct operational phases :

*   **Phase 1: CV Analyser Agent** – A conversational Retrieval-Augmented Generation (RAG) agent that indexes a candidate's CV into Pinecone, allowing recruiters to deeply explore qualifications, extract structured skills, and generate targeted resume improvement feedback.
*   **Phase 2: Hiring Decision Agent** – An automated decision-making agent that concurrently evaluates multiple candidates against a shared job description using strict vector isolation (namespaces), scoring them across multiple dimensions to issue a data-driven hiring recommendation.

---

## 🚀 Key Architectural Features

*   **🤖 Multi-Agent Workflow:** Separate specialized agents built to handle deep individual analysis vs. comparative hiring logic.
*   **🔒 Isolated Vector Storage:** Uses dedicated Pinecone namespaces per candidate to maintain strict data compliance, ensuring zero information leakage between candidate profiles.
*   **🛡️ Data Privacy & Compliance:** Implements specialized **CV Data Cards** to audit and justify Personal Identifiable Information (PII) risk levels before processing.
*   **🧩 Optimized Chunking Strategy:** Text splitting is precision-tuned for structured resume sections rather than default generic limits to ensure high semantic accuracy.
*   **💻 Custom REPL Interface:** A tailored Command-Line Interface (CLI) loop featuring custom reserved keywords for structured analysis, comparisons, and automated database cleanup on exit.

---

## ⚙️ Setup Before Running

Add these files and folders to your project directory :
1. Create a `.env` file containing the following lines :
   <p>GEMINI_API_KEY="ADD YOUR GEMINI_API_KEY"</p>
   <p>GEMINI_MODEL_NAME=gemini-2.5-flash</p>
   <p>GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001</p>
   <p>GEMINI_TEMPERATURE=0.7</p>
   <p>PINECONE_API_KEY="ADD YOUR PINECONE_API_KEY"</p>
   <p>PINECONE_INDEX_NAME=cv-analyser-index</p>
   <p>PINECONE_NAMESPACE=cv-analyser-namespace</p>

2. Make sure you have a folder to put the data in. so you can do these steps:
- Create folder called "data".
- Inside the data folder, create a new folder to put your job description files in.
- Inside the data folder, create another folder to put your CV's files in.

---

## 📂 PHASE 1 - CV Analyser Agent (CVAnalyserAgent)
### 🧠 What the agent can do 
* Index a single CV file into Pinecone.
* Answer free-form questions about the CV through the standard chat loop.
* Produce a structured summary of the candidate on demand.
* Extract technical and soft skills from the CV as separate lists.
* Suggest improvements for a named section (e.g., SUMMARY, WORK EXPERIENCE).

### 🛠️ How to run 
* Run main_phase1.py (In PyCharm, write this command in the terminal): python main_phase1.py

### 🎛️ The available commands 
*   `exit` or `quit`: End the run.
*   `select`: Select another candidate CV.
*   `summary`: Summarize the candidate CV.
*   `skills`: Receive/extract two lists of technical and soft skills from the candidate CV.
*   `improvement <name_of_the_section>`: Receive improvement suggestions for the chosen section in the candidate CV.

---

## 📂 PHASE 2 - Hiring Decision Agent (`HiringAgent`)

### 🧠 What the agent can do 
*   Index each CV in an isolated Pinecone namespace (one per candidate).
*   Score each candidate against the job description across multiple dimensions.
*   Produce a side-by-side comparison of all candidates.
*   Issue a final recommendation with written justification.

### 🛠️ How to run 
*   Run `main_phase2.py` (In PyCharm, write this command in the terminal): python main_phase2.py

### 🎛️ The available commands 
*   `exit` or `quit`: End the run.
*   `select`: Select another job description.
*   `score`: Receive a score out of 10 indicating how well each candidate matches the chosen job description.
*   `comparison`: Compare the candidates (don't compare yet).
*   `recommendation`: Choose the best recommended candidate for the selected job.

---

## ✉️ Contact

For any questions or inquiries, please contact :
<ol>
  <li>Mohammad Arabi - mohammadarabe22@gmail.com</li>
</ol>
