import json
import os
import re
import time
import requests
from core.settings import Settings
from core.storage_service import get_ai_config
from utils.helpers import parse_score


class AIService:
    def __init__(self):
        self.settings = Settings

    def _compress_code(self, code_text: str) -> str:
        """Loại bỏ khoảng trắng thừa cuối dòng và nén nhiều dòng trống liên tiếp thành tối đa 1 dòng trống."""
        if not code_text:
            return ""
        lines = [line.rstrip() for line in code_text.splitlines()]
        compressed = []
        last_was_empty = False
        for line in lines:
            if not line:
                if not last_was_empty:
                    compressed.append("")
                    last_was_empty = True
            else:
                compressed.append(line)
                last_was_empty = False
        return "\n".join(compressed)

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Thực hiện HTTP request với cơ chế tự động thử lại kèm dãn cách tăng dần (Exponential Backoff)."""
        max_attempts = 5
        base_delay = 2.0
        for attempt in range(max_attempts):
            try:
                response = requests.request(method, url, **kwargs)
                if response.status_code in (429, 503):
                    retry_after = response.headers.get("Retry-After")
                    delay = None
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            pass
                    
                    if not delay:
                        text = response.text
                        match = re.search(
                            r"(?:please retry in|retry after|waiting for|try again in)\s*(\d+(?:\.\d+)?)\s*s",
                            text,
                            re.IGNORECASE
                        )
                        if match:
                            delay = float(match.group(1))
                            
                    if not delay:
                        delay = base_delay * (2 ** attempt)
                        
                    time.sleep(delay)
                    continue
                return response
            except requests.RequestException as e:
                if attempt == max_attempts - 1:
                    raise e
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
        return requests.request(method, url, **kwargs)

    def grade_project(
        self,
        github_url: str,
        files: list[dict],
        provider: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None,
        model_name: str | None = None,
        criteria: str | None = None,
    ) -> dict:
        config = get_ai_config()
        provider = (
            (
                provider
                or config.get("provider")
                or self.settings.AI_PROVIDER
                or "gemini"
            )
            .strip()
            .lower()
        )
        model = (model_name or self.resolve_model_name(provider, config)).strip()
        api_key = api_key or self.resolve_api_key(provider, config)
        api_base_url = (
            api_base_url
            or config.get("custom_api_base_url")
            or config.get("openrouter_api_base_url")
            or self.settings.OPENROUTER_API_BASE_URL
        )

        self.settings.validate(
            provider=provider, api_key=api_key, api_base_url=api_base_url
        )
        prompt = self.build_prompt(
            github_url, files, criteria or self.settings.DEFAULT_CRITERIA
        )
        answer = self.send_to_model(provider, api_key, api_base_url, model, prompt)
        score = parse_score(answer) or "N/A"
        return {
            "provider": provider,
            "model": model,
            "score": score,
            "report": answer,
            "prompt": prompt,
        }

    def resolve_api_key(self, provider: str, config: dict) -> str:
        provider = provider.strip().lower()
        if provider == "deepseek":
            return config.get("deepseek_api_key") or self.settings.DEEPSEEK_API_KEY
        if provider == "openrouter":
            return config.get("openrouter_api_key") or self.settings.OPENROUTER_API_KEY
        if provider == "custom":
            return config.get("custom_api_key") or self.settings.CUSTOM_API_KEY
        if provider == "gemini":
            return config.get("gemini_api_key") or self.settings.GEMINI_API_KEY
        return config.get("gemini_api_key") or self.settings.GEMINI_API_KEY

    def resolve_model_name(self, provider: str, config: dict) -> str:
        provider = provider.strip().lower()
        if provider == "deepseek":
            return (
                config.get("deepseek_model_name") or self.settings.DEEPSEEK_MODEL_NAME
            )
        if provider == "openrouter":
            return (
                config.get("openrouter_model_name")
                or self.settings.OPENROUTER_MODEL_NAME
            )
        if provider == "custom":
            return (
                config.get("custom_model_name")
                or self.settings.CUSTOM_MODEL_NAME
                or self.settings.DEFAULT_MODEL
            )
        if provider == "local":
            return config.get("local_model_name") or self.settings.LOCAL_MODEL_NAME
        return config.get("gemini_model_name") or self.settings.DEFAULT_MODEL

    def build_prompt(self, github_url: str, files: list[dict], criteria: str) -> str:
        content = []
        max_chars = self.settings.MAX_PROJECT_CHARS
        total_chars = 0
        for item in files:
            snippet = item.get("content", "")
            if not snippet:
                continue
            # Áp dụng nén code để giảm bớt token tiêu hao
            compressed_snippet = self._compress_code(snippet)
            part = f"FILE: {item['path']}\n{compressed_snippet}\n\n"
            if total_chars + len(part) > max_chars:
                remaining = max_chars - total_chars
                content.append(part[:remaining])
                break
            content.append(part)
            total_chars += len(part)

        prompt_lines = [
            "Bạn là trợ lý đánh giá mã nguồn tự động chuyên nghiệp.",
            f"URL repo: {github_url}",
            "Dưới đây là nội dung các tệp mã nguồn cần đánh giá:",
            "\n".join(content),
            "\nYêu cầu đánh giá theo tiêu chí sau:",
            criteria,
            "\nVui lòng trả về kết quả bằng Tiếng Việt và trình bày đẹp dưới dạng bảng biểu Markdown, bao gồm:\n- Bảng điểm chi tiết với từng tiêu chí và tổng điểm /100 ở dòng cuối.\n- Nhận xét chi tiết cho từng tiêu chí (Điểm mạnh & Điểm yếu).\n- Gợi ý cụ thể để cải thiện mã nguồn.\n",
        ]
        return "\n\n".join(prompt_lines)

    def send_to_model(
        self,
        provider: str,
        api_key: str | None,
        api_base_url: str,
        model_name: str,
        prompt: str,
    ) -> str:
        provider = provider.strip().lower()
        if provider == "gemini":
            return self.send_to_gemini(api_key, model_name, prompt)
        if provider == "deepseek":
            return self.send_to_deepseek(api_key, api_base_url, model_name, prompt)
        if provider in ("openrouter", "custom"):
            return self.send_to_openrouter(api_key, api_base_url, model_name, prompt)
        if provider == "local":
            return self.send_to_local(api_key, api_base_url, model_name, prompt)
        raise ValueError(f"Nhà cung cấp AI không được hỗ trợ: {provider}")

    def send_to_gemini(self, api_key: str, model: str, prompt: str) -> str:
        """Gọi Google Gemini API trực tiếp qua REST API (không phụ thuộc SDK)."""
        model_endpoint = model if model.startswith("models/") else f"models/{model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_endpoint}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        response = self._request_with_retry("POST", url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Cấu trúc phản hồi Gemini không đúng định dạng. Phản hồi: {json.dumps(data)}")

    def send_to_deepseek(
        self, api_key: str, api_base_url: str, model: str, prompt: str
    ) -> str:
        url = api_base_url.rstrip("/") + "/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        response = self._request_with_retry("POST", url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return self.extract_chat_response(data)

    def send_to_openrouter(
        self, api_key: str, api_base_url: str, model: str, prompt: str
    ) -> str:
        url = api_base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        response = self._request_with_retry("POST", url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return self.extract_chat_response(data)

    def send_to_local(
        self, api_key: str | None, api_base_url: str, model: str, prompt: str
    ) -> str:
        url = api_base_url.rstrip("/") + "/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        try:
            response = self._request_with_retry("POST", url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                return self.extract_chat_response(response.json())
        except Exception:
            pass

        url_fallback = api_base_url.rstrip("/") + "/v1/generate"
        payload_fallback = {"model": model, "prompt": prompt}
        response = self._request_with_retry("POST", url_fallback, json=payload_fallback, timeout=120)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if isinstance(results, list) and results:
                return str(results[0].get("content") or results[0])
        elif isinstance(data, dict) and "response" in data:
            return data["response"]
        return json.dumps(data)

    def extract_chat_response(self, data: dict) -> str:
        if not isinstance(data, dict):
            return str(data)
        choices = data.get("choices") or []
        if choices and isinstance(choices, list):
            first = choices[0]
            message = first.get("message") or first
            if isinstance(message, dict):
                return (
                    message.get("content") or message.get("text") or json.dumps(message)
                )
            return str(message)
        return json.dumps(data)
