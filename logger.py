import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

# 1. Constants and Color Mapping
class LogColors:
    HEADER = '\033[95m'
    INFO = '\033[94m'    # Blue
    SUCCESS = '\033[92m' # Green
    WARNING = '\033[93m' # Yellow
    ERROR = '\033[91m'   # Red
    RESET = '\033[0m'

class AgentLogger:
    """
    Thread-safe, high-performance logger for LLM Orchestration.
    Centralizes file I/O and console formatting.
    """
    _instance = None

    def __new__(cls):
        """Singleton pattern to prevent redundant log handlers."""
        if cls._instance is None:
            cls._instance = super(AgentLogger, cls).__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Standard Python Logger Setup
        self.logger = logging.getLogger("AgentFramework")
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers if setup is called twice
        if not self.logger.handlers:
            # File Handler (Daily Logs)
            log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def _format_terminal(self, node_name: str, message: str, color: str) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"{LogColors.INFO}[{timestamp}]{LogColors.RESET} {LogColors.HEADER}{node_name:15}{LogColors.RESET} | {color}{message}{LogColors.RESET}"

    def log_interaction(self, node_name: str, prompt: str, response: str, is_error: bool = False):
        """Logs detailed LLM input/output to file and summary to console."""
        
        # 1. Prepare Persistent File Log (Full Detail)
        log_detail = (
            f"\n{'='*20} NODE: {node_name} {'='*20}\n"
            f"PROMPT: {prompt.strip()}\n"
            f"RESPONSE: {response.strip()}\n"
            f"{'='*50}"
        )
        
        if is_error:
            self.logger.error(log_detail)
            console_msg = self._format_terminal(node_name, "✖ LLM Error - Check logs for detail", LogColors.ERROR)
        else:
            self.logger.info(log_detail)
            # Snippet for console
            snippet = response.replace('\n', ' ')[:75] + "..." if len(response) > 75 else response
            console_msg = self._format_terminal(node_name, f"✔ {snippet}", LogColors.SUCCESS)
        
        print(console_msg)

    def log_event(self, message: str, level: str = "INFO"):
        """Logs general system events."""
        color_map = {
            "INFO": LogColors.INFO,
            "SUCCESS": LogColors.SUCCESS,
            "WARNING": LogColors.WARNING,
            "ERROR": LogColors.ERROR
        }
        
        color = color_map.get(level.upper(), LogColors.RESET)
        
        # Log to file
        self.logger.info(f"EVENT: {message}")
        
        # Print to console
        print(f"{color}>>> {message}{LogColors.RESET}")

# 2. Global convenience instance
agent_logger = AgentLogger()