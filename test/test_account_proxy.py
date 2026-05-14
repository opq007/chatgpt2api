"""
Test account-level proxy functionality
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.account_service import account_service
from services.openai_backend_api import OpenAIBackendAPI
from services.proxy_service import test_proxy


class TestAccountProxy(unittest.TestCase):
    """Test account-level proxy binding functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_token = "test_proxy_token_12345"
        self.test_proxy = "http://testuser:testpass@proxy.example.com:8080"
        self.test_proxy_socks5 = "socks5://testuser:testpass@proxy.example.com:1080"

    def test_account_proxy_field(self):
        """Test that account proxy field is properly stored and retrieved"""
        account_service.add_accounts([self.test_token])
        account = account_service.update_account(self.test_token, {"proxy": self.test_proxy})

        self.assertIsNotNone(account)
        self.assertEqual(account.get("proxy"), self.test_proxy)

        accounts = account_service.list_accounts()
        test_account = next((a for a in accounts if a.get("access_token") == self.test_token), None)
        self.assertIsNotNone(test_account)
        self.assertEqual(test_account.get("proxy"), self.test_proxy)

        account_service.delete_accounts([self.test_token])

    def test_account_proxy_normalization(self):
        """Test that proxy field is normalized (whitespace trimmed)"""
        account_service.add_accounts([self.test_token])

        proxy_with_spaces = f"  {self.test_proxy}  "
        account = account_service.update_account(self.test_token, {"proxy": proxy_with_spaces})

        self.assertIsNotNone(account)
        self.assertEqual(account.get("proxy"), self.test_proxy)

        account_service.delete_accounts([self.test_token])

    def test_account_proxy_none_handling(self):
        """Test that None proxy is handled correctly"""
        account_service.add_accounts([self.test_token])

        account_service.update_account(self.test_token, {"proxy": self.test_proxy})
        account = account_service.update_account(self.test_token, {"proxy": None})

        self.assertIsNotNone(account)
        self.assertIsNone(account.get("proxy"))

        account_service.delete_accounts([self.test_token])

    def test_openai_backend_api_account_proxy(self):
        """Test that OpenAIBackendAPI accepts and uses account proxy"""
        backend = OpenAIBackendAPI(
            access_token=self.test_token,
            account_proxy=self.test_proxy,
            global_proxy="http://global-proxy.example.com:8080"
        )

        self.assertEqual(backend.account_proxy, self.test_proxy)

        backend_no_account = OpenAIBackendAPI(
            access_token=self.test_token,
            global_proxy="http://global-proxy.example.com:8080"
        )

        self.assertIsNone(backend_no_account.account_proxy)

    def test_proxy_priority(self):
        """Test that account proxy takes priority over global proxy"""
        backend = OpenAIBackendAPI(
            access_token=self.test_token,
            account_proxy=self.test_proxy,
            global_proxy="http://global-proxy.example.com:8080"
        )

        self.assertEqual(backend.account_proxy, self.test_proxy)

    def test_socks5_proxy_support(self):
        """Test that SOCKS5 proxy format is supported"""
        account_service.add_accounts([self.test_token])

        account = account_service.update_account(self.test_token, {"proxy": self.test_proxy_socks5})

        self.assertIsNotNone(account)
        self.assertEqual(account.get("proxy"), self.test_proxy_socks5)

        account_service.delete_accounts([self.test_token])

    def test_proxy_field_in_account_list(self):
        """Test that proxy field appears in account list"""
        account_service.add_accounts([self.test_token])

        account_service.update_account(self.test_token, {"proxy": self.test_proxy})

        accounts = account_service.list_accounts()
        test_account = next((a for a in accounts if a.get("access_token") == self.test_token), None)

        self.assertIsNotNone(test_account)
        self.assertIn("proxy", test_account)
        self.assertEqual(test_account.get("proxy"), self.test_proxy)

        account_service.delete_accounts([self.test_token])

    def test_empty_proxy_string(self):
        """Test that empty proxy string is handled correctly"""
        account_service.add_accounts([self.test_token])

        account = account_service.update_account(self.test_token, {"proxy": ""})

        self.assertIsNotNone(account)

        account_service.delete_accounts([self.test_token])


if __name__ == "__main__":
    unittest.main()