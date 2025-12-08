# browser_agent/agent/agent.py
import asyncio
import traceback
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel

from browser import Browser
from browser.dom import extract_dom
from agent.llm import llm_decide
from actions import execute_action

console = Console()


class Agent:
    def __init__(self, task: str, browser: Browser, llm_client, max_steps: int = 20):
        self.task = task
        self.browser = browser
        self.llm_client = llm_client
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []
        self.last_dom: Optional[Dict[str, Any]] = None

    async def run(self) -> Optional[str]:
        console.print(Panel.fit(f"[bold cyan]Задача:[/bold cyan] {self.task}"))

        final_result = None

        for step in range(1, self.max_steps + 1):
            console.print(f"\n[bold yellow]Шаг {step}/{self.max_steps}[/bold yellow]")

            self.last_dom = await extract_dom(self.browser.page)
            url = self.last_dom.get("url", "")

            # 🔥 AUTO-DONE
            if "youtube.com/watch" in url:
                msg = "Видео успешно открыто."
                console.print(Panel.fit(f"[bold green]{msg}[/bold green]"))
                return msg

            if "market.yandex" in url and "search" in url:
                msg = "Открыта страница поиска на Яндекс Маркете."
                console.print(Panel.fit(f"[bold green]{msg}[/bold green]"))
                return msg

            # 2) LLM decision
            decision = await llm_decide(
                client=self.llm_client,
                task=self.task,
                dom=self.last_dom,
                history=self.history,
            )

            action = decision["action"]
            args = decision.get("args", {})
            thoughts = decision.get("thoughts", "")

            console.print(f"[green]Action:[/green] {action}")
            console.print(f"[green]Args:[/green] {args}")
            if thoughts:
                console.print(f"[blue]Thoughts:[/blue] {thoughts}")

            # 3) DONE
            if action == "done":
                result = args.get("result", "Задача завершена.")
                console.print(Panel.fit(f"[bold green]DONE: {result}[/bold green]"))
                return result

            # 4) ⚠️ Prevent repeated actions
            if self.history:
                last = self.history[-1]
                if last["action"] == action and last["args"] == args:
                    msg = "Пропущено: повторное действие (политика безопасности агента)."
                    console.print(f"[red]{msg}[/red]")
                    self.history.append({
                        "step": step,
                        "action": action,
                        "args": args,
                        "result": msg,
                        "error": "Blocked by agent safety policy",
                    })
                    continue

            # 5) Execute action
            try:
                result_str = await asyncio.wait_for(
                    execute_action(self.browser, action, args),
                    timeout=10,
                )
                console.print(f"[magenta]Result:[/magenta] {result_str}")
                error = None

            except asyncio.TimeoutError:
                result_str = f"TIMEOUT: действие '{action}' > 10 секунд."
                console.print(Panel.fit(f"[red]{result_str}[/red]"))
                error = result_str

            except Exception as e:
                err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                console.print(Panel.fit(f"[red]Ошибка {action}[/red]\n{err}"))
                result_str = f"ERROR: {e}"
                error = err

            self.history.append({
                "step": step,
                "action": action,
                "args": args,
                "result": result_str,
                "error": error,
            })

        console.print(
            Panel.fit("[bold red]Агент дошёл до лимита шагов и не завершил задачу.[/bold red]")
        )
        return None