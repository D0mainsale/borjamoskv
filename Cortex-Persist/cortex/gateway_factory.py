import asyncio
import logging
from cortex.swarm.llm_gateway import SovereignLLMGateway, ModelSpec

logger = logging.getLogger("cortex.gateway_factory")

async def _default_call(prompt: str) -> str:
    """
    Default fallback/stub logic for C4-SIMULATION.
    In a real production environment, this would call Gemini, OpenAI, or local Llama.
    """
    await asyncio.sleep(0.1)
    # If the prompt contains 'ARCHI', return a valid JSON manifest for a landing page
    if "ARCHI" in prompt.upper() and "MANIFEST" in prompt.upper():
        return '{ "product_type": "app", "blueprint": { "name": "Agents.Archi Landing", "description": "Sovereign UI" }, "forge_actions": [ { "action": "create_file", "path": "index.html", "content_hint": "<html><body style=\'background:#0A0A0A;color:#2BE58B;font-family:monospace;\'><h1>∴ AGENTS.ARCHI</h1><p>PROVENANCE: C5-REAL</p></body></html>" } ], "exergy_estimate": 2500 }'
    
    return f"Response to: {prompt[:50]}..."

def get_standard_gateway() -> SovereignLLMGateway:
    """
    Returns a configured SovereignLLMGateway with standard model tiers.
    """
    specs = [
        ModelSpec(
            name="gemini-2.0-pro-exp",
            tpm_max=1_000_000,
            call=_default_call,
            tier=0
        ),
        ModelSpec(
            name="llama-3.1-405b-fallback",
            tpm_max=2_000_000,
            call=_default_call,
            tier=1
        )
    ]
    
    return SovereignLLMGateway(models=specs)
