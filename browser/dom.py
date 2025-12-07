from typing import Dict, Any, List

from playwright.async_api import Page


async def extract_dom(page: Page) -> Dict[str, Any]:
    """
    Собирает компактное представление страницы:
      - url, title
      - немного HTML
      - списки кнопок, ссылок, инпутов с индексами
    Это то, что мы будем давать LLM.
    """
    url = page.url
    title = await page.title()
    html = await page.content()

    # ограничим HTML
    max_html = 8000
    if len(html) > max_html:
        html = html[:max_html] + "\n<!-- truncated -->"

    # кнопки
    button_locator = page.locator("button, [role='button']")
    button_texts: List[str] = await button_locator.all_text_contents()
    buttons = []
    for idx, txt in enumerate(button_texts):
        norm = " ".join(txt.split())
        if not norm:
            norm = "(пустой текст)"
        buttons.append(
            {
                "index": idx,
                "text": norm[:200],
            }
        )

    # ссылки
    link_locator = page.locator("a")
    link_texts: List[str] = await link_locator.all_text_contents()
    links = []
    for idx, txt in enumerate(link_texts):
        norm = " ".join(txt.split())
        if not norm:
            continue
        links.append(
            {
                "index": idx,
                "text": norm[:200],
            }
        )
        if len(links) >= 50:
            break

    # инпуты
    input_locator = page.locator("input, textarea")
    input_elements = await input_locator.all()
    inputs = []
    for idx, el in enumerate(input_elements):
        attrs = {}
        for name in ["id", "name", "type", "placeholder", "value"]:
            try:
                v = await el.get_attribute(name)
                if v:
                    attrs[name] = v[:200]
            except Exception:
                pass
        inputs.append(
            {
                "index": idx,
                "attrs": attrs,
            }
        )
        if len(inputs) >= 50:
            break

    return {
        "url": url,
        "title": title,
        "html": html,
        "buttons": buttons,
        "links": links,
        "inputs": inputs,
    }