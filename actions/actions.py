from typing import Any, Dict
from browser import Browser

async def execute_action(browser: Browser, action: str, args: Dict[str, Any]) -> str:
    action = action.lower()

    if action == "navigate":
        url = args.get("url")
        if not isinstance(url, str):
            return "navigate: invalid url"

        ok = await browser.goto(url)
        if not ok:
            return f"navigate: FAILED to load {url}"
        return f"Перешёл на {url}"

    elif action == "click":
        target = args.get("target")
        index = args.get("index")

        if not isinstance(index, int):
            return "click: invalid index"

        if target == "link":
            await browser.click_link(index)
            return f"Клик по ссылке #{index}"
        elif target == "button":
            await browser.click_button(index)
            return f"Клик по кнопке #{index}"
        elif target == "input":
            await browser.click_input(index)
            return f"Клик по инпуту #{index}"
        else:
            return "click: invalid target"

    elif action == "type":
        index = args.get("index")
        text = args.get("text")
        if not isinstance(index, int) or not isinstance(text, str):
            return "type: invalid args"

        await browser.type_into_input(index, text)
        return f"Ввёл текст в input[{index}]"

    elif action == "scroll":
        await browser.scroll(args.get("direction", "down"), args.get("amount", 800))
        return "scroll"

    elif action == "wait":
        await browser.wait(float(args.get("seconds", 1.0)))
        return "wait"

    elif action == "press":
        await browser.press(args.get("key", "Enter"))
        return "press"

    elif action == "done":
        return args.get("result", "done")

    return f"unknown action: {action}"