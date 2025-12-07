from typing import Any, Dict

from browser_agent.browser import Browser


async def execute_action(
    browser: Browser,
    action: str,
    args: Dict[str, Any],
) -> str:
    """
    Выполняет одно действие, которое выбрала модель.

    Возвращает строку-результат (короткое описание).
    """
    action = action.lower()

    if action == "navigate":
        url = args.get("url")
        if not isinstance(url, str):
            raise ValueError("navigate: ожидается строка url в args['url']")
        await browser.goto(url)
        return f"Перешёл на {url}"

    elif action == "click":
        target = args.get("target")
        index = args.get("index")
        if not isinstance(index, int):
            raise ValueError("click: ожидается целое число в args['index']")
        if target == "link":
            await browser.click_link(index)
            return f"Клик по ссылке index={index}"
        elif target == "button":
            await browser.click_button(index)
            return f"Клик по кнопке index={index}"
        elif target == "input":
            await browser.click_input(index)
            return f"Клик по инпуту index={index}"
        else:
            raise ValueError("click: target должен быть 'link' | 'button' | 'input'")

    elif action == "type":
        index = args.get("index")
        text = args.get("text")
        if not isinstance(index, int) or not isinstance(text, str):
            raise ValueError("type: ожидается index:int и text:str")
        await browser.type_into_input(index, text)
        return f"Ввёл текст в input index={index}: {text!r}"

    elif action == "scroll":
        direction = args.get("direction", "down")
        amount = args.get("amount", 800)
        if direction not in ("down", "up"):
            direction = "down"
        if not isinstance(amount, int):
            amount = 800
        await browser.scroll(direction=direction, amount=amount)
        return f"Прокрутка {direction} на {amount} пикселей"

    elif action == "wait":
        seconds = args.get("seconds", 1.0)
        try:
            seconds_f = float(seconds)
        except Exception:
            seconds_f = 1.0
        await browser.wait(seconds_f)
        return f"Ждал {seconds_f} секунд"

    elif action == "press":
        key = args.get("key", "Enter")
        if not isinstance(key, str):
            key = "Enter"
        await browser.press(key)
        return f"Нажал клавишу {key}"

    elif action == "done":
        # done отрабатывается в Agent, здесь просто возвращаем result
        result = args.get("result", "done")
        return f"Задача завершена: {result}"

    else:
        raise ValueError(f"Неизвестное действие: {action}")