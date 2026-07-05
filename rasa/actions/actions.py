"""
Rasa Custom Actions - Debt Collections Voice Bot
=================================================
Three action classes that call the Spring Boot REST API at localhost:8080.
The bot NEVER reads from the database directly.

Actions:
    ActionFetchAccount          — fetches account data and sets slots
    ActionValidateAndSavePTP    — validates PTP against business rules and saves
    ActionSaveFollowup          — auto-generates remarks and saves followup record
"""

from typing import Any, Dict, List, Optional, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import httpx
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8080/api/v1"
TIMEOUT_SECONDS = 5.0


def parse_date(text: str) -> Optional[str]:
    """Parse a date string in multiple formats and return ISO format (YYYY-MM-DD).

    Tries common formats first, then falls back to dateutil for natural language.
    Returns None if the date cannot be parsed.
    """
    from datetime import datetime

    formats = [
        "%Y-%m-%d",      # 2025-03-15
        "%d/%m/%Y",      # 15/03/2025
        "%d-%m-%Y",      # 15-03-2025
        "%m/%d/%Y",      # 03/15/2025
        "%d %B %Y",      # 15 March 2025
        "%d %b %Y",      # 15 Mar 2025
        "%d %B",         # 15 March (assumes current year)
        "%d %b",         # 15 Mar (assumes current year)
        "%B %d",         # March 15
        "%b %d",         # Mar 15
        "%d/%m/%y",      # 15/03/25
        "%d-%m-%y",      # 15-03-25
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(text.strip(), fmt)
            # If no year was in format, use current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.date().isoformat()
        except ValueError:
            continue

    # Fallback: try dateutil for natural language dates
    try:
        from dateutil.parser import parse
        parsed = parse(text, dayfirst=True)
        return parsed.date().isoformat()
    except Exception:
        pass

    # Fallback: handle relative dates like "5 days", "2 weeks"
    try:
        import re
        from datetime import timedelta

        text_lower = text.lower().strip()

        # "kal" = tomorrow (Hindi)
        if text_lower in ("kal", "tomorrow"):
            return (datetime.now() + timedelta(days=1)).date().isoformat()

        # "parson" = day after tomorrow (Hindi)
        if text_lower in ("parson", "day after tomorrow"):
            return (datetime.now() + timedelta(days=2)).date().isoformat()

        # "aaj" = today (Hindi)
        if text_lower in ("aaj", "today"):
            return datetime.now().date().isoformat()

        # "X din baad" / "in X days"
        days_match = re.search(r"(\d+)\s*(?:din|days?)\s*(?:baad|later)?", text_lower)
        if days_match:
            days = int(days_match.group(1))
            return (datetime.now() + timedelta(days=days)).date().isoformat()

        # "X hafte/weeks"
        weeks_match = re.search(r"(\d+)\s*(?:hafte|weeks?)\s*(?:baad|later)?", text_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return (datetime.now() + timedelta(weeks=weeks)).date().isoformat()

        # "next week"
        if "next week" in text_lower or "agle hafte" in text_lower:
            return (datetime.now() + timedelta(weeks=1)).date().isoformat()

        # "next month" / "agle mahine"
        if "next month" in text_lower or "agle mahine" in text_lower:
            return (datetime.now() + timedelta(days=30)).date().isoformat()

    except Exception:
        pass

    return None


def parse_amount(text: str) -> Optional[float]:
    """Extract a numeric amount from text.

    Handles formats like: '5000', '5,000', '5000 rupees', 'Rs. 5000'
    """
    import re

    if text is None:
        return None

    text = str(text).strip()

    # Try direct float conversion first
    try:
        return float(text)
    except ValueError:
        pass

    # Extract number from text
    # Remove common currency prefixes/suffixes
    cleaned = re.sub(r"[Rr]s\.?\s*", "", text)
    cleaned = re.sub(r"[₹$]", "", cleaned)
    cleaned = re.sub(r"\s*(rupees?|rupaye?|dollars?)\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        pass

    # Try to find any number in the string
    match = re.search(r"[\d,]+\.?\d*", text)
    if match:
        try:
            return float(match.group().replace(",", ""))
        except ValueError:
            pass

    return None


class ActionFetchAccount(Action):
    """Fetches account data from Spring Boot API and sets all relevant slots."""

    def name(self) -> Text:
        return "action_fetch_account"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        account_number = tracker.get_slot("account_number")

        if not account_number:
            dispatcher.utter_message(text="Kripya apna account number batayein.")
            return []

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(f"{API_BASE_URL}/accounts/{account_number}")

            if response.status_code == 200:
                account_data = response.json()
                logger.info(f"Account {account_number} loaded successfully.")
                return [
                    SlotSet("account_id", float(account_data.get("accountId", 0))),
                    SlotSet("customer_name", account_data.get("customerName")),
                    SlotSet("overdue_amount", float(account_data.get("overdueAmount", 0))),
                    SlotSet("charges", float(account_data.get("charges", 0))),
                    SlotSet("last_emi_date", account_data.get("lastEmiDate")),
                    SlotSet("last_payment_amount", float(account_data.get("lastPaymentAmount", 0))),
                    SlotSet("last_payment_date", account_data.get("lastPaymentDate")),
                ]

            if response.status_code == 404:
                dispatcher.utter_message(response="utter_account_not_found")
                return []

            dispatcher.utter_message(text=f"Account service returned {response.status_code}.")
            return []

        except httpx.RequestError as exc:
            logger.error(f"Account service unavailable: {exc}")
            dispatcher.utter_message(text="Account service is unavailable. Kripya thodi der baad koshish karein.")
            return []


class ActionValidateAndSavePTP(Action):
    """Validates PTP against business rules from promise_policy and saves if valid."""

    def name(self) -> Text:
        return "action_validate_and_save_ptp"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        ptp_date_raw  = tracker.get_slot("ptp_date")
        ptp_amount_raw = tracker.get_slot("ptp_amount")
        account_id    = tracker.get_slot("account_id")
        overdue_amount = tracker.get_slot("overdue_amount") or 0
        followup_id   = tracker.get_slot("followup_id")

        logger.info(
            "ActionValidateAndSavePTP: date=%s amount=%s account=%s followup=%s",
            ptp_date_raw, ptp_amount_raw, account_id, followup_id,
        )

        if not account_id:
            dispatcher.utter_message(text="Account information missing. Kripya pehle account verify karein.")
            return []

        # --- Smart slot-aware dispatch -----------------------------------------
        both_set = bool(ptp_date_raw and ptp_amount_raw)
        only_date    = bool(ptp_date_raw and not ptp_amount_raw)
        only_amount  = bool(ptp_amount_raw and not ptp_date_raw)

        if only_amount:
            logger.info("PTP: only amount set (%.2f) - prompting for date", ptp_amount_raw)
            dispatcher.utter_message(response="utter_ask_ptp_date")
            return []

        if only_date:
            logger.info("PTP: only date set (%s) - prompting for amount", ptp_date_raw)
            dispatcher.utter_message(response="utter_ask_ptp_amount")
            return []

        if not both_set:
            logger.info("PTP: neither set - prompting for both")
            dispatcher.utter_message(text="Kripya payment ki date aur amount dono batayein.")
            return []

        # --- Both slots are set: validate and save -----------------------------
        parsed_date = parse_date(str(ptp_date_raw))
        if parsed_date is None:
            dispatcher.utter_message(response="utter_date_invalid")
            return [SlotSet("ptp_date", None)]

        ptp_amount = parse_amount(str(ptp_amount_raw))
        if ptp_amount is None:
            dispatcher.utter_message(text="Amount samajh nahi aaya. Kripya sirf number mein batayein.")
            return [SlotSet("ptp_amount", None)]

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                policy_response = await client.get(f"{API_BASE_URL}/promise-policy")

                if policy_response.status_code != 200:
                    dispatcher.utter_message(text="Promise policy service is unavailable.")
                    return []

                policy = policy_response.json()
                max_days   = int(policy.get("maxPromiseDays", 30))
                min_percent = float(policy.get("minPromisePercent", 25.0))

                from datetime import date as dt_date, datetime as dt_datetime
                today   = dt_date.today()
                promised = dt_datetime.fromisoformat(parsed_date).date()

                days_diff = (promised - today).days
                if days_diff > max_days:
                    dispatcher.utter_message(
                        text=f"Promise date should be within {max_days} days from today. "
                        f"You selected a date {days_diff} days away."
                    )
                    return [SlotSet("ptp_date", None)]

                if days_diff < 0:
                    dispatcher.utter_message(text="Promise date cannot be in the past. Kripya aaj ya future ka date batayein.")
                    return [SlotSet("ptp_date", None)]

                min_amount = float(overdue_amount) * (min_percent / 100.0)
                if ptp_amount < min_amount:
                    dispatcher.utter_message(
                        text=f"Minimum payment should be {min_amount:.2f} rupees "
                        f"({min_percent:.0f}% of {float(overdue_amount):.2f} overdue)."
                    )
                    return [SlotSet("ptp_amount", None)]

                # Create followup before saving promise
                if not followup_id:
                    try:
                        fu_resp = await client.post(
                            f"{API_BASE_URL}/followup",
                            json={
                                "accountId": int(account_id),
                                "remarks": (
                                    f"Promise to pay captured: {ptp_amount} by {parsed_date}. "
                                    f"Overdue: {overdue_amount}."
                                ),
                            },
                        )
                        if fu_resp.status_code == 200:
                            followup_id = fu_resp.json().get("followupId")
                            logger.info("Followup created: id=%s", followup_id)
                    except httpx.RequestError:
                        logger.warning("Could not create followup, continuing without it.")

                payload = {
                    "accountId": int(account_id),
                    "followupId": int(followup_id) if followup_id else None,
                    "promiseAmount": ptp_amount,
                    "promiseDate": parsed_date,
                }
                logger.info("POSTing promise payload: %s", payload)
                save_response = await client.post(f"{API_BASE_URL}/promise", json=payload)
                logger.info("Promise POST response: %s", save_response.status_code)

            if save_response.status_code == 200:
                saved = save_response.json()
                logger.info("PTP saved: account=%s amount=%s date=%s followup_id=%s",
                            account_id, ptp_amount, parsed_date, followup_id)
                dispatcher.utter_message(response="utter_ptp_saved")
                return [
                    SlotSet("ptp_saved", True),
                    SlotSet("followup_id", followup_id),
                ]

            if save_response.status_code == 400:
                error_data = save_response.json()
                dispatcher.utter_message(text=error_data.get("error", "PTP validation failed."))
                return []

            dispatcher.utter_message(text="Unable to save promise at this time.")
            return []

        except httpx.RequestError as exc:
            logger.error(f"PTP API unavailable: {exc}")
            dispatcher.utter_message(text="Unable to validate PTP because the API is unavailable.")
            return []


class ActionSaveFollowup(Action):
    """Auto-generates remarks based on call context and saves followup record."""

    def name(self) -> Text:
        return "action_save_followup"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        account_id = tracker.get_slot("account_id")
        ptp_saved = tracker.get_slot("ptp_saved") or False
        ptp_amount = tracker.get_slot("ptp_amount")
        ptp_date = tracker.get_slot("ptp_date")
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        if not account_id:
            dispatcher.utter_message(text="Account information missing. Kripya pehle account number batayein.")
            return []

        # Build contextual remarks based on the conversation outcome
        if last_intent == "dispute":
            remarks = (
                f"Customer disputed the amount. PTP captured: {ptp_saved}. "
                f"Requires human agent review. Escalated."
            )
        elif last_intent == "request_callback":
            remarks = (
                f"Customer requested callback. PTP captured: {ptp_saved}. "
                f"Will schedule callback."
            )
        elif last_intent == "deny_ptp":
            remarks = (
                f"Customer denied PTP. PTP captured: {ptp_saved}. "
                f"Will continue collection process."
            )
        elif last_intent == "goodbye" and ptp_saved:
            remarks = (
                f"Call completed successfully. PTP captured: True. "
                f"Promise: {ptp_amount} by {ptp_date}."
            )
        elif last_intent == "goodbye":
            remarks = f"Call completed. PTP captured: {ptp_saved}. Customer said goodbye."
        else:
            remarks = f"Call completed. PTP captured: {ptp_saved}. Last intent: {last_intent}."

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{API_BASE_URL}/followup",
                    json={"accountId": int(account_id), "remarks": remarks},
                )

            if response.status_code == 200:
                saved = response.json()
                logger.info(f"Followup saved: id={saved.get('followupId')}, account={account_id}")
                return [SlotSet("followup_id", float(saved.get("followupId", 0)))]

            dispatcher.utter_message(text="Unable to save followup record.")
            return []

        except httpx.RequestError as exc:
            logger.error(f"Followup API unavailable: {exc}")
            dispatcher.utter_message(text="Unable to connect to the followup service.")
            return []
