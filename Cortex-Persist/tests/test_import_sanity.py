import importlib
import pytest

MODULES_TO_TEST = [
    "cortex.sovereign",
    "cortex.sovereign.cronos",
    "cortex.sovereign.memoria",
    "cortex.server.main",
    "cortex.server.stellar_strike_v1",
    "cortex.core.autodream",
    "cortex.ouroboros.ouroboros.core.security",
    "cortex.ouroboros.ouroboros.core.protocols",
    "cortex.ouroboros.ouroboros.core.context",
]

@pytest.mark.parametrize("module_name", MODULES_TO_TEST)
def test_import_resolves(module_name):
    """
    Smoke test to ensure critical modules resolve correctly without ImportErrors.
    This prevents regressions of existence gaps or phantom symbols.
    """
    try:
        importlib.import_module(module_name)
    except Exception as e:
        pytest.fail(f"Failed to import {module_name}: {e}")
