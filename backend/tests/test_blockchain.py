import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from pipeline.blockchain import store_verification, BlockchainResult


def _make_mock_w3(tx_hash_hex: str = "0x" + "ab" * 32, block_number: int = 12345):
    mock_w3 = MagicMock()
    mock_receipt = MagicMock()
    mock_receipt.transactionHash = bytes.fromhex(tx_hash_hex[2:])
    mock_receipt.blockNumber = block_number
    mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt
    mock_w3.eth.get_transaction_count.return_value = 1
    mock_w3.eth.gas_price = 30_000_000_000
    mock_w3.eth.account.sign_transaction.return_value = MagicMock(
        rawTransaction=b"raw_tx"
    )
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex(tx_hash_hex[2:])
    mock_w3.to_checksum_address = lambda x: x
    return mock_w3


_TEST_ENV = {
    "CONTRACT_ADDRESS": "0xTEST000000000000000000000000000000000001",
    "DEPLOYER_PRIVATE_KEY": "0x" + "aa" * 32,
    "POLYGON_RPC_URL": "https://rpc-amoy.polygon.technology/",
}


def test_store_verification_returns_result(mocker):
    mock_w3 = _make_mock_w3()
    mock_contract = MagicMock()
    mock_contract.functions.storeVerification.return_value.build_transaction.return_value = {
        "gas": 200000, "gasPrice": 30_000_000_000, "nonce": 1, "data": "0x"
    }

    mocker.patch.dict("os.environ", _TEST_ENV)
    mocker.patch("pipeline.blockchain._get_w3", return_value=mock_w3)
    mocker.patch("pipeline.blockchain._get_contract", return_value=mock_contract)
    mocker.patch("pipeline.blockchain._get_account_address", return_value="0xDEAD")

    result = store_verification("UK-2024-00183", [b"a" * 32], 91, True)

    assert isinstance(result, BlockchainResult)
    assert result.block_number == 12345
    assert result.tx_hash.startswith("0x")
    assert result.contract_address == _TEST_ENV["CONTRACT_ADDRESS"]


def test_store_verification_failure_returns_none(mocker):
    mocker.patch("pipeline.blockchain._get_w3", side_effect=Exception("RPC unreachable"))

    result = store_verification("UK-2024-00183", [b"a" * 32], 91, True)
    assert result is None


def test_blockchain_result_has_polygonscan_url(mocker):
    mock_w3 = _make_mock_w3()
    mock_contract = MagicMock()
    mock_contract.functions.storeVerification.return_value.build_transaction.return_value = {
        "gas": 200000, "gasPrice": 30_000_000_000, "nonce": 1, "data": "0x"
    }

    mocker.patch.dict("os.environ", _TEST_ENV)
    mocker.patch("pipeline.blockchain._get_w3", return_value=mock_w3)
    mocker.patch("pipeline.blockchain._get_contract", return_value=mock_contract)
    mocker.patch("pipeline.blockchain._get_account_address", return_value="0xDEAD")

    result = store_verification("UK-2024-00183", [b"a" * 32], 91, True)
    assert result is not None
    assert "amoy.polygonscan.com" in result.polygonscan_url
