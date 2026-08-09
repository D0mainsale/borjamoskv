import os
import subprocess
import logging
from typing import Dict, List, Any

logger = logging.getLogger("cortex.forge")

class ArchiForge:
    """
    The Forge — Execution Layer
    Transmutes digital blueprints into physical/executable assets.
    """
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def execute_manifest(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes a sequence of actions from a manifest.
        """
        actions = manifest.get("forge_actions", [])
        results = []
        
        logger.info(f"⚙ [FORGE_IGNITION] Executing {len(actions)} actions.")
        
        for action in actions:
            try:
                result = self._dispatch_action(action)
                results.append({"action": action.get("action"), "status": "success", "detail": result})
            except Exception as e:
                logger.error(f"⚙ [FORGE_CRITICAL] Action failed: {e}")
                results.append({"action": action.get("action"), "status": "failed", "error": str(e)})
                
        return results

    def _dispatch_action(self, action: Dict[str, Any]) -> str:
        name = action.get("action")
        
        if name == "create_file":
            path = self._safe_path(action.get("path"))
            content = action.get("content_hint", "")
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Created file: {path}"
            
        elif name == "create_dir":
            path = self._safe_path(action.get("path"))
            os.makedirs(path, exist_ok=True)
            return f"Created directory: {path}"

        elif name == "delete_file":
            path = self._safe_path(action.get("path"))
            if os.path.exists(path):
                os.remove(path)
                return f"Deleted file: {path}"
            return f"File not found, skip delete: {path}"

        elif name == "move_file":
            src = self._safe_path(action.get("src"))
            dst = self._safe_path(action.get("dst"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst)
            return f"Moved {src} to {dst}"

        elif name == "execute_command":
            cmd = action.get("cmd")
            # WARNING: Law Ω6 mandates SafeToAutoRun
            process = subprocess.run(cmd, shell=False, capture_output=True, text=True, cwd=self.workspace_root)
            if process.returncode != 0:
                raise RuntimeError(f"Command failed: {process.stderr}")
            return f"Executed command: {cmd[:50]}..."
            
        else:
            raise ValueError(f"Unknown forge action: {name}")

    def _safe_path(self, relative_path: str) -> str:
        """Enforces Law Ω6: Jailbreak prevention."""
        if not relative_path:
            raise ValueError("Empty path provided to Forge.")
        
        full_path = os.path.abspath(os.path.join(self.workspace_root, relative_path))
        if not full_path.startswith(os.path.abspath(self.workspace_root)):
            raise PermissionError(f"Forge path outside workspace: {relative_path}")
        return full_path

def get_archi_forge(workspace_root: str) -> ArchiForge:
    return ArchiForge(workspace_root)
