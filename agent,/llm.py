import json
from typing import Any, Dict, List

from anthropic import Anthropic

from browser_agent.config import ANTHROPIC_MODEL


SYSTEM_PROMPT = """
Ты — умный браузерный агент.

У тебя есть:
- Задача пользователя (на естественном языке, может быть на русском).
- Текущее состояние страницы (DOM-выжимка: url, title, кнопки, ссылки, инпуты).
- История предыдущих шагов (что пробовал до этого).

ТВОЯ ЗАДАЧА — выбрать СЛЕДУЮЩЕЕ ДЕЙСТВИЕ для управления браузером.

Доступные действия (поле "action") и их аргументы ("args"):

1. "navigate"
   - открыть URL
   - args: { "url": "https://..." }

2. "click"
   - клик по элементу
   - args: { "target": "link" | "button" | "input", "index": <int> }
   - index — это индекс из dom.links / dom.buttons / dom.inputs

3. "type"
   - ввести текст в поле ввода (input/textarea)
   - args: { "index": <int>, "text": "что ввести" }
   - index — это индекс из dom.inputs

4. "scroll"
   - прокрутить страницу
   - args: { "direction": "down" | "up", "amount": 800 }

5. "wait"
   - подождать немного
   - args: { "seconds": 1.5 }

6. "press"
   - нажать клавишу (например, Enter)
   - args: { "key": "Enter" }

7. "done"
   - задача полностью выполнена
   - args: { "result": "краткое описание результата на русском" }

ОЧЕНЬ ВАЖНО:
- Используй только существующие индексы элементов, которые видишь в dom["buttons"], dom["links"], dom["inputs"].
- Если задача ещё не выполнена — НЕ используй "done".
- Думай пошагово: сначала понять страницу (url, title, кнопки, инпуты), потом решать, куда кликнуть/куда вводить.
- Для поиска на сайте обычно:
  - найти поисковое поле (input с placeholder / name / type='search'),
  - ввести текст (type),
  - нажать Enter (press) либо кликнуть по кнопке поиска (click).

Формат ответа:
СТРОГО ТОЛЬКО JSON, без комментариев, без текста вокруг, без Markdown и без пояснений.

Пример корректного ответа:

{
  "action": "type",
  "args": {
    "index": 0,
    "text": "iphone"
  },
  "thoughts": "Нашёл поисковое поле по index=0 и ввожу туда запрос."
}

Поле "thoughts" — это краткое объяснение по-русски, что ты делаешь и зачем.
"""


def _trim(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


async def llm_decide(
    client: Anthropic,
    task: str,
    dom: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Делает один шаг: даёт Claude задачу, DOM и историю, возвращает JSON-решение.
    """
    # История в виде текста (коротко)
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
        "Ответь СТРОГО В ФОРМАТЕ JSON (без текста вокруг, без форматирования).\n"
    )

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=512,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": user_content,
            }
        ],
    )

    # Собираем текст из блоков
    text = ""
    for block in response.content:
        if block.type == "text":
            text += block.text

    text = text.strip()
    # На всякий случай обрежем всё до первой '{'
    if "{" in text:
        text = text[text.index("{") :]
    # И до последней '}'
    if "}" in text:
        last = text.rfind("}")
        text = text[: last + 1]

    try:
        data = json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Не удалось распарсить JSON из ответа модели: {e}\nОтвет:\n{text}")

    # Минимальная валидация
    if "action" not in data or "args" not in data:
        raise RuntimeError(f"Некорректный формат ответа модели: {data}")

    if "thoughts" not in data:
        data["thoughts"] = ""

    return data