from typing import Dict, Any, List
from playwright.async_api import Page

async def extract_dom(page: Page) -> Dict[str, Any]:
    """ Надёжный DOM-сборщик. Не падает даже при сломанной навигации. """

    # URL
    try:
        url = page.url
    except:
        url = ""

    # TITLE
    try:
        title = await page.title()
    except:
        title = ""

    # HTML (ограничение 8kb)
    try:
        html = await page.content()
        if len(html) > 8000:
            html = html[:8000] + "\n<!-- truncated -->"
    except:
        html = ""

    # Buttons
    buttons = []
    try:
        locator = page.locator("button, [role='button']")
        texts = await locator.all_text_contents()
        for idx, txt in enumerate(texts):
            t = txt.strip()
            if not t:
                t = "(empty)"
            buttons.append({"index": idx, "text": t[:200]})
    except:
        pass

    # Links
    links = []
    try:
        locator = page.locator("a")
        texts = await locator.all_text_contents()
        for idx, txt in enumerate(texts):
            t = txt.strip()
            if t:
                links.append({"index": idx, "text": t[:200]})
                if len(links) >= 50:
                    break
    except:
        pass

    # Inputs
    inputs = []
    try:
        locator = page.locator("input, textarea")
        els = await locator.all()

        for idx, el in enumerate(els):
            attrs = {}
            for name in ["id", "name", "type", "placeholder", "value"]:
                try:
                    v = await el.get_attribute(name)
                    if v:
                        attrs[name] = v[:200]
                except:
                    pass

            inputs.append({"index": idx, "attrs": attrs})
            if len(inputs) >= 50:
                break
    except:
        pass

    return {
        "url": url,
        "title": title,
        "html": html,
        "buttons": buttons,
        "links": links,
        "inputs": inputs,
    }