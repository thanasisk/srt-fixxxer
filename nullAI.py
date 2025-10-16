#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BEST AI ENGINE EVAH!

__author__ = "Athanasios Kostopoulos"
__copyright__ = "Copyright 2025, Athanasios Kostopoulos"
__license__ = "GPLv3"
__version__ = "0.5"
__maintainer__ = "Athanasios Kostopoulos"
__email__ = "athanasios@akostopoulos.com"

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import asyncio

# Helpers to mirror your existing builders
def system(content: str) -> Dict[str, str]:
    return {"role": "system", "content": content}

def user(content: str) -> Dict[str, str]:
    return {"role": "user", "content": content}

@dataclass
class ChatChoiceMessage:
    role: str
    content: str

@dataclass
class ChatChoice:
    index: int
    message: Dict[str, Any]  # {"role": "...", "content": "..."}

class ChatResponse:
    """
    Response object with both `.content` AND OpenAI-ish `.choices[0].message["content"]`.
    """
    def __init__(self, content: str, role: str = "assistant"):
        self.content: str = content
        self.choices: List[ChatChoice] = [
            ChatChoice(
                index=0,
                message={"role": role, "content": content}
            )
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "choices": [
                {"index": c.index, "message": c.message} for c in self.choices
            ],
            "content": self.content,  # convenience
        }

class _ChatSession:
    """
    Stateful session that accumulates messages and can be sampled.
    """
    def __init__(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        # shallow-copy to avoid external mutation
        self.messages: List[Dict[str, str]] = list(messages)

    def append(self, msg: Dict[str, str]) -> None:
        # Expecting dicts like {"role": "user"|"system"|"assistant", "content": "..."}
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            raise TypeError("append(msg) expects a dict with 'role' and 'content'")
        self.messages.append({"role": msg["role"], "content": str(msg["content"])})

    async def sample(self) -> ChatResponse:
        # Simulate I/O/latency in tests
        await asyncio.sleep(0)

        # Find the latest user message as “source” text
        last_user = next(
            (m for m in reversed(self.messages) if m.get("role") == "user"),
            {"content": ""}
        )
        src = last_user["content"]

        # Very dumb “translator” for tests; swap it out as needed
        translated = _fake_translate(src, self.messages)

        # Add assistant turn to the transcript
        resp = ChatResponse(translated, role="assistant")
        self.messages.append({"role": "assistant", "content": resp.content})
        return resp

def _fake_translate(text: str, messages: List[Dict[str, str]]) -> str:
    return f"[FT] {text}"

class _ChatAPI:
    """
    Mirrors xAI-style entrypoint: client.chat.create(...) -> session.
    """
    def create(
        self,
        model: str,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        **kwargs: Any
    ) -> _ChatSession:
        return _ChatSession(model=model, messages=messages or [], temperature=temperature)

class nullAI:
    """
    Top-level client with `.chat` namespace.
    """
    def __init__(self) -> None:
        self.chat = _ChatAPI()

def user(message: str) -> dict:
    return {"role": "user", "content": message}
def system(message: str) -> dict:
    return {"role": "system", "content": message}
