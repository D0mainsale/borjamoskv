"""
cortex.server.supervisor.py
====================
Industrial Noir Process Supervisor v1.0
Orchestrates: 1x API Server + Nx Swarm Workers
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from typing import List

from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text

# ── Config ────────────────────────────────────────────────────────────────────

API_CMD    = [sys.executable, "-m", "cortex.server.api"]
WORKER_CMD = [sys.executable, "-m", "cortex.server.worker"]
NUM_WORKERS = int(os.getenv("CORTEX_WORKERS", "2"))

console = Console()

class ProcessManager:
    def __init__(self, name: str, command: List[str]):
        self.name = name
        self.command = command
        self.proc = None
        self.start_time = None
        self.restarts = 0
        self.status = "INITIALIZING"

    def start(self):
        self.status = "STARTING"
        self.proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.start_time = datetime.now()
        self.status = "ONLINE"

    def check(self):
        if self.proc and self.proc.poll() is not None:
            self.status = "CRASHED"
            self.restarts += 1
            self.start() # Auto-restart logic

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.status = "OFFLINE"

    def get_uptime(self):
        if not self.start_time: return "0s"
        delta = datetime.now() - self.start_time
        return str(delta).split(".")[0]

class Supervisor:
    def __init__(self):
        self.processes = []
        self.processes.append(ProcessManager("API_SERVER", API_CMD))
        for i in range(NUM_WORKERS):
            self.processes.append(ProcessManager(f"WORKER_{i:02d}", WORKER_CMD))
        
        self.running = True

    def make_dashboard(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        # Header
        header_text = Text("◈ CORTEX INDUSTRIAL SUPERVISOR v1.0 ◈", style="bold cyan")
        layout["header"].update(Panel(header_text, style="blue"))
        
        # Table of status
        table = Table(box=None, expand=True)
        table.add_column("PROCESS", style="bold white")
        table.add_column("STATUS", justify="center")
        table.add_column("UPTIME", justify="right")
        table.add_column("RESTARTS", justify="right")
        
        for p in self.processes:
            status_style = "green" if p.status == "ONLINE" else "red"
            table.add_row(
                p.name,
                f"[{status_style}]{p.status}[/]",
                p.get_uptime(),
                str(p.restarts)
            )
        
        layout["body"].update(Panel(table, title="Swarm Matrix", border_style="dim blue"))
        return layout

    def run(self):
        for p in self.processes:
            p.start()

        with Live(self.make_dashboard(), refresh_per_second=1, console=console) as live:
            try:
                while self.running:
                    for p in self.processes:
                        p.check()
                    live.update(self.make_dashboard())
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False
        for p in self.processes:
            p.stop()
        console.print("\n[bold red]∴ SYSTEM PURGE COMPLETE. ALL PROCESSES OFFLINE.[/]")

if __name__ == "__main__":
    sup = Supervisor()
    sup.run()
