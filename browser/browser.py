import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Page

class Browser:
    def __init__(self, headless: bool = False):
        self._pw = None
        self._browser = None
        self.page: Optional[Page] = None
        self.headless = headless

    async def start(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.headless)
        self.page = await self._browser.new_page(
            viewport={"width": 1280, "height": 800}
        )

    async def close(self):
        try:
            if self._browser:
                await self._browser.close()
        finally:
            if self._pw:
                await self._pw.stop()

    # ---------------- SAFE CLICK -----------------
    async def safe_click(self, locator, index: int):
        try:
            await locator.nth(index).click(
                timeout=2000,
                trial=True,
                force=True
            )
        except:
            pass

        await self.page.wait_for_timeout(300)

    # ---------------- SAFE GOTO -------------------
    async def goto(self, url: str) -> bool:
        try:
            await self.page.goto(url, wait_until="load", timeout=60000)
            return True
        except:
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                return True
            except:
                return False

    # CLICK API
    async def click_link(self, index: int):
        locator = self.page.locator("a")
        if index >= await locator.count():
            raise ValueError("Invalid link index")
        await self.safe_click(locator, index)

    async def click_button(self, index: int):
        locator = self.page.locator("button, [role='button']")
        if index >= await locator.count():
            raise ValueError("Invalid button index")
        await self.safe_click(locator, index)

    async def click_input(self, index: int):
        locator = self.page.locator("input, textarea")
        if index >= await locator.count():
            raise ValueError("Invalid input index")
        await self.safe_click(locator, index)

    # TYPE
    async def type_into_input(self, index: int, text: str):
        locator = self.page.locator("input, textarea")
        if index >= await locator.count():
            raise ValueError("Invalid input index")

        el = locator.nth(index)

        try:
            await el.click(timeout=2000, trial=True, force=True)
        except:
            pass

        await el.fill("")
        await el.type(text, delay=40)
        await self.page.wait_for_timeout(200)

    async def scroll(self, direction="down", amount=800):
        dy = amount if direction == "down" else -amount
        await self.page.mouse.wheel(0, dy)
        await self.page.wait_for_timeout(300)

    async def wait(self, seconds: float):
        await self.page.wait_for_timeout(int(seconds * 1000))

    async def press(self, key: str = "Enter"):
        await self.page.keyboard.press(key)
        await self.page.wait_for_timeout(300)