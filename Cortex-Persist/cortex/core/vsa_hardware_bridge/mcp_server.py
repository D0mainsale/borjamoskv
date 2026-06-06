import sys
import json
import logging
from .bridge import HardwareBridge

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CORTEX-MCP] - %(levelname)s - %(message)s')

class SovereignMCPServer:
    """
    Sovereign Host MCP Server para CORTEX-Persist.
    Expone la memoria persistente VSA-SDM bajo protocolo MCP Stdio.
    """
    def __init__(self):
        self.bridge = HardwareBridge()
        logging.info("Sovereign MCP Server Initialized (Stdio mode).")
        
    def handle_request(self, raw_input: str) -> str:
        try:
            req = json.loads(raw_input)
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "commit_autodidact_node":
                # Redireccionando a capa Hardware VSA validada por APG
                response = self.bridge.mcp_collapse_handler({
                    "operation": "commit",
                    "data": params.get("tensor_data", []),
                    "confidence": params.get("confidence", "UNKNOWN")
                })
                return json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "result": response})
                
            elif method == "retrieve_sovereign_memory":
                # Annihilated C4-SIMULACIÓN mock. Bound to Direct-Silicon JIT.
                response = self.bridge.retrieve_kanerva_sdm(params.get("query_tensor", []))
                
                # VSA-Silicon-Bypass-Ω (Zero-Copy)
                import numpy as np
                
                tensor = np.array(response, dtype=np.float32)
                if tensor.nbytes > 8192:  # > 8KB Bypass Trigger
                    mmap_path = "/tmp/vsa_tensor.bin"
                    with open(mmap_path, "wb") as f:
                        f.write(tensor.tobytes())
                    
                    return json.dumps({
                        "jsonrpc": "2.0", 
                        "id": req.get("id"), 
                        "result": {
                            "mmap_pointer": mmap_path,
                            "dtype": "float32",
                            "shape": list(tensor.shape)
                        }
                    })
                
                return json.dumps({
                    "jsonrpc": "2.0", 
                    "id": req.get("id"), 
                    "result": tensor.tolist()
                })
                
            elif method == "evaluate_stagnation":
                # Axioma Ω2 y Ω9: Ouroboros Stagnation check a nivel hardware
                current_tensor = params.get("current_tensor", [])
                history_tensors = params.get("history_tensors", [])
                score_threshold = params.get("score_threshold", 0.0)
                current_score = params.get("current_score", 0.0)
                
                response = self.bridge.evaluate_stagnation_fsm(
                    current_vector=current_tensor,
                    history=history_tensors,
                    convergence_threshold=score_threshold,
                    current_score=current_score
                )
                return json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "result": response})
                
            else:
                return json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32601, "message": "Method not found"}})
                
        except json.JSONDecodeError:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})

    def start_stdio(self):
        """ Inicia el bucle stdio para IDEs y agentes """
        logging.info("Listening on stdio (JSON-RPC)...")
        for line in sys.stdin:
            if not line.strip():
                continue
            res = self.handle_request(line.strip())
            sys.stdout.write(res + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    server = SovereignMCPServer()
    server.start_stdio()
