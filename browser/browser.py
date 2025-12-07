import asyncio
from typing import Optional

from playwright.async_api import async_playwright, Page


class Browser:
    """
    Обёртка над Playwright:
      - запуск/остановка браузера
      - базовые действия: goto, click, type, scroll, wait, press
    """

    def __init__(self, headless: bool = False):
        self._pw = None
        self._browser = None
        self.page: Optional[Page] = None
        self.headless = headless

    async def start(self):
        """
        Запускает Chromium и создаёт новую страницу.
        """
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.headless,
        )
        self.page = await self._browser.new_page(
            viewport={"width": 1280, "height": 800}
        )

    async def close(self):
        """
        Закрывает браузер и Playwright.
        """
        try:
            if self._browser:
                await self._browser.close()
        finally:
            if self._pw:
                await self._pw.stop()

    async def goto(self, url: str):
        if not self.page:
            raise RuntimeError("Страница не инициализирована, вызови start() сначала.")
        await self.page.goto(url, wait_until="load", timeout=60000)

    async def click_link(self, index: int):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        locator = self.page.locator("a")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"link index {index} out of range (0..{count-1})")
        await locator.nth(index).click()

    async def click_button(self, index: int):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        locator = self.page.locator("button, [role='button']")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"button index {index} out of range (0..{count-1})")
        await locator.nth(index).click()

    async def click_input(self, index: int):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        locator = self.page.locator("input, textarea")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"input index {index} out of range (0..{count-1})")
        await locator.nth(index).click()

    async def type_into_input(self, index: int, text: str):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        locator = self.page.locator("input, textarea")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"input index {index} out of range (0..{count-1})")
        el = locator.nth(index)
        await el.click()
        await el.fill("")  # очистим
        await el.type(text, delay=50)

    async def scroll(self, direction: str = "down", amount: int = 800):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        dy = amount if direction == "down" else -amount
        await self.page.mouse.wheel(0, dy)
        await self.page.wait_for_timeout(500)

    async def wait(self, seconds: float):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        await self.page.wait_for_timeout(int(seconds * 1000))

    async def press(self, key: str = "Enter"):
        if not self.page:
            raise RuntimeError("Страница не инициализирована.")
        await self.page.keyboard.press(key)
        await self.page.wait_for_timeout(1000)