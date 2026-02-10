import requests
import json
import re
import subprocess
import time
from functools import wraps

OLLAMA_URL = "http://172.22.124.89:11434/api/generate"
MODEL = "gemma3" # Replace with your model name

def retry_llm_call(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                    if result and result.strip():
                        return result
                except Exception:
                    pass
                retries += 1
                time.sleep(current_delay)
                current_delay *= 2
            return ""
        return wrapper
    return decorator

@retry_llm_call()
def call_ollama(node_name, prompt, is_json=True):
    payload = {"model": MODEL, "prompt": prompt, "stream": True, "options": {"temperature": 0.1}}
    if is_json: payload["format"] = "json"
    response = requests.post(OLLAMA_URL, json=payload, timeout=90)
    return response.json().get("response", "").strip()

def safe_json_load(text, fallback):
    try:
        return json.loads(text)
    except:
        return fallback

def extract_code(text):
    code_match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    return code_match.group(1) if code_match else text

def execute_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout