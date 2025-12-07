import json
from typing import Any, Dict, List

from anthropic import Anthropic

from browser_agent.config import ANTHROPIC_MODEL


SYSTEM_PROMPT = """
Ты — умный браузерный агент.

У тебя есть:
- Задача пользователя (на естественном языке).
- Текущее состояние страницы (DOM-выжимка: url, title, кнопки, ссылки, инпуты).
- История предыдущих шагов.

ТВОЯ ЗАДАЧА — выбрать СЛЕДУЮЩЕЕ ДЕЙСТВИЕ из списка:
navigate, click, type, scroll, wait, press, done.

=========================
ВАЖНЕЙШИЕ ПРАВИЛА
=========================

1) ЕСЛИ ЗАДАЧА ПО СУТИ ВЫПОЛНЕНА → ДЕЛАЙ:
{
  "action": "done",
  "args": { "result": "краткое описание успеха" }
}

Примеры выполнения задачи:
- Открыт нужный сайт (URL содержит целевой домен).
- На YouTube открыт URL формата "watch?v=" → видео открыто.
- На Маркете отображена страница результатов поиска.
- Пользовательская цель достигнута по смыслу.

2) НИКОГДА не повторяй одно и то же действие снова,
   если оно уже было в последних шагах истории.

3) НЕ кликай по невидимым и пустым элементам.
   Если элемент по индексу невидим или пуст — выбирай другой.

4) НЕ кликай по тому же элементу дважды подряд.

5) Если сайт уже находится там, куда пытаешься navigate → НЕ повторяй navigate.

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