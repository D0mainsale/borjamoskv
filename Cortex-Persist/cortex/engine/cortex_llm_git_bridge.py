"""
CORTEX-LLM: Git Sentinel Bridge (C5-REAL)
=========================================
Acopla la salida inmutable del Motor Termodinámico (Deltas Estructurales)
con el sistema de archivos y dispara el ciclo de Pre-Commit + Git Commit de CORTEX.
"""
import os
import subprocess
import logging
from typing import List, Dict, Any
from pathlib import Path
from cortex.engine.cortex_llm import ThermodynamicDelta

logger = logging.getLogger("cortex_llm_git_bridge")

class SentinelBridge:
    """Cristaliza deltas físicos y audita la entropía vía pre-commit."""
    def __init__(self, workspace_root: str):
        self.workspace = Path(workspace_root)
        if not self.workspace.exists():
            raise FileNotFoundError(f"CORTEX-LLM Workspace inválido: {workspace_root}")

    def apply_delta_and_crystallize(self, delta: ThermodynamicDelta, commit_msg: str) -> str:
        """
        Aplica los deltas JSON (operaciones sobre archivos).
        Luego invoca al Git Sentinel para auto-validación.
        Si la validación falla (Linter/Types/Tests), revierte el FS o 
        devuelve el error al motor LLM para la auto-curación.
        """
        logger.info(f"[CORTEX-LLM] Aplicando Deltas. Confianza: {delta.confidence}")
        
        # 1. Aplicación de deltas al FileSystem (Simplificado L0)
        for op in delta.operations:
            self._apply_fs_op(op)
            
        # 2. Invocación de Git Sentinel (Anergia Purge & BFT Validation)
        try:
            logger.info("[CORTEX-LLM] Ejecutando Sentinel (Pre-commit Audit)...")
            subprocess.run(
                [".git/hooks/pre-commit"], 
                cwd=str(self.workspace), 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            logger.info("[CORTEX-LLM] Pre-commit superado. Procediendo a Cristalización Git.")
            subprocess.run(
                ["git", "add", "."], 
                cwd=str(self.workspace), 
                check=True
            )
            
            subprocess.run(
                ["git", "commit", "-m", f"feat(cortex-llm/autopoiesis): {commit_msg}"],
                cwd=str(self.workspace),
                check=True,
                capture_output=True,
                text=True
            )
            
            return "Cristalización exitosa. Git Ledger Mutado."
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Fallo en BFT Pre-commit. Anergia detectada. \n{e.stderr or e.stdout}")
            subprocess.run(["git", "restore", "."], cwd=str(self.workspace)) # Turbo-Rollback
            raise RuntimeError(f"CORTEX-LLM Mutación abortada. Falló el Gate C5-REAL.\n{e.stderr or e.stdout}")

    def _apply_fs_op(self, op: Dict[str, Any]):
        action = op.get("op")
        target_path = self.workspace / op.get("path", "")
        
        if not op.get("path"):
            return
            
        if action == "replace" or action == "create":
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(op.get("content", ""))
        elif action == "delete":
            if target_path.exists():
                target_path.unlink()
        else:
            logger.warning(f"Operación no soportada por el Bridge: {action}")
