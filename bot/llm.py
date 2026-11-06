"""Client Gemini minimal avec sortie JSON structurée."""
from __future__ import annotations

import json
import logging
import os
import time

from pydantic import BaseModel

from .config import GEMINI_MODEL

log = logging.getLogger(__name__)


class Gemini:
    def __init__(self, api_key: str, model: str = GEMINI_MODEL):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model

    @classmethod
    def from_env(cls) -> "Gemini | None":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            log.warning("GEMINI_API_KEY absente : stratégies Gemini désactivées")
            return None
        return cls(key)

    def json(self, prompt: str, schema: type[BaseModel], system: str | None = None,
             retries: int = 3) -> BaseModel:
        from google.genai import types

        cfg = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            system_instruction=system,
            temperature=0.2,
        )
        last: Exception | None = None
        for attempt in range(retries):
            try:
                resp = self.client.models.generate_content(model=self.model, contents=prompt, config=cfg)
                if getattr(resp, "parsed", None) is not None:
                    return resp.parsed
                return schema.model_validate(json.loads(resp.text))
            except Exception as e:  # noqa: BLE001
                last = e
                log.warning("Appel Gemini échoué (essai %d) : %s", attempt + 1, e)
                time.sleep(2 ** (attempt + 1))
        raise RuntimeError(f"Gemini indisponible : {last}")
