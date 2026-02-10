# 📊 AutoReport Pro: AI-Driven Analytics Agent

AutoReport Pro is an intelligent multi-agent system that transforms raw CSV data into professional, executive-level PDF reports. Built with **LangGraph** and **Ollama**, it leverages specialized agents to perform statistical analysis, KPI tracking, and high-fidelity LaTeX document synthesis.

---

## 🚀 Key Features

* **Multi-Agent Architecture**: Discrete agents for Planning, Statistics, KPIs, and Executive Writing.
* **LaTeX Document Synthesis**: Generates professional academic-grade reports (avoiding inconsistent Markdown-to-PDF conversions).
* **Automated Visualizations**: Dynamically generates time-series charts and histograms based on identified data trends.
* **Smart PDF Post-Processing**: Automatically removes redundant title pages and unifies document structure via **PyPDF2**.
* **Real-time Streaming**: Features a built-in spinner and typewriter effect to monitor agent progress in the terminal.
* **Robust Error Handling**: Automated LaTeX character escaping (fixing `$`, `%`, and `_`) and `itemize` environment validation.

---

## 🛠️ Tech Stack

* **Orchestration**: LangGraph / LangChain
* **LLM**: Ollama (Llama 3 / Mistral)
* **PDF Engine**: LaTeX (`pdflatex`)
* **PDF Manipulation**: PyPDF2
* **Data Handling**: Pandas / Matplotlib / Seaborn

---

## 📋 Prerequisites

Before running the agent, ensure you have the following installed:

1.  **Ollama**: [Download here](https://ollama.ai/)
2.  **LaTeX**:
    * *Ubuntu/Debian*: `sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra`
    * *MacOS*: `brew install --cask mactex`
3.  **Python Dependencies**:
    ```bash
    pip install langgraph pandas requests PyPDF2 matplotlib seaborn
    ```

---

## 🏃 How to Run

1.  **Start Ollama**:
    ```bash
    ollama run llama3
    ```

2.  **Prepare your Data**:
    Place your `data.csv` in the root directory or set the `DATA_SOURCE` environment variable.

3.  **Execute the Agent**:
    ```bash
    python main.py
    ```

4.  **Find your Report**:
    The final output is generated at `output/report.pdf`.

---

## 🤖 Agent Workflow

1.  **Planner**: Analyzes CSV headers and defines the reporting strategy.
2.  **Reporting Agents (KPIs & Stats)**: Extract insights and format them into validated LaTeX blocks.
3.  **Visualization Agent**: Executes Python code to create PNG artifacts for visual context.
4.  **Writer Agent**: Assembles all components into a structured LaTeX `article` template.
5.  **Final PDF Node**: Injects images, compiles the `.tex` file twice (for layout stability), and trims the final PDF.

---


## 📊 flowchart
image link  https://github.com/simran1devloper/Autoreport_agent/blob/main/agent_flow.png

## 📁 Project Structure

```text
├── main.py              # Entry point & Graph execution
├── graph.py             # LangGraph workflow & state definition
├── agents.py            # Agent logic & final_pdf compilation
├── utils.py             # Ollama API caller & character cleaning
├── data.csv             # Input dataset
└── output/              # Target for .tex, .png, and .pdf artifacts
