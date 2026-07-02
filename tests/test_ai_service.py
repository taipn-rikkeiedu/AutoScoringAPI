import unittest
from unittest.mock import patch, Mock
from core.ai_service import AIService
from core.settings import Settings

class AIServiceTest(unittest.TestCase):
    @patch("core.settings.Settings.GEMINI_API_KEY", "")
    def test_validation_fails_when_gemini_key_missing(self):
        with self.assertRaises(ValueError) as context:
            AIService(config={"provider": "gemini", "api_key": ""})
        self.assertIn("Thiếu GEMINI_API_KEY", str(context.exception))

    @patch("core.settings.Settings.GEMINI_API_KEY", "dummy-key")
    def test_validation_passes_when_gemini_key_in_settings(self):
        # Should not raise ValueError
        service = AIService(config={"provider": "gemini"})
        self.assertEqual(service.api_key, "dummy-key")

    def test_validation_passes_when_gemini_key_provided_in_config(self):
        # Should not raise ValueError even if settings has no key
        with patch("core.settings.Settings.GEMINI_API_KEY", ""):
            service = AIService(config={"provider": "gemini", "api_key": "user-key"})
            self.assertEqual(service.api_key, "user-key")

    def test_local_provider_does_not_require_keys(self):
        # Should not raise ValueError
        service = AIService(config={"provider": "local"})
        self.assertEqual(service.provider, "local")

    @patch("core.settings.Settings.DEEPSEEK_API_KEY", "")
    def test_validation_fails_when_deepseek_key_missing(self):
        with self.assertRaises(ValueError) as context:
            AIService(config={"provider": "deepseek", "api_key": ""})
        self.assertIn("Thiếu DEEPSEEK_API_KEY", str(context.exception))

    @patch("core.settings.Settings.DEEPSEEK_API_KEY", "dummy-key")
    def test_validation_passes_when_deepseek_key_in_settings(self):
        # Should not raise ValueError
        service = AIService(config={"provider": "deepseek"})
        self.assertEqual(service.api_key, "dummy-key")

    def test_validation_passes_when_deepseek_key_provided_in_config(self):
        # Should not raise ValueError even if settings has no key
        with patch("core.settings.Settings.DEEPSEEK_API_KEY", ""):
            service = AIService(config={"provider": "deepseek", "api_key": "user-key"})
            self.assertEqual(service.api_key, "user-key")

    @patch("core.settings.Settings.OPENROUTER_API_KEY", "")
    def test_validation_fails_when_openrouter_key_missing(self):
        with self.assertRaises(ValueError) as context:
            AIService(config={"provider": "openrouter", "api_key": ""})
        self.assertIn("Thiếu OPENROUTER_API_KEY", str(context.exception))

    @patch("core.settings.Settings.OPENROUTER_API_KEY", "dummy-key")
    def test_validation_passes_when_openrouter_key_in_settings(self):
        # Should not raise ValueError
        service = AIService(config={"provider": "openrouter"})
        self.assertEqual(service.api_key, "dummy-key")

    def test_validation_passes_when_openrouter_key_provided_in_config(self):
        # Should not raise ValueError even if settings has no key
        with patch("core.settings.Settings.OPENROUTER_API_KEY", ""):
            service = AIService(config={"provider": "openrouter", "api_key": "user-key"})
            self.assertEqual(service.api_key, "user-key")

if __name__ == "__main__":
    unittest.main()
