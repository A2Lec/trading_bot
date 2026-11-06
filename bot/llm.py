"""Client Gemini minimal avec sortie JSON structurée.

- API forcée en v1beta : depuis google-genai 3.x le SDK utilise v1 par défaut, qui ne
  connaît pas les alias (`gemini-flash-latest`…) ni certaines fonctions.
- Le modèle est choisi parmi ceux réellement disponibles pour la clé (models.list),
  en respectant GEMINI_MODEL s'il existe.
- Les erreurs définitives (clé invalide, modèle introuvable…) ne sont pas réessayées, et
  désactivent Gemini pour le reste du run au lieu de répéter l'échec à chaque appel.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time

from pydantic import BaseModel

from .config import GEMINI_MODEL

log = logging.getLogger(__name__)

API_VERSION = "v1beta"
_EXCLUDE = ("lite", "8b", "image", "tts", "audio", "live", "embedding", "thinking", "vision", "robotics", "computer")
_RETRYABLE = {429, 500, 502, 503, 504}


def _version(name: str) -> float:
    m = re.match(r"gemini-(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else 0.0


def pick_model(available: list[str], wanted: str | None) -> str | None:
    """Choisit le modèle : celui demandé s'il existe, sinon le Flash stable le plus récent."""
    if wanted:
        if wanted in available:
            return wanted
        log.warning("Modèle Gemini %r indisponible pour cette clé, sélection automatique", wanted)
    flash = [n for n in available if "flash" in n and not any(x in n for x in _EXCLUDE)]
    stable = [n for n in flash if re.fullmatch(r"gemini-\d+(\.\d+)?-flash", n)]
    previews = [n for n in flash if "preview" in n or "exp" in n]
    aliases = [n for n in flash if n.endswith("-latest")]
    for group in (stable, aliases, previews, flash):
        if group:
            return sorted(group, key=lambda n: (_version(n), n), reverse=True)[0]
    return None


class GeminiUnavailable(RuntimeError):
    pass


class Gemini:
    def __init__(self, api_key: str, model: str | None = None):
        from google import genai
        from google.genai import types

        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version=API_VERSION))
        self.error: str | None = None  # erreur définitive rencontrée pendant ce run
        available = [
            m.name.removeprefix("models/")
            for m in self.client.models.list()
            if "generateContent" in (m.supported_actions or [])
        ]
        self.model = pick_model(available, model)
        if not self.model:
            raise GeminiUnavailable(f"Aucun modèle Gemini Flash disponible (modèles vus : {', '.join(available[:15])})")
        log.info("Gemini : modèle %s (API %s)", self.model, API_VERSION)

    @classmethod
    def from_env(cls) -> "Gemini | None":
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            log.warning("GEMINI_API_KEY absente : stratégies Gemini désactivées")
            return None
        try:
            return cls(key, os.getenv("GEMINI_MODEL") or GEMINI_MODEL)
        except Exception as e:  # noqa: BLE001
            log.error("Gemini inutilisable : %s", e)
            return None

    def json(self, prompt: str, schema: type[BaseModel], system: str | None = None,
             retries: int = 3) -> BaseModel:
        from google.genai import errors, types

        if self.error:
            raise GeminiUnavailable(self.error)
        cfg = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            system_instruction=system,
            temperature=0.2,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        last: Exception | None = None
        for attempt in range(retries):
            try:
                resp = self.client.models.generate_content(model=self.model, contents=prompt, config=cfg)
                if getattr(resp, "parsed", None) is not None:
                    return resp.parsed
                return schema.model_validate(json.loads(resp.text))
            except errors.APIError as e:
                last = e
                if e.code not in _RETRYABLE:  # erreur définitive : inutile d'insister
                    self.error = f"Gemini {e.code} {e.status} : {e.message}"
                    log.error(self.error)
                    raise GeminiUnavailable(self.error) from e
                log.warning("Appel Gemini échoué (essai %d/%d) : %s", attempt + 1, retries, e)
            except Exception as e:  # noqa: BLE001 — JSON invalide, réseau…
                last = e
                log.warning("Appel Gemini échoué (essai %d/%d) : %s", attempt + 1, retries, e)
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
        raise GeminiUnavailable(f"Gemini indisponible : {last}")
