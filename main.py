import asyncio

from browser_agent.config import get_anthropic_client
from browser_agent.browser import Browser
from browser_agent.agent import Agent


async def run_agent():
    task = input(
        "Введите задачу (например: 'открой https://market.yandex.ru и найди iphone'): "
    )

    # Инициализируем LLM
    llm_client = get_anthropic_client()

    # Запускаем браузер
    browser = Browser(headless=False)
    await browser.start()

    try:
        agent = Agent(
            task=task,
            browser=browser,
            llm_client=llm_client,
            max_steps=15,
        )
        await agent.run()
    finally:
        await browser.close()


def main():
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()