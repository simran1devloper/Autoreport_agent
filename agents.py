import os
import uuid
import pandas as pd
import re
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from utils import call_ollama, safe_json_load, extract_code, execute_command
from logger import LogColors

def clean_content(content: Any) -> str:
    """Removes Markdown, flattens dicts, and clears placeholders."""
    if isinstance(content, dict):
        return "\n".join([f"{k.replace('_', ' ').title()}: {clean_content(v)}" for k, v in content.items()])
    if isinstance(content, list):
        return "\n".join([f"- {clean_content(i)}" for i in content])
    
    text = str(content)
    text = re.sub(r'\*\*|__|\*|_|#+\s?', '', text) # Remove Markdown
    text = re.sub(r'\[insert.*?\]', 'N/A', text)   # Remove placeholders
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").strip()

class BaseAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name
import pandas as pd

class StrategicPlanner(BaseAgent):
    def run(self, csv_path: str) -> Dict[str, Any]:
        # 1. Load a snippet of data to create context
        try:
            df = pd.read_csv(csv_path)
            # Create a summary string for the LLM
            data_context = f"""
            Columns: {list(df.columns)}
            Sample Data (first 2 rows):
            {df.head(2).to_dict()}
            Shape: {df.shape}
            """
        except Exception as e:
            data_context = f"Error loading CSV headers: {str(e)}"
 

        # 2. Ask the LLM to generate the goals
        prompt = f"""
       Based on the data schema {data_context}, define a visualization strategy.

        Your strategy must include:
        1. A 'viz_goal' that explicitly requests a Comparison Bar Chart between the main categories (e.g., 'Compare total units sold by Product').
        2. Instructions for secondary plots like 'Time-series trends' or 'Price distributions'.

        Return the plan in JSON format:
        {{
        "kpi_goal": "...",
        "stats_goal": "...",
        "viz_goal": "Generate a grouped bar chart comparing Units Sold by Product and a line chart for daily sales trends."
        }}
        """
        
        plan_res = call_ollama(self.model_name, prompt, is_json=True)
        plan = safe_json_load(plan_res, {
            "kpi_goal": "General KPIs", 
            "stats_goal": "Basic statistics", 
            "viz_goal": "Data distribution"
        })

        # 3. Return both the plan AND the data_summary to the state
        return {
            "plan": plan,
            "data_summary": data_context
        }


import os
import uuid
import subprocess
import glob
from typing import List

class VisualizationAgent(BaseAgent):
    def __init__(self, model_name: str, output_dir: str = "output"):
        super().__init__(model_name)
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, csv_path: str, viz_goal: str) -> List[str]:
        # 1. Provide the agent with actual column names to prevent "KeyErrors"
        try:
            import pandas as pd
            df_cols = list(pd.read_csv(csv_path).columns)
        except:
            df_cols = "Unknown"

        script_name = f"temp_viz_{uuid.uuid4().hex[:8]}.py"
        pre_files = set(glob.glob(os.path.join(self.output_dir, "*.png")))
        
        # 2. Optimized Prompt: Expert Data Scientist Mode
        prompt = f"""
        You are a Senior Data Scientist. Write a Python script to visualize this CSV: '{os.path.abspath(csv_path)}'.
        
        DATA SCHEMA:
        Columns: {df_cols}
        
        GOAL:
        {viz_goal}
        - Automatically decide the best charts. 
        - If 'Product' and 'units_sold' exist, prioritize a Bar Chart comparing them.
        
        STRICT RULES:
        1. TOP LINE: 'import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import pandas as pd'
        2. CLEANING: Use 'df.dropna()' before plotting.
        3. DESIGN: Use plt.style.use('ggplot'), add titles, and clear labels.
        4. OUTPUT: Save to '{self.output_dir}' with unique names.
        5. LOGGING: For EVERY file saved, you MUST print: PATH:<full_path>
        
        Provide ONLY the Python code block.
        """
        
        code = extract_code(call_ollama(self.model_name, prompt, is_json=False))
        
        try:
            with open(script_name, "w") as f:
                f.write(code)
            
            # 3. Capture the error if it fails to help you debug
            proc = subprocess.run(["python", script_name], capture_output=True, text=True)
            
            if proc.returncode != 0:
                print(f"{LogColors.ERROR}Plotting Script Failed! Error: {proc.stderr}{LogColors.RESET}")
                return []

            # Extract paths
            paths = [line.split("PATH:")[-1].strip() for line in proc.stdout.splitlines() if "PATH:" in line]
            
            # Fallback discovery
            if not paths:
                post_files = set(glob.glob(os.path.join(self.output_dir, "*.png")))
                paths = list(post_files - pre_files)
                
            return paths
        finally:
            if os.path.exists(script_name): os.remove(script_name)

from typing import Dict, Any

class ReportingAgent(BaseAgent):
    def generate_section(self, section_type: str, summary: Any, goal: str) -> str:
        # 1. Pre-processing: Escape raw data symbols
        safe_summary = self.clean_for_latex(str(summary))
        
        persona = "Lead Statistical Analyst" if section_type == "stats" else "Senior Business Consultant"
        
        prompt = f"""
        ROLE: {persona} (LaTeX Specialist)
        DATA: {safe_summary}
        GOAL: {goal}

        INSTRUCTIONS:
        Generate a professional report section using raw LaTeX code.
        DO NOT include a preamble or \\begin{{document}}.
        
        STRUCTURE:
        \\subsection*{{{section_type.upper()} Analysis}}
        \\textbf{{Key Finding:}} [One sentence]
        \\begin{{itemize}}
          \\item \\textbf{{Trend:}} ...
          \\item \\textbf{{Metrics:}} ...
          \\item \\textbf{{Strategic "So What?":}}
            \\begin{{itemize}}
              \\item ...
            \\end{{itemize}}
        \\end{{itemize}}

        STRICT RULES:
        - Output ONLY the LaTeX code. 
        - Ensure every \\begin{{itemize}} has a matching \\end{{itemize}}.
        """
        
        raw_latex = call_ollama(self.model_name, prompt, is_json=False).strip()
        
        # 2. Post-processing: Validate and Repair tags
        return self.validate_latex(raw_latex)

    def clean_for_latex(self, text: str) -> str:
        """Escapes common LaTeX control characters found in data."""
        replacements = {'$': r'\$', '%': r'\%', '&': r'\&', '#': r'\#', '_': r'\_'}
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text

    def validate_latex(self, text: str) -> str:
        """Counts itemize tags and appends missing closing tags to prevent crashes."""
        open_tags = text.count(r'\begin{itemize}')
        close_tags = text.count(r'\end{itemize}')
        
        if open_tags > close_tags:
            # Append missing tags to the end of the string
            missing = open_tags - close_tags
            text += (r'\end{itemize}' * missing)
            print(f">>> Auto-Repair: Added {missing} missing \\end{{itemize}} tags.")
            
        return text

class WriterAgent(BaseAgent):
    def run(self, kpis: str, stats: str) -> str:
        prompt = f"""
        ROLE: LaTeX Document Architect
        
        GOAL: Generate a complete, valid LaTeX document based on the provided KPI and STATS blocks.
        
        INPUT DATA:
        KPI Block: {kpis}
        STATS Block: {stats}

        STRICT LATEX TEMPLATE RULES:
        1. DOCUMENT CLASS: Use \\documentclass[11pt]{{article}}
        2. PACKAGES: Include \\usepackage{{graphicx}}, \\usepackage{{geometry}}, \\usepackage{{booktabs}}
        3. GEOMETRY: Use \\geometry{{margin=1in, top=0.5in}} to ensure no blank space at the top.
        4. PREAMBLE: You MUST define:
           \\title{{Sales Performance Executive Report}}
           \\author{{AI Analytics Agent}}
           \\date{{\\today}}
        5. BODY: 
           - Start with \\begin{{document}}
           - Immediately call \\maketitle (This will now work and won't be blank).
           - Insert a 2-3 sentence Executive Summary.
           - Insert the KPI Block.
           - Insert the STATS Block.
           - End with \\section*{{Visual Analysis}} and then \\end{{document}}.

        STRICT FORMATTING:
        - Escape all special characters: % as \\% and $ as \\$.
        - NO Markdown code blocks (no backticks).
        - NO conversational text. Output ONLY the LaTeX code starting from \\documentclass.
        """
        # We use .strip() to remove any accidental leading/trailing whitespace
        return call_ollama(self.model_name, prompt, is_json=False).strip()
    
import os
import subprocess
from typing import Dict, Any
from PyPDF2 import PdfReader, PdfWriter # Requires: pip install PyPDF2

def final_pdf(state: Dict[str, Any]):
    os.makedirs("output", exist_ok=True)
    report_sections = state.get('report_sections', {})
    narrative_data = report_sections.get('narrative', {})

    # Extract LaTeX string from the state dictionary
    latex_content = narrative_data.get('content', "") if isinstance(narrative_data, dict) else narrative_data

    # 1. Handle Image Injection to fix missing visualizations
    artifacts = state.get('artifacts', [])
    image_latex = ""
    if artifacts:
        # Check for existing header to prevent duplication
        if "\\section*{Visual Analysis}" not in latex_content:
            image_latex = "\n\\section*{Visual Analysis}\n"
        
        for img in artifacts:
            if os.path.exists(img):
                # Ensure paths are LaTeX-compatible absolute paths
                path = os.path.abspath(img).replace("\\", "/")
                image_latex += f"\\begin{{figure}}[h!]\\centering\\includegraphics[width=0.8\\textwidth]{{{path}}}\\end{{figure}}\n"

    # 2. Finalize LaTeX structure
    if "\\end{document}" in latex_content:
        latex_content = latex_content.replace("\\end{document}", f"{image_latex}\\end{{document}}")
    else:
        latex_content += f"\n{image_latex}\\end{{document}}"

    tex_path = os.path.join("output", "report.tex")
    pdf_path = os.path.join("output", "report.pdf")
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)

    try:
        # 3. Compile LaTeX twice to resolve layout and page numbering
        for _ in range(2):
            subprocess.run(["pdflatex", "-output-directory=output", "-interaction=nonstopmode", tex_path], check=True)

        # 4. Logic to delete the blank/malformed first page
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Only proceed if there are multiple pages to avoid an empty document
        if len(reader.pages) > 1:
            # Skip page index 0 (the blank page) and keep everything from page 1 onwards
            for page_num in range(1, len(reader.pages)):
                writer.add_page(reader.pages[page_num])
            
            # Overwrite the original PDF with the trimmed version
            with open(pdf_path, "wb") as f:
                writer.write(f)
            print(">>> Post-Processing Complete: Blank page 1 removed.")
        else:
            print(">>> Warning: PDF only has one page; skipping removal.")

        return os.path.abspath(pdf_path)

    except Exception as e:
        print(f">>> PDF Generation Error: {e}")
        return None
