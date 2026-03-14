import os
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

CONTRACT_ABI_PATH = (
    Path(__file__).parent.parent.parent
    / "contracts"
    / "artifacts"
    / "contracts"
    / "DocumentVerification.sol"
    / "DocumentVerification.json"
)


@dataclass
class BlockchainResult:
    tx_hash: str
    block_number: int
    contract_address: str
    polygonscan_url: str


def _get_w3() -> Web3:
    from web3.middleware import geth_poa_middleware
    rpc_url = os.environ["POLYGON_RPC_URL"]
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def _get_contract(w3: Web3):
    contract_address = os.environ["CONTRACT_ADDRESS"]
    abi_json = json.loads(CONTRACT_ABI_PATH.read_text())
    abi = abi_json["abi"]
    return w3.eth.contract(
        address=w3.to_checksum_address(contract_address),
        abi=abi,
    )


def _get_account_address() -> str:
    private_key = os.environ["DEPLOYER_PRIVATE_KEY"]
    from eth_account import Account
    return Account.from_key(private_key).address


def store_verification(
    applicant_id: str,
    doc_hashes: list[bytes],
    confidence: int,
    is_verified: bool,
) -> BlockchainResult | None:
    try:
        w3 = _get_w3()
        contract = _get_contract(w3)
        account_address = _get_account_address()
        private_key = os.environ["DEPLOYER_PRIVATE_KEY"]
        contract_address = os.environ["CONTRACT_ADDRESS"]

        # Convert raw bytes to bytes32
        doc_hashes_bytes32 = [h[:32].ljust(32, b"\x00") for h in doc_hashes]

        fn = contract.functions.storeVerification(
            applicant_id,
            doc_hashes_bytes32,
            confidence,
            is_verified,
        )

        # Estimate actual gas needed (much cheaper than hardcoded 300k)
        estimated_gas = fn.estimate_gas({"from": account_address})
        gas_limit = int(estimated_gas * 1.1)  # 10% safety buffer

        tx = fn.build_transaction({
            "from": account_address,
            "nonce": w3.eth.get_transaction_count(account_address),
            "gas": gas_limit,
            "gasPrice": w3.eth.gas_price,
        })

        signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=60)

        raw_hex = receipt.transactionHash.hex()
        tx_hash = raw_hex if raw_hex.startswith("0x") else "0x" + raw_hex

        return BlockchainResult(
            tx_hash=tx_hash,
            block_number=receipt.blockNumber,
            contract_address=contract_address,
            polygonscan_url=f"https://amoy.polygonscan.com/tx/{tx_hash}",
        )

    except Exception as e:
        logger.error(f"Blockchain write failed: {e}")
        return None
