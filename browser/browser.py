import asyncio
from typing import Optional

from playwright.async_api import async_playwright, Page


class Browser:
    """
    Обёртка над Playwright:
      - запуск/остановка браузера
      - базовые действия: goto, click, type, scroll, wait, press
      - надёжный safe_click, чтобы не падать при исчезновении элементов
    """

    def __init__(self, headless: bool = False):
        self._pw = None
        self._browser = None
        self.page: Optional[Page] = None
        self.headless = headless

    async def start(self):
        """Запускает Chromium и создаёт новую страницу."""
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.headless)
        self.page = await self._browser.new_page(
            viewport={"width": 1280, "height": 800}
        )

    async def close(self):
        """Закрывает браузер и Playwright."""
        try:
            if self._browser:
                await self._browser.close()
        finally:
            if self._pw:
                await self._pw.stop()

    # ======================================================================
    #                           SAFE CLICK
    # ======================================================================
    async def safe_click(self, locator, index: int):
        """
        Делает надёжный клик:
          - trial=True → НЕ бросает ошибку если элемент исчез
          - короткий таймаут (2 сек)
          - подавляет ошибки YouTube (когда элемент не видим)
        """
        try:
            await locator.nth(index).click(
                timeout=2000,
                trial=True,      # <-- ключевой параметр!
                force=True        # <-- YouTube требует force
            )
        except Exception:
            # Если элемент исчез из DOM → это норма
            pass

        # Дать странице чуть обновиться
        await self.page.wait_for_timeout(300)

    # ======================================================================
    #                           NAVIGATION
    # ======================================================================
    async def goto(self, url: str):
        if not self.page:
            raise RuntimeError("Страница не инициализирована, вызови start() сначала.")

        try:
            await self.page.goto(url, wait_until="load", timeout=60000)
        except Exception:
            # YouTube, Market иногда дают ERR_SOCKET_NOT_CONNECTED
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)

        await self.page.wait_for_timeout(300)

    # ======================================================================
    #                           CLICK methods
    # ======================================================================
    async def click_link(self, index: int):
        locator = self.page.locator("a")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"link index {index} out of range (0..{count-1})")

        await self.safe_click(locator, index)

    async def click_button(self, index: int):
        locator = self.page.locator("button, [role='button']")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"button index {index} out of range (0..{count-1})")

        await self.safe_click(locator, index)

    async def click_input(self, index: int):
        locator = self.page.locator("input, textarea")
        count = await locator.count()
        if index < 0 or index >= count:
            raise ValueError(f"input index {index} out of range (0..{count-1})")

        await self.safe_click(locator, index)

    # ======================================================================
    #                           INPUT & ACTIONS
    # ======================================================================
    async def type_into_input(self, index: int, text: str):
        locator = self.page.locator("input, textarea")
        count = await locator.count()

        if index < 0 or index >= count:
            raise ValueError(f"input index {index} out of range (0..{count-1})")

        el = locator.nth(index)

        # Клик без ошибок
        try:
            await el.click(timeout=2000, trial=True, force=True)
        except Exception:
            pass

        await el.fill("")
        await el.type(text, delay=40)
        await self.page.wait_for_timeout(200)

    async def scroll(self, direction: str = "down", amount: int = 800):
        dy = amount if direction == "down" else -amount
        await self.page.mouse.wheel(0, dy)
        await self.page.wait_for_timeout(300)

    async def wait(self, seconds: float):
        await self.page.wait_for_timeout(int(seconds * 1000))

    async def press(self, key: str = "Enter"):
        await self.page.keyboard.press(key)
        await self.page.wait_for_timeout(300)