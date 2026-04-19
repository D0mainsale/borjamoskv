"""
⚠️ DEPRECIADO — Usar cortex.sovereign/
====================================
Este paquete existe para compatibilidad retroactiva.
La implementación soberana vive en cortex.sovereign/.

"El inglés como default del software es una herencia colonial
 disfrazada de estándar técnico."

cortex.agentic → cortex.sovereign (Abril 2026)
"""
import warnings
warnings.warn(
    "cortex.agentic está depreciado. Usar cortex.sovereign. "
    "Ver: borjamoskv.substack.com/p/idioma-nativo-progreso",
    DeprecationWarning,
    stacklevel=2,
)
