import subprocess
import sys
from logger import log_event, Colors

def execute_command(command: str):
    """Executes a shell command and returns the output."""
    log_event(f"Executing CLI Command: {command}", Colors.BLUE)
    try:
        # shell=True allows for standard CLI commands (pip, ls, etc.)
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode == 0:
            log_event("Command executed successfully.", Colors.GREEN)
            return result.stdout
        else:
            log_event(f"Command failed: {result.stderr}", Colors.RED)
            return f"Error: {result.stderr}"
            
    except Exception as e:
        log_event(f"Execution Exception: {str(e)}", Colors.RED)
        return str(e)