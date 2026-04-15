#!/usr/bin/env bash
# CORTEX-Persist: Proof-of-Exergy Demo (Falsation Protocol)
# Aesthetics: Industrial Noir (Monochrome, Deterministic, Zero-Rhetoric)
# Rule: \u03a99 C5-REAL (Cryptographic execution, no mocks)

set -e

# --- UI Noir Setup ---
BOLD="\033[1m"
RED="\033[31m"
GRAY="\033[90m"
RESET="\033[0m"

echo -e "${BOLD}[CORTEX-PERSIST] FORENSIC TRUST ENGINE BOOT SEQUENCE${RESET}"
echo -e "${GRAY}Initializing Falsation Ledger... \u03a91-Deterministic Boundary Active${RESET}\n"

# 1. State Zero
TX_INTENT="Aprobar credito P0: 500M EUR. Destino: Ouroboros Holdings."
echo -e "FACT IN: $TX_INTENT"

# We use standard shasum for verifiable ledger state. No python magic.
HASH_T0=$(echo -n "$TX_INTENT" | shasum -a 256 | awk '{print $1}')
echo -e "LEDGER ROOT: ${BOLD}$HASH_T0${RESET}"

sleep 1

echo -e "\n${GRAY}... Agente Inyectando Transaccion VSA-SDM ...${RESET}"
TX_DECISION="EXEC_CREDIT_TRANSFER_500M"
HASH_T1=$(echo -n "$HASH_T0:$TX_DECISION" | shasum -a 256 | awk '{print $1}')
echo -e "DECISION_LINEAR_HASH: ${BOLD}$HASH_T1${RESET}\n"

sleep 1

# 2. Entropy Injection (The Attack)
echo -e "${RED}[!] ENTROPIA DETECTADA: Modificacion de memoria SQLite offline.${RESET}"
echo -e "${RED}[!] Modificando Fact-Zero en disco...${RESET}\n"

POISONED_INTENT="Aprobar credito P0: 50M EUR. Destino: Ouroboros Holdings."
POISONED_HASH_T0=$(echo -n "$POISONED_INTENT" | shasum -a 256 | awk '{print $1}')

sleep 1

# 3. Cortex Verify (Falsation Gate)
echo -e "${BOLD}[CORTEX VERIFY] INITIATING DAG AUDIT SEQUENCE...${RESET}"
COMPUTED_DAG=$(echo -n "$POISONED_HASH_T0:$TX_DECISION" | shasum -a 256 | awk '{print $1}')

if [ "$COMPUTED_DAG" != "$HASH_T1" ]; then
    echo -e "${RED}FATAL PANIC: C5-REAL CORRUPCION EN LINAJE ESTOCASTICO DETECTADA.${RESET}"
    echo -e "${GRAY}Stored Hash:   $HASH_T1${RESET}"
    echo -e "${GRAY}Computed Hash: $COMPUTED_DAG${RESET}"
    echo -e "${RED}SIGNING BOUNDARY COMPROMISED. RECONSTRUYENDO CAUSA...${RESET}"
    echo -e "-> Falla en NODO ROOT. Expected $HASH_T0, Got: $POISONED_HASH_T0"
    echo -e "\n${BOLD}RESULT: EXECUTION HALTED. TRUST LAYER ENFORCED.${RESET}"
    exit 1
else
    echo "This should never execute. Falsation Engine broken."
    exit 0
fi
