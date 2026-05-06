import json
from dataclasses import dataclass
from hashlib import sha256
from urllib import request
from urllib.error import URLError

from multi_agent_research_lab.core.config import Settings, get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None

class LLMClient:
    """Provider-agnostic LLM client with Gemini/OpenAI and local fallback."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Gemini is preferred when GEMINI_API_KEY is configured. OpenAI remains
        supported for the original starter repo. Without provider keys, this
        returns a stable local response so tests and demos run offline.
        """

        if self.settings.gemini_api_key:
            try:
                return self._complete_gemini(system_prompt, user_prompt)
            except (OSError, URLError, TimeoutError, ValueError, KeyError) as exc:
                fallback = self._local_complete(system_prompt, user_prompt)
                return LLMResponse(
                    content=f"{fallback}\n\nGemini fallback note: {type(exc).__name__}: {exc}",
                    input_tokens=self._count_tokens(system_prompt + "\n" + user_prompt),
                    output_tokens=self._count_tokens(fallback),
                    cost_usd=0.0,
                )

        if self.settings.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.settings.openai_api_key)
                response = client.chat.completions.create(
                    model=self.settings.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )
                usage = response.usage
                input_tokens = getattr(usage, "prompt_tokens", None)
                output_tokens = getattr(usage, "completion_tokens", None)
                content = response.choices[0].message.content or ""
                return LLMResponse(
                    content=content.strip(),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=self._estimate_cost(input_tokens, output_tokens),
                )
            except Exception as exc:
                fallback = self._local_complete(system_prompt, user_prompt)
                return LLMResponse(
                    content=f"{fallback}\n\nProvider fallback note: {type(exc).__name__}: {exc}",
                    input_tokens=self._count_tokens(system_prompt + "\n" + user_prompt),
                    output_tokens=self._count_tokens(fallback),
                    cost_usd=0.0,
                )

        fallback = self._local_complete(system_prompt, user_prompt)
        return LLMResponse(
            content=fallback,
            input_tokens=self._count_tokens(system_prompt + "\n" + user_prompt),
            output_tokens=self._count_tokens(fallback),
            cost_usd=0.0,
        )

    def _complete_gemini(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        model = self._normalize_gemini_model(self.settings.gemini_model)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={self.settings.gemini_api_key}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1200,
            },
        }
        req = request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self.settings.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))

        candidate = data["candidates"][0]
        parts = candidate["content"].get("parts", [])
        content = "\n".join(part.get("text", "") for part in parts).strip()
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount")
        output_tokens = usage.get("candidatesTokenCount")
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._estimate_cost(input_tokens, output_tokens),
        )

    def _local_complete(self, system_prompt: str, user_prompt: str) -> str:
        digest = sha256(f"{system_prompt}\n{user_prompt}".encode()).hexdigest()[:8]
        prompt_lines = [line.strip("- ") for line in user_prompt.splitlines() if line.strip()]
        key_points = prompt_lines[:5] or [user_prompt[:240]]
        bullets = "\n".join(f"- {point}" for point in key_points)
        return (
            "Offline LLM synthesis\n"
            f"Run id: {digest}\n"
            "Key points:\n"
            f"{bullets}\n"
            "Recommendation: verify external facts with live search before production use."
        )

    def _count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))

    def _normalize_gemini_model(self, model: str) -> str:
        if model.startswith("gemini-"):
            return model
        return f"gemini-{model}"

    def _estimate_cost(self, input_tokens: int | None, output_tokens: int | None) -> float | None:
        if input_tokens is None and output_tokens is None:
            return None
        total = (input_tokens or 0) + (output_tokens or 0)
        return round(total * 0.0000005, 6)
