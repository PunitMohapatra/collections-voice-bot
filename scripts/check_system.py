import os
import socket
import sys
from pathlib import Path

# Try to import requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import json
    HAS_REQUESTS = False

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(service_name, is_ok, details=""):
    status_str = f"{Colors.GREEN}[PASS]{Colors.RESET}" if is_ok else f"{Colors.RED}[FAIL]{Colors.RESET}"
    detail_str = f" ({details})" if details else ""
    print(f"  {status_str} {service_name}{detail_str}")

def check_port(host, port):
    try:
        with socket.create_connection((host, port), timeout=2.0):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def http_get(url):
    if HAS_REQUESTS:
        try:
            resp = requests.get(url, timeout=3.0)
            return resp.status_code, resp.text
        except Exception:
            return None, ""
    else:
        try:
            with urllib.request.urlopen(url, timeout=3.0) as response:
                return response.status, response.read().decode('utf-8')
        except Exception:
            return None, ""

def main():
    print("=" * 60)
    print(f"{Colors.BOLD}{Colors.CYAN}Debt Collections Voice Bot - System Health Check{Colors.RESET}")
    print("=" * 60)

    all_pass = True

    # 1. PostgreSQL Check
    pg_ok = check_port("localhost", 5432)
    print_status("PostgreSQL (Port 5432)", pg_ok, "Running" if pg_ok else "Not reachable")
    if not pg_ok:
        all_pass = False

    # 2. Spring Boot API Check
    spring_status = False
    spring_details = "Not reachable"
    spring_code, spring_text = http_get("http://localhost:8080/api/v1/accounts/LN001")
    if spring_code == 200:
        spring_status = True
        spring_details = "Available & responding correctly"
    elif spring_code:
        spring_details = f"Server responded with status {spring_code}"
    
    print_status("Spring Boot REST API (Port 8080)", spring_status, spring_details)
    if not spring_status:
        all_pass = False

    # 3. Rasa Server Check
    rasa_status = False
    rasa_details = "Not reachable"
    rasa_code, rasa_text = http_get("http://localhost:5005/status")
    if rasa_code == 200:
        rasa_status = True
        rasa_details = "Dialogue engine active"
    elif rasa_code:
        rasa_details = f"Server responded with status {rasa_code}"
        
    print_status("Rasa Dialogue Server (Port 5005)", rasa_status, rasa_details)
    if not rasa_status:
        all_pass = False

    # 4. Rasa Action Server Check
    action_ok = check_port("localhost", 5055)
    print_status("Rasa Action Server (Port 5055)", action_ok, "Running" if action_ok else "Not reachable")
    if not action_ok:
        all_pass = False

    # 5. FastAPI Bot Server Check
    fastapi_status = False
    fastapi_details = "Not reachable"
    fastapi_code, fastapi_text = http_get("http://localhost:8000/health")
    if fastapi_code == 200:
        fastapi_status = True
        fastapi_details = "Orchestrator active"
    elif fastapi_code:
        fastapi_details = f"Server responded with status {fastapi_code}"
        
    print_status("FastAPI Bot Server (Port 8000)", fastapi_status, fastapi_details)
    if not fastapi_status:
        all_pass = False

    # 6. Check Model Files
    print(f"\n{Colors.BOLD}Model Files Verification:{Colors.RESET}")
    base_dir = Path(__file__).resolve().parent.parent / "bot"
    
    hi_voice_path = base_dir / "models" / "hi" / "hi_IN" / "rohan" / "medium" / "hi_IN-rohan-medium.onnx"
    en_voice_path = base_dir / "models" / "en" / "en_US" / "amy" / "low" / "en_US-amy-low.onnx"
    
    hi_exists = hi_voice_path.exists()
    en_exists = en_voice_path.exists()
    
    print_status("Piper Hindi Voice Model (hi_IN-rohan-medium.onnx)", hi_exists, "Found" if hi_exists else "Missing")
    print_status("Piper English Voice Model (en_US-amy-low.onnx)", en_exists, "Found" if en_exists else "Missing")
    
    if not hi_exists or not en_exists:
        all_pass = False
        print(f"\n{Colors.YELLOW}[TIP] Download missing voice models to 'bot/models/' directory.{Colors.RESET}")

    print("=" * 60)
    if all_pass:
        print(f"{Colors.GREEN}{Colors.BOLD}SYSTEM STATUS: Healthy & Ready for Calls!{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}SYSTEM STATUS: Some components are down or missing. Check details above.{Colors.RESET}")
    print("=" * 60)

if __name__ == "__main__":
    main()
