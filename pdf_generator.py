import os
import logging
from typing import Optional, List, Any, Dict
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch

# Initialize logging
logger = logging.getLogger("ReportBuilder")

class ReportGenerator:
    """Handles the transformation of AgentState into a professional PDF report."""
    
    def __init__(self, output_path: str = "output/Data_Analysis_Report.pdf"):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        directory = os.path.dirname(self.output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def _sanitize_text(text: Any) -> str:
        """Escapes XML and handles non-string types safely."""
        if not text:
            return ""
        if isinstance(text, dict):
            return " | ".join([f"<b>{k}:</b> {v}" for k, v in text.items()])
        
        # Standard XML escaping for ReportLab
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _create_image(self, img_path: str) -> Optional[Image]:
        """Loads and scales images while maintaining aspect ratio."""
        if not os.path.exists(img_path):
            logger.warning(f"Image path does not exist: {img_path}")
            return None
        
        try:
            # Set a max width of 6 inches for the letter size page
            img = Image(img_path)
            aspect = img.imageHeight / float(img.imageWidth)
            img.drawWidth = 6 * inch
            img.drawHeight = (6 * inch) * aspect
            return img
        except Exception as e:
            logger.error(f"Failed to process image {img_path}: {e}")
            return None

    def build(self, state: Dict[str, Any]) -> Optional[str]:
        """Main method to compile the PDF from the agent state."""
        try:
            doc = SimpleDocTemplate(self.output_path, pagesize=letter)
            story = []

            # 1. Title Section
            story.append(Paragraph("Automated Data Analysis Report", self.styles['Title']))
            story.append(Spacer(1, 0.25 * inch))

            # 2. Executive Summary
            narrative = state.get('report_sections', {}).get('narrative', {})
            title = self._sanitize_text(narrative.get('title', 'Executive Summary'))
            summary = self._sanitize_text(narrative.get('summary', 'No summary provided.'))
            
            story.append(Paragraph(title, self.styles['Heading2']))
            story.append(Paragraph(summary, self.styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

            # 3. Data Insights (KPIs & Stats)
            sections = [
                ("Key Performance Indicators", 'kpis'),
                ("Statistical Insights", 'stats')
            ]

            for header, key in sections:
                story.append(Paragraph(header, self.styles['Heading3']))
                content = state.get('report_sections', {}).get(key, f"No {header.lower()} available.")
                story.append(Paragraph(self._sanitize_text(content), self.styles['Normal']))
                story.append(Spacer(1, 0.2 * inch))

            # 4. Visualizations
            artifacts = state.get('artifacts', [])
            if artifacts:
                story.append(Paragraph("Visualizations", self.styles['Heading3']))
                for img_path in artifacts:
                    # Handle potential list nesting from previous agent outputs
                    path = img_path[0] if isinstance(img_path, list) else img_path
                    img_widget = self._create_image(path)
                    if img_widget:
                        story.append(Spacer(1, 0.1 * inch))
                        story.append(img_widget)
                        story.append(Spacer(1, 0.2 * inch))

            doc.build(story)
            logger.info(f"Report successfully generated at: {self.output_path}")
            return self.output_path

        except Exception as e:
            logger.critical(f"Critical failure building PDF: {e}", exc_info=True)
            return None

def build_report_factory(state: Dict[str, Any], output_path: str = "output/report.pdf"):
    """Functional wrapper for backward compatibility with your existing workflow."""
    generator = ReportGenerator(output_path)
    return generator.build(state)