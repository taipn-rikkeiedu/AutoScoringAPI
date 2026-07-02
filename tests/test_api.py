import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from extension.api_server import app

class APITest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("extension.api_server.get_ai_config")
    def test_get_config(self, mock_get_config):
        mock_get_config.return_value = {
            "provider": "gemini",
            "gemini_api_key": "key123",
            "exercise_source": "local",
            "exercise_api_url": "",
            "github_token": "token123"
        }
        
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["provider"], "gemini")
        self.assertEqual(data["exercise_source"], "local")
        self.assertTrue(data["has_github_token"])
        # Ensure API key is NOT leaked
        self.assertNotIn("gemini_api_key", data)

    @patch("extension.api_server.ExerciseService.load_templates")
    def test_get_exercises(self, mock_load_templates):
        mock_load_templates.return_value = {
            "Chương 1": {
                "Session 1": {
                    "Bài tập 1": {
                        "assignment": "Mô tả đề",
                        "criteria": "Tiêu chí"
                    }
                }
            }
        }
        
        response = self.client.get("/api/exercises")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Chương 1", data)
        self.assertIn("Session 1", data["Chương 1"])

    @patch("extension.api_server.get_cached_report")
    @patch("extension.api_server.GitHubService.get_repo_contents")
    @patch("extension.api_server.ExerciseService.load_templates")
    def test_grade_assignment_cached(self, mock_load_templates, mock_get_repo, mock_get_cached):
        # Setup mocks
        mock_load_templates.return_value = {
            "Chương 1": {
                "Session 1": {
                    "Bài tập 1": {
                        "assignment": "Đề bài mẫu",
                        "criteria": "Tiêu chí mẫu"
                    }
                }
            }
        }
        mock_get_repo.return_value = {
            "total_files": 2,
            "content": "FILE PATH: main.py\nprint('Hello')"
        }
        mock_get_cached.return_value = "## KẾT QUẢ CHẤM ĐIỂM\n| Tiêu chí | Điểm |\n|---|---|\n| **TỔNG** | **90/100** |\n## NHẬN XÉT\nTốt"

        payload = {
            "repo_url": "https://github.com/test/repo",
            "chapter": "Chương 1",
            "session": "Session 1",
            "assignment_name": "Bài tập 1"
        }
        
        response = self.client.post("/api/grade", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["cache_hit"])
        self.assertEqual(data["score"], "90")
        self.assertEqual(data["total_files"], 2)
        self.assertIn("TỔNG", data["report"])

if __name__ == "__main__":
    unittest.main()
