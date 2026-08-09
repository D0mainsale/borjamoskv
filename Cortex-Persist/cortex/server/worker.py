"""
cortex.server.worker.py
================
The execution engine of the Agents.archi swarm.
Pulls tasks from IndustrialQueue and executes agent logic.
"""

import time
import uuid
import logging
import traceback
from typing import Dict, Any

from cortex.server.queue import IndustrialQueue

# Industrial Noir Logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[2m%(asctime)s\033[0m \033[38;5;33m\033[1mWORKER\033[0m %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("cortex-worker")

class CortexWorker:
    def __init__(self, worker_id: str = None):
        self.worker_id = worker_id or f"WORKER-{uuid.uuid4().hex[:6].upper()}"
        self.queue = IndustrialQueue()
        self.running = False
        
        # Registry of task handlers
        self.handlers = {
            "HUNT": self.handle_hunt,
            "SCOUT": self.handle_scout
        }

    def handle_hunt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Bridge to cortex.tools.bounty_hunter.py logic."""
        logger.info(f"Targeting: {payload.get('repo_url', 'unknown')}")
        
        try:
            from cortex.tools.bounty_hunter import hunt
            result = hunt(
                task_label=payload.get("name", "Remote Task"),
                platform=payload.get("platform", "unknown"),
                repo_url=payload.get("repo_url"),
                reward_usd=payload.get("reward", 0)
            )
            return result
        except Exception as e:
            logger.error(f"Hunt Execution Error: {e}")
            return {"status": "error", "error": str(e)}

    def handle_scout(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Bridge to cortex.tools.bounty_scout.py logic."""
        logger.info("Executing Recon phase...")
        try:
            from cortex.tools.bounty_scout import scout
            result = scout(
                min_reward=payload.get("min_reward", 1000),
                max_count=payload.get("max_count", 20),
                auto_enqueue=True  # Auto-link scout -> hunt
            )
            return result
        except Exception as e:
            logger.error(f"Scout Execution Error: {e}")
            return {"status": "error", "error": str(e)}

    def run(self):
        logger.info(f"Sovereign Worker {self.worker_id} \033[38;5;46mONLINE\033[0m")
        self.running = True
        
        while self.running:
            try:
                task = self.queue.claim(self.worker_id)
                if task:
                    task_id = task["id"]
                    task_type = task["task_type"]
                    payload = json.loads(task["payload"])
                    
                    logger.info(f"Claimed Task \033[1m#{task_id}\033[0m [{task_type}]")
                    
                    handler = self.handlers.get(task_type)
                    if handler:
                        try:
                            result = handler(payload)
                            self.queue.complete(task_id, result)
                            logger.info(f"Task \033[1m#{task_id}\033[0m \033[38;5;46mCOMPLETED\033[0m")
                        except Exception as e:
                            logger.error(f"Task \033[1m#{task_id}\033[0m \033[38;5;196mFAILED\033[0m: {e}")
                            self.queue.fail(task_id, traceback.format_exc())
                    else:
                        logger.warning(f"No handler for task type: {task_type}")
                        self.queue.fail(task_id, f"Unknown task type: {task_type}")
                else:
                    # Idle: high-latency aware polling
                    time.sleep(2)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    import json
    worker = CortexWorker()
    worker.run()
