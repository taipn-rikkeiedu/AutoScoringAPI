import unittest
from unittest.mock import patch, Mock
from core.exercise_service import ExerciseService

class ExerciseServiceTest(unittest.TestCase):
    def setUp(self):
        # Reset global templates before each test
        import core.exercise_service
        core.exercise_service._GLOBAL_TEMPLATES = None

    def test_load_templates_non_streamlit_returns_dict(self):
        # Should not raise exception and should return a dict
        templates = ExerciseService.load_templates()
        self.assertIsInstance(templates, dict)

    def test_save_templates_non_streamlit_persists_in_memory(self):
        test_data = {"Chương 1": {"Session 1": {"Bài tập 1": {"assignment": "test", "criteria": "test"}}}}
        # Save templates
        ExerciseService.save_templates(test_data)
        # Load templates should return the same dictionary
        loaded = ExerciseService.load_templates()
        self.assertEqual(loaded, test_data)

    @patch("core.exercise_service.requests.get")
    def test_fetch_from_api_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Chương 1": {
                "Session 1": {
                    "Bài tập 1": {
                        "assignment": "Đề bài mẫu",
                        "criteria": "Tiêu chí mẫu"
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        data = ExerciseService.fetch_from_api("http://example.com/api/exercises", "token123")
        self.assertIn("Chương 1", data)
        self.assertEqual(data["Chương 1"]["Session 1"]["Bài tập 1"]["assignment"], "Đề bài mẫu")
        mock_get.assert_called_once_with("http://example.com/api/exercises", headers={"Authorization": "Bearer token123"}, timeout=30)

    @patch("core.exercise_service.requests.get")
    def test_fetch_from_api_invalid_structure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Chương 1": "Invalid Session Structure"
        }
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            ExerciseService.fetch_from_api("http://example.com/api/exercises")
        self.assertIn("phải chứa một đối tượng sessions", str(context.exception))

if __name__ == "__main__":
    unittest.main()
