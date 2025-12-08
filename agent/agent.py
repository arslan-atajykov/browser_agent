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

    async def run(self) -> Optional[str]:
        console.print(Panel.fit(f"[bold cyan]Задача:[/bold cyan] {self.task}"))

        for step in range(1, self.max_steps + 1):
            console.print(f"\n[bold yellow]Шаг {step}/{self.max_steps}[/bold yellow]")

            # SAFE DOM
            try:
                dom = await extract_dom(self.browser.page)
            except:
                dom = {"url": "", "title": "", "buttons": [], "links": [], "inputs": []}

            decision = await llm_decide(
                client=self.llm_client,
                task=self.task,
                dom=dom,
                history=self.history,
            )

            action = decision["action"]
            args = decision.get("args", {})
            thoughts = decision.get("thoughts", "")

            console.print(f"[green]Action:[/green] {action}")
            console.print(f"[green]Args:[/green] {args}")
            if thoughts:
                console.print(f"[blue]Thoughts:[/blue] {thoughts}")

            if action == "done":
                result = args.get("result", "Задача выполнена")
                console.print(Panel.fit(f"[bold green]{result}[/bold green]"))
                return result

            try:
                result = await asyncio.wait_for(
                    execute_action(self.browser, action, args),
                    timeout=10,
                )
                console.print(f"[magenta]Result:[/magenta] {result}")
                err = None

            except Exception as e:
                err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                console.print(Panel.fit(f"[red]{err}[/red]"))
                result = str(e)

            self.history.append({
                "step": step,
                "action": action,
                "args": args,
                "result": result,
                "error": err,
            })

        console.print(Panel.fit("[bold red]Достигнут лимит шагов[/bold red]"))
        return None