# browser_agent/main.py
import asyncio
import os

from anthropic import Anthropic
from browser_agent.browser import Browser
from browser_agent.agent import Agent


async def main_loop():
    # 1. Инициализируем LLM-клиент (Haiku)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Не найден ANTHROPIC_API_KEY в окружении.")
        print("   Пример: export ANTHROPIC_API_KEY='sk-ant-...'\n")
        return

    llm_client = Anthropic(api_key=api_key)

    print("🤖 Browser Agent запущен. Пиши задачи.\n")

    # 2. Основной цикл: после каждой задачи спрашиваем новую
    while True:
        task = input("Введите задачу (или 'exit' для выхода): ").strip()
        if not task:
            continue
        if task.lower() in ("exit", "quit", "выход"):
            print("👋 Выход из агента.")
            break

        # 3. Запускаем браузер под эту задачу
        browser = Browser()  # без headless, как ты сейчас используешь
        await browser.start()

        try:
            agent = Agent(
                task=task,
                browser=browser,
                llm_client=llm_client,
                max_steps=15,
            )
            result = await agent.run()

            print("\n=== РЕЗУЛЬТАТ ===")
            print(result)
            print("=== КОНЕЦ ЗАДАЧИ ===\n")

        finally:
            await browser.close()


def main():
    asyncio.run(main_loop())


if __name__ == "__main__":
    main()