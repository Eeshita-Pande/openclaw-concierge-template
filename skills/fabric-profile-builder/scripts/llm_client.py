"""Unified LLM client supporting multiple providers.

Usage:
    client = create_client(provider, model)
    text = client.complete(prompt, max_tokens=2048, temperature=0.1)

Supported providers:
    - anthropic: Anthropic API (claude-haiku-4-5, claude-sonnet-4-6, etc.)
    - openai: OpenAI API (gpt-4o-mini, gpt-4o, etc.) or any compatible endpoint
    - openrouter: OpenRouter API (any model via openrouter.ai)

Each provider reads its API key from the standard env var:
    - ANTHROPIC_API_KEY (also checks auth-profiles.json as fallback)
    - OPENAI_API_KEY
    - OPENROUTER_API_KEY

Optional env vars for extra headers:
    - ANTHROPIC_EXTRA_HEADERS: comma-separated key=value pairs
    - ANTHROPIC_BETA: comma-separated beta feature flags (e.g., oauth-2025-04-20)
"""

import json
import os
import sys
import time


class LLMClient:
    """Base class for LLM clients."""

    def __init__(self, model: str):
        self.model = model

    def complete(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.1) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    def __init__(self, model: str):
        super().__init__(model)
        try:
            import anthropic
        except ImportError:
            print("ERROR: 'anthropic' package not installed. Run: pip install anthropic", file=sys.stderr)
            sys.exit(1)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # Try to read from OpenClaw auth-profiles
            api_key = self._read_openclaw_key()
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY not set and no OpenClaw auth profile found", file=sys.stderr)
            sys.exit(1)

        self.client = anthropic.Anthropic(api_key=api_key)

        # Build extra headers (beta flags, etc.)
        self.extra_headers = {}
        beta = os.environ.get("ANTHROPIC_BETA", "")
        if beta:
            self.extra_headers["anthropic-beta"] = beta
        extra = os.environ.get("ANTHROPIC_EXTRA_HEADERS", "")
        if extra:
            for pair in extra.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    self.extra_headers[k.strip()] = v.strip()

    def _read_openclaw_key(self) -> str | None:
        """Try to read Anthropic key from OpenClaw auth-profiles.json."""
        paths = [
            os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json"),
        ]
        for path in paths:
            try:
                with open(path) as f:
                    data = json.load(f)
                profile = data.get("profiles", {}).get("anthropic:default", {})
                token = profile.get("token", "")
                if token:
                    return token
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue
        return None

    def complete(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.1) -> str:
        import anthropic

        for attempt in range(3):
            try:
                kwargs = dict(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                if self.extra_headers:
                    kwargs["extra_headers"] = self.extra_headers

                response = self.client.messages.create(**kwargs)
                return response.content[0].text.strip()

            except anthropic.RateLimitError:
                wait = 30 * (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            except Exception as e:
                if attempt < 2:
                    print(f"    Error (attempt {attempt + 1}): {e}", file=sys.stderr)
                    time.sleep(2 ** (attempt + 1))
                else:
                    raise
        raise RuntimeError("Failed after 3 attempts")


class OpenAIClient(LLMClient):
    def __init__(self, model: str, base_url: str | None = None, api_key_env: str = "OPENAI_API_KEY"):
        super().__init__(model)
        try:
            import openai
        except ImportError:
            print("ERROR: 'openai' package not installed. Run: pip install openai", file=sys.stderr)
            sys.exit(1)

        api_key = os.environ.get(api_key_env)
        if not api_key:
            print(f"ERROR: {api_key_env} not set", file=sys.stderr)
            sys.exit(1)

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**kwargs)

    def complete(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.1) -> str:
        import openai

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} if "json" in prompt.lower()[:100] else None,
                )
                return response.choices[0].message.content.strip()

            except openai.RateLimitError:
                wait = 30 * (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            except Exception as e:
                if attempt < 2:
                    print(f"    Error (attempt {attempt + 1}): {e}", file=sys.stderr)
                    time.sleep(2 ** (attempt + 1))
                else:
                    raise
        raise RuntimeError("Failed after 3 attempts")


def create_client(provider: str, model: str) -> LLMClient:
    """Create an LLM client for the given provider and model.

    Args:
        provider: One of 'anthropic', 'openai', 'openrouter'
        model: Model identifier (provider-specific)

    Returns:
        An LLMClient instance ready to use.
    """
    provider = provider.lower().strip()

    if provider == "anthropic":
        return AnthropicClient(model)
    elif provider == "openai":
        return OpenAIClient(model)
    elif provider == "openrouter":
        return OpenAIClient(
            model=model,
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
        )
    else:
        print(f"ERROR: Unknown provider '{provider}'. Supported: anthropic, openai, openrouter", file=sys.stderr)
        sys.exit(1)
