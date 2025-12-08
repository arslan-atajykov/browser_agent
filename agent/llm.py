# browser_agent/agent/llm.py
import json
from typing import Any, Dict, List

from anthropic import AsyncAnthropic
from config import ANTHROPIC_MODEL


SYSTEM_PROMPT = """
Ты — умный браузерный агент.

У тебя есть:
- Задача пользователя.
- Текущее состояние страницы (DOM-выжимка: url, title, кнопки, ссылки, инпуты).
- История предыдущих шагов.

ТВОЯ ЗАДАЧА — выбрать СЛЕДУЮЩЕЕ ДЕЙСТВИЕ из списка:
navigate, click, type, scroll, wait, press, done.

=========================
ГЛАВНЫЕ ПРАВИЛА
=========================

1) Если цель задачи уже достигнута — сразу делай:
{
  "action": "done",
  "args": { "result": "краткое описание успеха" }
}

2) Если URL содержит "watch?v=" — видео УЖЕ открыто.
   Значит:
{
  "action": "done",
  "args": { "result": "Видео успешно открыто" }
}

3) НИКОГДА не выполняй повторный navigate на тот же домен/URL.
   Если уже на целевом сайте → делай done.

4) НИКОГДА не делай одинаковое действие два раза подряд
   (navigate → navigate, click → click на тот же index, type → type и т.п.).

5) НЕ кликай по невидимым или пустым элементам.

6) НЕ кликай два раза по одному и тому же элементу.

7) Если загрузился нужный сайт (например market.yandex.ru) —
   повторно navigate на Market НЕ делать. Считай задачу выполненной.

8) Если пользователь говорит "закрыть сайт" —
   в одновкладочном браузере это означает:
   ПРОСТО выполнить navigate на другой сайт ОДИН РАЗ.
   Никаких прыжков туда-сюда.

=========================
ДОСТУПНЫЕ ДЕЙСТВИЯ
=========================

1. "navigate"
    args: { "url": "https://..." }

2. "click"
    args: { "target": "link" | "button" | "input", "index": <int> }

3. "type"
    args: { "index": <int>, "text": "..." }

4. "scroll"
    args: { "direction": "down" | "up", "amount": 800 }

5. "wait"
    args: { "seconds": 1.5 }

6. "press"
    args: { "key": "Enter" }

7. "done"
    args: { "result": "..." }

=========================
ФОРМАТ ОТВЕТА
=========================

СТРОГО ТОЛЬКО JSON без текста вокруг. Пример:

{
  "action": "type",
  "args": { "index": 0, "text": "iphone" },
  "thoughts": "Нашёл поисковое поле и ввожу запрос."
}
"""


def _trim(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


async def llm_decide(
    client: AsyncAnthropic,
    task: str,
    dom: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    history_text_parts = []
    for step in history[-10:]:
        history_text_parts.append(
            f"- step {step['step']}: action={step['action']}, args={step['args']}, "
            f"result={_trim(step.get('result', ''), 120)}"
        )
    history_text = "\n".join(history_text_parts) or "(пока пусто)"

    dom_preview = {
        "url": dom.get("url"),
        "title": dom.get("title"),
        "buttons": dom.get("buttons", [])[:20],
        "links": dom.get("links", [])[:20],
        "inputs": dom.get("inputs", [])[:20],
    }

    user_content = (
        "Задача пользователя:\n"
        f"{task}\n\n"
        "История предыдущих действий:\n"
        f"{history_text}\n\n"
        "Текущее состояние страницы (DOM-выжимка):\n"
        f"{json.dumps(dom_preview, ensure_ascii=False, indent=2)}\n\n"
        "ВЫБЕРИ СЛЕДУЮЩЕЕ ДЕЙСТВИЕ. "
        "Ответь СТРОГО В ФОРМАТЕ JSON.\n"
    )

    # ✅ THIS LINE MUST HAVE 'await'
    response = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=512,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    # Extract text
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text
    text = text.strip()

    # Extract JSON
    if "{" in text:
        text = text[text.index("{"):]
    if "}" in text:
        text = text[:text.rindex("}") + 1]

    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Ошибка парсинга JSON: {e}\nОтвет модели:\n{text}")

    if "action" not in data or "args" not in data:
        raise RuntimeError(f"Некорректный JSON: {data}")

    if "thoughts" not in data:
        data["thoughts"] = ""

    return data