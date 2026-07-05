import requests
import sys

BOT_URL = "http://localhost:8000"
SPRING_API_URL = "http://localhost:8080/api/v1"
DEFAULT_ACCOUNT = "LN001"

def build_local_greeting(account: dict) -> str:
    name = account.get("customerName", "customer")
    overdue = account.get("overdueAmount", 0)
    charges = account.get("charges", 0)
    language = account.get("preferredLanguage", "en")

    if language == "hi":
        return (
            f"Namaste, kya main {name} ji se baat kar sakta hoon? "
            f"Aapke loan account par {overdue} rupaye baaki hain aur {charges} rupaye ke charges hain. "
            f"Aap kab tak payment kar sakte hain?"
        )

    return (
        f"Hello, am I speaking with {name}? "
        f"Your loan account has an overdue amount of {overdue} rupees "
        f"with additional charges of {charges} rupees. "
        f"When would you be able to make this payment?"
    )

def main():
    print("=" * 60)
    print("Debt Collections Voice Bot - Text Client Simulator")
    print("=" * 60)

    account_num = input(f"Enter account number to call (default: {DEFAULT_ACCOUNT}): ").strip()
    if not account_num:
        account_num = DEFAULT_ACCOUNT

    # 1. Start Call
    print(f"\nInitializing call for account {account_num} via /call/start...")
    try:
        start_resp = requests.post(f"{BOT_URL}/call/start?account_number={account_num}")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to FastAPI server at {BOT_URL}. Is it running?")
        return

    if start_resp.status_code != 200:
        print(f"Failed to start call. Status: {start_resp.status_code}, Detail: {start_resp.text}")
        return

    # 2. Fetch account details directly from Spring Boot to display greeting
    print("Fetching account details for local transcript...")
    try:
        acc_resp = requests.get(f"{SPRING_API_URL}/accounts/{account_num}")
        if acc_resp.status_code == 200:
            account_data = acc_resp.json()
            greeting = build_local_greeting(account_data)
            print(f"\n[Bot]: {greeting}")
        else:
            print("\n[Bot]: Hello! (Could not fetch account details for custom greeting)")
    except Exception:
        print("\n[Bot]: Hello! (Could not fetch account details for custom greeting)")

    # 3. Conversation Loop
    while True:
        try:
            user_input = input("\n[User] (type 'q' to end): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_input:
            continue

        if user_input.lower() == 'q':
            print("Ending call...")
            break

        # Send text message to FastAPI text endpoint
        try:
            resp = requests.post(
                f"{BOT_URL}/call/message/text?account_number={account_num}&message={user_input}"
            )
            if resp.status_code == 200:
                bot_resp = resp.json().get("response", "")
                print(f"[Bot]: {bot_resp}")
            else:
                print(f"Error from bot server: {resp.status_code} - {resp.text}")
                break
        except Exception as e:
            print(f"Failed to send message: {e}")
            break

    # 4. End Call and print outcomes
    print("\nFinalizing call via /call/end...")
    try:
        end_resp = requests.post(f"{BOT_URL}/call/end?account_number={account_num}")
        if end_resp.status_code == 200:
            result = end_resp.json()
            print("=" * 60)
            print("Call Log Summary:")
            print(f"  Final Status: {result.get('status')}")
            print(f"  PTP Captured: {result.get('ptp_captured')}")
            print(f"  Escalated:    {result.get('escalated')}")
            print("=" * 60)
        else:
            print(f"Failed to end call properly: {end_resp.status_code}, {end_resp.text}")
    except Exception as e:
        print(f"Error ending call: {e}")

if __name__ == "__main__":
    main()
