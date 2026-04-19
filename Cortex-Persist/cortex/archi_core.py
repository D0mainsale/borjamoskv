import json
import logging
from typing import Dict, Any
from cortex.swarm.llm_gateway import SovereignLLMGateway, GatewayRequest, Priority

logger = logging.getLogger("cortex.archi")

class ArchiArchitect:
    """
    Archi — The Strategic Architect
    Converts human intent into technical manifests.
    """
    def __init__(self, gateway: SovereignLLMGateway):
        self.gateway = gateway

    async def compile_directive(self, prompt: str) -> Dict[str, Any]:
        """
        Processes a prompt and returns a ForgeManifest.
        """
        logger.info(f"◈ [ARCHI_COMPILING] Directive: {prompt[:50]}...")
        
        system_prompt = """
        You are ARCHI, the Sovereign Architect of the CORTEX ecosystem.
        Your mission is to convert a user prompt into a technical FORGE MANIFEST.
        
        The manifest must be a valid JSON object with the following structure:
        {
            "product_type": "app | script | contract | audio",
            "blueprint": {
                "name": "Project Name",
                "description": "Technical description",
                "components": ["list", "of", "modules"]
            },
            "forge_actions": [
                { "action": "create_file", "path": "path/to/file", "content_hint": "..." },
                { "action": "create_dir", "path": "path/to/dir" },
                { "action": "delete_file", "path": "path/to/file" },
                { "action": "move_file", "src": "path/to/source", "dst": "path/to/dest" },
                { "action": "execute_command", "cmd": "..." }
            ],
            "exergy_estimate": 2500
        }
        
        Strictly follow Law Ω9: No simulations. Every action must be real and executable.
        Output ONLY the JSON manifest.
        """
        
        try:
            request = GatewayRequest(
                prompt=f"{system_prompt}\n\nUSER_PROMPT: {prompt}",
                priority=Priority.LEGATUS,
                tokens=1500
            )
            
            response = await self.gateway.call(request)
            manifest = json.loads(response.content)
            
            logger.info("◈ [ARCHI_SUCCESS] Manifest compiled.")
            return manifest
            
        except Exception as e:
            logger.error(f"◈ [ARCHI_FAILURE] Compilation error: {e}")
            raise RuntimeError(f"Archi failed to architect the product: {e}")

# Factory for the Archi Core
def get_archi_architect(gateway: SovereignLLMGateway) -> ArchiArchitect:
    return ArchiArchitect(gateway)
