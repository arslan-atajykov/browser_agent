import traceback
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel

from browser_agent.browser import Browser, extract_dom
from browser_agent.agent.llm import llm_decide
from browser_agent.actions import execute_action

console = Console()


class Agent:
    """
    Мини-агент:
      - на каждом шаге: собирает DOM → спрашивает LLM → выполняет действие
      - завершается при action="done" или по max_steps
    """

    def __init__(
        self,
        task: str,
        browser: Browser,
        llm_client,
        max_steps: int = 20,
    ):
        self.task = task
        self.browser = browser
        self.llm_client = llm_client
        self.max_steps = max_steps

        self.history: List[Dict[str, Any]] = []
        self.last_dom: Optional[Dict[str, Any]] = None

    async def run(self) -> Optional[str]:
        console.print(Panel.fit(f"[bold cyan]Задача:[/bold cyan] {self.task}"))

        final_result: Optional[str] = None

        for step in range(1, self.max_steps + 1):
            console.print(f"\n[bold yellow]Шаг {step}/{self.max_steps}[/bold yellow]")

            if not self.browser.page:
                raise RuntimeError("Ошибка: browser.page = None, браузер не запущен")

            # ---------- 1. Сбор DOM ----------
            self.last_dom = await extract_dom(self.browser.page)

            # ---------- 2. Решение LLM ----------
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

            # ---------- 3. Если done ----------
            if action.lower() == "done":
                result = args.get("result", "Задача завершена.")
                console.print(Panel.fit(f"[bold green]DONE:[/bold green] {result}"))
                final_result = result
                self.history.append(
                    {
                        "step": step,
                        "action": action,
                        "args": args,
                        "result": result,
                    }
                )
                break

            # ---------- 4. Выполняем действие ----------
            try:
                result_str = await execute_action(self.browser, action, args)
                console.print(f"[magenta]Result:[/magenta] {result_str}")
                error = None
            except Exception as e:
                error_text = "".join(
                    traceback.format_exception(type(e), e, e.__traceback__)
                )
                console.print(
                    Panel.fit(
                        f"[red]Ошибка при выполнении действия: {action}[/red]\n{error_text}"
                    )
                )
                result_str = f"ERROR: {str(e)}"
                error = error_text

            # ---------- 5. Пишем историю ----------
            self.history.append(
                {
                    "step": step,
                    "action": action,
                    "args": args,
                    "result": result_str,
                    "error": error,
                }
            )

        if final_result is None:
            console.print(
                Panel.fit(
                    "[bold red]Агент достиг лимита шагов и не завершил задачу явно.[/bold red]"
                )
            )

        return final_result