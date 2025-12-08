import asyncio
import os
from anthropic import Anthropic
from browser import Browser
from agent import Agent

async def main_loop():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Не найден API ключ.")
        return

    client = Anthropic(api_key=api_key)
    browser = Browser()
    await browser.start()

    try:
        while True:
            task = input("Введите задачу: ").strip()
            if task.lower() in ("exit", "quit"):
                break

            agent = Agent(
                task=task,
                browser=browser,
                llm_client=client,
                max_steps=15,
            )

            result = await agent.run()
            print("\n=== RESULT ===")
            print(result)
            print("==============\n")

    finally:
        await browser.close()

def main():
    asyncio.run(main_loop())

if __name__ == "__main__":
    main()