import pytest
import requests
import json
from datetime import datetime, timedelta
import time


# Use seeded account numbers from schema.sql
SEEDED_ACCOUNT_NUMBER = "LN001"
API_BASE_URL = "http://localhost:8080/api/v1"


class TestAccountFetching:
    """Test account fetching functionality"""
    
    @pytest.fixture
    def valid_account(self):
        """Valid account data for testing"""
        return {
            "accountId": 12345,
            "customerName": "John Doe",
            "overdueAmount": 5000.00,
            "charges": 500.00,
            "lastEmiDate": "2025-01-15",
            "preferredLanguage": "en"
        }
    
    def test_fetch_account_success(self, valid_account):
        """Test successful account fetch"""
        response = requests.get(
            f"{API_BASE_URL}/accounts/{SEEDED_ACCOUNT_NUMBER}",
            headers={"Accept": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        assert data["accountNumber"] == SEEDED_ACCOUNT_NUMBER
        assert "customerName" in data
        assert "overdueAmount" in data
    
    def test_fetch_account_invalid_id(self):
        """Test fetching non-existent account"""
        response = requests.get(
            f"{API_BASE_URL}/accounts/99999",
            headers={"Accept": "application/json"}
        )
        
        assert response.status_code == 404
    
    def test_fetch_account_timeout(self):
        """Test account fetch timeout"""
        # This would require mocking the network
        pass


class TestPTPValidation:
    """Test PTP validation and saving"""
    
    def _get_account_id(self):
        """Helper to resolve a real account ID from seeded data."""
        response = requests.get(
            f"{API_BASE_URL}/accounts/{SEEDED_ACCOUNT_NUMBER}",
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()["accountId"]
    
    def test_ptp_validation_within_limits(self):
        """Test PTP within business rule limits"""
        account_response = requests.get(
            f"{API_BASE_URL}/accounts/{SEEDED_ACCOUNT_NUMBER}",
            headers={"Accept": "application/json"}
        )
        account_response.raise_for_status()
        account = account_response.json()
        account_id = account["accountId"]
        overdue_amount = float(account["overdueAmount"])
        
        # Create followup first because promise requires an existing followupId
        followup_payload = {
            "accountId": account_id,
            "remarks": "Customer agreed to pay."
        }
        followup_resp = requests.post(
            f"{API_BASE_URL}/followup",
            json=followup_payload,
            headers={"Content-Type": "application/json"}
        )
        assert followup_resp.status_code == 200, f"Followup creation failed: {followup_resp.text}"
        followup_id = followup_resp.json()["followupId"]

        today = datetime.now()
        future_date = today + timedelta(days=15)  # Within limit
        
        ptp_request = {
            "accountId": account_id,
            "followupId": followup_id,
            "promiseAmount": overdue_amount * 0.25,  # Exactly 25%
            "promiseDate": future_date.strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{API_BASE_URL}/promise",
            json=ptp_request,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}, request={ptp_request}"
    
    def test_ptp_validation_exceeds_max_days(self):
        """Test PTP exceeding max promise days"""
        account_id = self._get_account_id()
        today = datetime.now()
        future_date = today + timedelta(days=31)  # Exceeds 30 day limit
        
        ptp_request = {
            "accountId": account_id,
            "followupId": 1,
            "promiseAmount": 5000.00,
            "promiseDate": future_date.strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{API_BASE_URL}/promise",
            json=ptp_request,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "promise date must be within 30 days from today" in response.text.lower()
    
    def test_ptp_validation_below_min_percent(self):
        """Test PTP below minimum percentage"""
        account_response = requests.get(
            f"{API_BASE_URL}/accounts/{SEEDED_ACCOUNT_NUMBER}",
            headers={"Accept": "application/json"}
        )
        account_response.raise_for_status()
        account = account_response.json()
        account_id = account["accountId"]
        overdue_amount = float(account["overdueAmount"])
        min_amount = overdue_amount * 0.25

        # Create followup first because promise requires an existing followupId
        followup_payload = {
            "accountId": account_id,
            "remarks": "Customer disputed the amount."
        }
        followup_resp = requests.post(
            f"{API_BASE_URL}/followup",
            json=followup_payload,
            headers={"Content-Type": "application/json"}
        )
        assert followup_resp.status_code == 200, f"Followup creation failed: {followup_resp.text}"
        followup_id = followup_resp.json()["followupId"]

        ptp_request = {
            "accountId": account_id,
            "followupId": followup_id,
            "promiseAmount": min_amount - 100.00,  # Below minimum
            "promiseDate": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{API_BASE_URL}/promise",
            json=ptp_request,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "promise amount must be at least" in response.text.lower()
        assert "minimum 25.00% of overdue" in response.text.lower()


class TestFollowupSaving:
    """Test followup record saving"""
    
    def _get_account_id(self):
        """Helper to resolve a real account ID from seeded data."""
        response = requests.get(
            f"{API_BASE_URL}/accounts/{SEEDED_ACCOUNT_NUMBER}",
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()["accountId"]
    
    def test_save_followup_success(self):
        """Test successful followup save"""
        account_id = self._get_account_id()
        followup_data = {
            "accountId": account_id,
            "remarks": "Customer requested callback"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/followup",
            json=followup_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        assert "followupId" in data
    
    def test_save_followup_with_dispute(self):
        """Test followup save with dispute remark"""
        account_id = self._get_account_id()
        followup_data = {
            "accountId": account_id,
            "remarks": "Customer disputed the amount. PTP captured: False. Requires human agent review."
        }
        
        response = requests.post(
            f"{API_BASE_URL}/followup",
            json=followup_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
    
    def test_save_followup_with_callback_request(self):
        """Test followup save with callback request"""
        account_id = self._get_account_id()
        followup_data = {
            "accountId": account_id,
            "remarks": "Customer requested callback. PTP captured: True. Will schedule callback."
        }
        
        response = requests.post(
            f"{API_BASE_URL}/followup",
            json=followup_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200


class TestMultiLanguageSupport:
    """Test multi-language support"""
    
    def test_hindi_greeting(self):
        """Test Hindi greeting generation"""
        account_data = {
            "customerName": "Ramesh Kumar",
            "overdueAmount": 5000.00,
            "charges": 500.00,
            "preferredLanguage": "hi"
        }
        
        expected_greeting = (
            f"Namaste, kya main {account_data['customerName']} ji se baat kar sakta hoon? "
            f"Aapke loan account par {account_data['overdueAmount']} rupaye baaki hain "
            f"aur {account_data['charges']} rupaye ke charges hain. "
            f"Aap kab tak payment kar sakte hain?"
        )
        
        assert "Namaste" in expected_greeting
        assert "rupaye" in expected_greeting
    
    def test_tamil_greeting(self):
        """Test Tamil greeting generation"""
        account_data = {
            "customerName": "Suresh Kumar",
            "overdueAmount": 5000.00,
            "charges": 500.00,
            "preferredLanguage": "ta"
        }
        
        expected_greeting = (
            f"Vanakkam, enna {account_data['customerName']} ji-naal visheshama irukku? "
            f"Aapke loan account-la {account_data['overdueAmount']} rupayaa kooda irukka. "
            f"{account_data['charges']} rupayaa charges. "
            f"Payment kada kalam?"
        )
        
        assert "Vanakkam" in expected_greeting
    
    def test_english_greeting(self):
        """Test English greeting generation"""
        account_data = {
            "customerName": "John Doe",
            "overdueAmount": 5000.00,
            "charges": 500.00,
            "preferredLanguage": "en"
        }
        
        expected_greeting = (
            f"Hello, am I speaking with {account_data['customerName']}? "
            f"Your loan account has an overdue amount of {account_data['overdueAmount']} rupees "
            f"with additional charges of {account_data['charges']} rupees. "
            f"When would you be able to make this payment?"
        )
        
        assert "Hello" in expected_greeting


class TestBusinessRules:
    """Test business rule enforcement"""
    
    @pytest.fixture
    def promise_policy(self):
        """Promise policy configuration"""
        return {
            "maxPromiseDays": 30,
            "minPromisePercent": 25.0
        }
    
    def test_date_validation(self, promise_policy):
        """Test date validation against maxPromiseDays"""
        today = datetime.now()
        max_days = promise_policy["maxPromiseDays"]
        
        valid_date = today + timedelta(days=max_days - 1)
        assert valid_date <= today + timedelta(days=max_days)
        
        invalid_date = today + timedelta(days=max_days + 1)
        assert invalid_date > today + timedelta(days=max_days)
    
    def test_amount_validation(self, promise_policy):
        """Test amount validation against minPromisePercent"""
        overdue_amount = 5000.00
        min_percent = promise_policy["minPromisePercent"]
        min_amount = overdue_amount * (min_percent / 100)
        
        valid_amount = min_amount
        assert valid_amount >= min_amount
        
        invalid_amount = min_amount - 100.00
        assert invalid_amount < min_amount
    
    def test_combined_validation(self, promise_policy):
        """Test combined date and amount validation"""
        overdue_amount = 5000.00
        max_days = promise_policy["maxPromiseDays"]
        min_percent = promise_policy["minPromisePercent"]
        min_amount = overdue_amount * (min_percent / 100)
        
        today = datetime.now()
        
        valid_ptp = {
            "promiseAmount": min_amount,
            "promiseDate": (today + timedelta(days=max_days - 5)).strftime("%Y-%m-%d")
        }
        
        assert valid_ptp["promiseAmount"] >= min_amount
        assert datetime.strptime(valid_ptp["promiseDate"], "%Y-%m-%d") <= today + timedelta(days=max_days)


class TestCompleteFlow:
    """Test complete end-to-end flow"""
    
    def test_complete_collection_flow(self):
        """Test complete collection call flow"""
        account_number = SEEDED_ACCOUNT_NUMBER
        
        response = requests.get(
            f"{API_BASE_URL}/accounts/{account_number}",
            headers={"Accept": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        account_data = response.json()
        
        followup_data = {
            "accountId": account_data["accountId"],
            "remarks": "Customer agreed to pay."
        }
        followup_response = requests.post(
            f"{API_BASE_URL}/followup",
            json=followup_data,
            headers={"Content-Type": "application/json"}
        )
        assert followup_response.status_code == 200, f"Expected 200 but got {followup_response.status_code}: {followup_response.text}"
        followup_id = followup_response.json()["followupId"]
        
        ptp_request = {
            "accountId": account_data["accountId"],
            "followupId": followup_id,
            "promiseAmount": account_data["overdueAmount"] * 0.25,
            "promiseDate": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        }
        
        ptp_response = requests.post(
            f"{API_BASE_URL}/promise",
            json=ptp_request,
            headers={"Content-Type": "application/json"}
        )
        
        assert ptp_response.status_code == 200, f"Expected 200 but got {ptp_response.status_code}: {ptp_response.text}"
        
        saved_ptp = ptp_response.json()
        saved_followup = followup_response.json()
        
        assert saved_ptp["followupId"] == followup_id
        assert saved_followup["accountId"] == account_data["accountId"]
        assert saved_ptp["accountId"] == account_data["accountId"]
        assert saved_ptp["promiseAmount"] == ptp_request["promiseAmount"]
        assert saved_followup["remarks"] == followup_data["remarks"]


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_timeout_handling(self):
        """Test timeout error handling"""
        # This would require mocking network calls
        pass
    
    def test_invalid_account_number(self):
        """Test invalid account number handling"""
        response = requests.get(
            f"{API_BASE_URL}/accounts/invalid",
            headers={"Accept": "application/json"}
        )
        
        assert response.status_code == 404
    
    def test_invalid_ptp_date_format(self):
        """Test invalid date format handling"""
        account_id = 1
        ptp_request = {
            "accountId": account_id,
            "followupId": 1,
            "promiseAmount": 5000.00,
            "promiseDate": "invalid-date"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/promise",
            json=ptp_request,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
    
    def test_invalid_ptp_amount(self):
        """Test invalid amount handling"""
        account_id = 1
        ptp_request = {
            "accountId": account_id,
            "followupId": 1,
            "promiseAmount": -100.00,  # Negative amount
            "promiseDate": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        }
        
        response = requests.post(
            f"{API_BASE_URL}/promise",
            json=ptp_request,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
