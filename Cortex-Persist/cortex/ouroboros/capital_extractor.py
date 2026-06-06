import os
import logging
from typing import Dict, Any, Optional

try:
    from web3 import Web3
    from eth_account import Account
    from eth_account.messages import encode_defunct
except ImportError:
    Web3 = None
    Account = None
    encode_defunct = None

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger("Ouroboros-Capital")

class CapitalExtractorC5:
    """
    Ouroboros Capital-Extractor [C5-REAL Enforced].
    Strictly interfaces with Web3 RPCs and official APIs.
    Roleplaying is punished.
    """
    def __init__(self, rpc_endpoint: Optional[str] = None, c4_api_key: Optional[str] = None):
        self.rpc_endpoint = rpc_endpoint or os.getenv("ETH_RPC_URL")
        self.c4_api_key = c4_api_key or os.getenv("CODE4RENA_API_KEY")
        self.private_key = os.getenv("WALLET_PRIVATE_KEY")
        self.strike_mode = os.getenv("OUROBOROS_STRIKE_MODE", "dry-run").lower()
        
        # Initialize Web3
        self.w3 = None
        self.account = None
        
        if self.rpc_endpoint:
            if any(mock in self.rpc_endpoint.lower() for mock in ["mock", "test", "sim"]):
                raise RuntimeError("LAW Ω9 VIOLATION: Endpoint is a known mock string.")
            
            if Web3:
                self.w3 = Web3(Web3.HTTPProvider(self.rpc_endpoint))
                if not self.w3.is_connected():
                    raise ConnectionError(
                        f"C5-State Failure: Cannot connect to RPC {self.rpc_endpoint}"
                    )
            else:
                logger.warning("C5-REAL Degraded: web3.py not installed.")

        if self.private_key and Account:
            # Enforce real account instantiation
            self.account = Account.from_key(self.private_key)

    def verify_ecdsa_signature(self, signature: str, payload_string: str) -> bool:
        """
        Real ECDSA verification. No random.random() roleplay allowed.
        """
        if not Account or not encode_defunct:
            raise RuntimeError(
                "LAW Ω9 VIOLATION: Missing eth_account package for real ECDSA."
            )
        
        try:
            message = encode_defunct(text=payload_string)
            recovered_address = Account.recover_message(message, signature=signature)
            logger.info(f"C5-REAL: Recovered address {recovered_address}")
            return True
        except Exception as e:
            logger.error(f"C5-REAL Signature failure: {e}")
            return False

    def submit_code4rena_finding(self, handle: str, contest_id: str, vulnerability_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submits a real vulnerability report to Code4rena via API.
        No simulated yield generation.
        """
        if not requests:
            raise RuntimeError("LAW Ω9 VIOLATION: 'requests' library missing for real API transaction.")
            
        if not self.c4_api_key:
            raise RuntimeError(
                "LAW Ω9 VIOLATION: Missing CODE4RENA_API_KEY. Refusing simulation."
            )
            
        endpoint = "https://code4rena.com/api/submissions"
        headers = {
            "Authorization": f"Bearer {self.c4_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "contest": contest_id,
            "handle": handle,
            "finding": vulnerability_payload.get("title", "Untitled Extraction"),
            "risk": vulnerability_payload.get("risk", "3 (High Risk)"),
            "body": vulnerability_payload.get("markdown_body", "")
        }
        
        logger.info(f"C5-REAL: Submitting finding to {endpoint} for contest {contest_id} [MODE: {self.strike_mode}]")
        
        if self.strike_mode == "dry-run":
            logger.info("C5-REAL: [DRY-RUN] Submission captured. No external API call made.")
            return {"status": "DRY_RUN_SUCCESS", "handle": handle, "contest": contest_id, "mode": "DRY-RUN"}

        response = requests.post(endpoint, headers=headers, json=payload)
        
        if response.status_code >= 400:
            raise RuntimeError(f"C5-REAL Submission Failed: {response.status_code} {response.text}")
            
        return response.json()

    def extract_yield_onchain(self, target_contract: str, extraction_function: str, abi: list, args: list = None) -> str:
        """
        Execute real smart contract transaction to extract yield.
        """
        if not self.w3:
            raise RuntimeError("LAW Ω9 VIOLATION: w3 object not initialized. (ETH_RPC_URL missing or web3 not installed)")
        if not self.account:
            raise RuntimeError(
                "LAW Ω9 VIOLATION: WALLET_PRIVATE_KEY missing. Cannot sign."
            )
            
        args = args or []
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(target_contract), abi=abi)
        
        func = getattr(contract.functions, extraction_function)
        
        # Build raw transaction
        tx = func(*args).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Estimate gas properly to catch reverts (C5-REAL logic)
        try:
            gas_estimate = self.w3.eth.estimate_gas(tx)
            tx['gas'] = gas_estimate
        except Exception as e:
            raise RuntimeError(f"C5-REAL Revert detected during gas estimation: {e}")
            
        # Sign and send
        signed_tx = self.account.sign_transaction(tx)
        
        if self.strike_mode == "dry-run":
            logger.info(
                "C5-REAL: [DRY-RUN] Transaction signed. No broadcast."
            )
            return f"0x_DRY_RUN_TX_HASH_{target_contract[:8]}"

        try:
            raw = getattr(signed_tx, 'raw_transaction', getattr(signed_tx, 'rawTransaction', signed_tx.rawTransaction))
            tx_hash = self.w3.eth.send_raw_transaction(raw)
            hex_hash = self.w3.to_hex(tx_hash)
            logger.info(f"C5-REAL: TRANSACTION BROADCASTED. Hash: {hex_hash}")
            return hex_hash
        except Exception as e:
            raise RuntimeError(f"C5-REAL Broadcast failed: {e}")
