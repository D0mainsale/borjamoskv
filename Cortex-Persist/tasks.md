# CORTEX-Persist — Task Backlog (Ralph Protocol)

> Formato: `- [ ]` pendiente · `- [/]` en progreso · `- [x]` completada
> Ralph lee este archivo, elige UNA tarea incompleta y la ejecuta.

---

## Backlog

- [ ] **Audit cortex_3min_demo.sh** — El archivo contiene una API key expuesta en la línea 1 (`sk-or-v1-...`). Eliminar la key, limpiarla del historial git (si aplica), y añadir un `.env.example` con placeholder. Añadir `*.env` y archivos de secrets al `.gitignore`.

- [ ] **Crear `cortex_core/__init__.py`** — El módulo `cortex_core` no tiene `__init__.py`. Crear el archivo con docstring de módulo y exports de las clases principales que existan dentro del directorio.

- [ ] **Añadir `README` a `cortex_swarm/`** — Documentar la arquitectura del swarm: qué agentes existen, cómo se invocan, qué protocolo de comunicación usan (A2A, Blackboard, etc.).

- [ ] **Health-check script** — Crear `cortex_health.sh`: script que valide que Python >= 3.11, que `pyproject.toml` tiene todas las deps instaladas (`pip check`), que los subdirectorios críticos existen, y que imprima un resumen PASS/FAIL en estilo Industrial Noir.

- [ ] **Normalizar pyproject.toml** — Añadir `[project]` metadata completa: `name`, `version`, `description`, `authors`, `requires-python = ">=3.11"`, y mover las dependencias sueltas al bloque `[project.dependencies]` correcto.

---

## Progreso

<!-- Ralph documenta aquí cada ciclo completado -->
