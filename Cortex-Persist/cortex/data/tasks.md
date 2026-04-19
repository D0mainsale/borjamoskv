# CORTEX-Persist — Task Backlog (Ralph Protocol)

> Formato: `- [ ]` pendiente · `- [/]` en progreso · `- [x]` completada
> Ralph lee este archivo, elige UNA tarea incompleta y la ejecuta.

---

## Backlog

- [x] **Mythos Simulation: Step 14** — SQLi -> XSS Escalation. Escalada exitosa desde DB a navegador de usuario.
- [/] **Mythos Simulation: Step 15-20** — Insecure Deserialization Strike. Pivoteando hacia RCE en el servidor. Script `cortex.tools.cortex_strike_deserialization.py` operacional.

- [ ] **Audit cortex_3min_demo.sh** — El archivo contiene una API key expuesta en la línea 1 (`sk-or-v1-...`). Eliminar la key, limpiarla del historial git (si aplica), y añadir un `.env.example` con placeholder. Añadir `*.env` y archivos de secrets al `.gitignore`.

- [ ] **Crear `cortex.core/__init__.py`** — El módulo `cortex.core` no tiene `__init__.py`. Crear el archivo con docstring de módulo y exports de las clases principales que existan dentro del directorio.

- [ ] **Añadir `README` a `cortex.swarm/`** — Documentar la arquitectura del swarm: qué agentes existen, cómo se invocan, qué protocolo de comunicación usan (A2A, Blackboard, etc.).

- [ ] **Health-check script** — Crear `cortex_health.sh`: script que valide que Python >= 3.11, que `pyproject.toml` tiene todas las deps instaladas (`pip check`), que los subdirectorios críticos existen, y que imprima un resumen PASS/FAIL en estilo Industrial Noir.

- [ ] **Normalizar pyproject.toml** — Añadir `[project]` metadata completa: `name`, `version`, `description`, `authors`, `requires-python = ">=3.11"`, y mover las dependencias sueltas al bloque `[project.dependencies]` correcto.

---

## Progreso

<!-- Ralph documenta aquí cada ciclo completado -->


## 🎯 Bounty Queue — 2026-04-15 (Mythos x10 Forced)
<!-- Manual injection for high-priority targets -->
- [ ] [BOUNTY·CODE4RENA] GMX V2 Upgrade | reward=$100k | score=0.850 | repo=https://github.com/gmx-io/gmx-synthetics | url=https://code4rena.com/contests/2026-04-gmx-v2
- [ ] [BOUNTY·SHERLOCK] Usual Protocol Expansion | reward=$150k | score=0.850 | repo=https://github.com/usual-money/usual-contracts | url=https://audits.sherlock.xyz/contests/usual
- [ ] [BOUNTY·IMMUNEFI] Lido Finance Core | reward=$2000k | score=0.850 | repo=https://github.com/lidofinance/lido-dao | url=https://immunefi.com/bounty/lido/
- [ ] [BOUNTY·CODE4RENA] Aave V3.1 Maintenance | reward=$50k | score=0.850 | repo=https://github.com/aave/aave-v3-core | url=https://code4rena.com/contests/2026-04-aave-v3-1
