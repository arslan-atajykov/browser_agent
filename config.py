import os
from anthropic import Anthropic


ANTHROPIC_MODEL = "claude-3-haiku-20240307"


def get_anthropic_client() -> Anthropic:
   
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Не найден ANTHROPIC_API_KEY в окружении. "
                           "Сделай export ANTHROPIC_API_KEY=... в терминале.")
    return Anthropic(api_key=api_key)