# AGENTS.md — CORTEX-Persist Project Rules

## Existence-Gap & Package Invariants
- **Qualified Imports Only**: All internal module imports must be fully qualified relative to the root package (`from cortex.subpackage import module`) or explicitly relative (`from .module import symbol`). NEVER use unqualified top-level imports for internal modules (e.g. `import memoria` or `import sovereign_proxy`), which risks PyPI package shadowing and local path resolution failures.
- **Security Control Surface**: Security controls, verification membranes, and integrity hooks implemented in submodules MUST be explicitly re-exported in the top-level package `__init__.py` (e.g. `from .membrana import guard_and_commit_sync`).
- **Manifest Completeness**: Every third-party PyPI dependency used in code must be declared in `pyproject.toml`. Top-level namespace imports (such as `import google`) require declaring their corresponding distribution packages (e.g. `protobuf`, `google-genai`).
- **Component Styling Completeness**: Any React component importing a stylesheet (`import './Component.css'`) must have the corresponding CSS file present in the tree adhering to the Industrial Noir 2026 design system tokens.
