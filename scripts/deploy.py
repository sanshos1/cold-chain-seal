import json
import os
import re

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.abspath(os.path.join(ROOT, "..", "..", "..", ".."))


def account_value(name):
    with open(os.path.join(WORKSPACE, "accounts.env"), encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(rf'^\s*{name}\s*=\s*"?([^"\r\n]+)', text, re.M)
    if not match:
        raise SystemExit(name + " is missing")
    return match.group(1).strip()


def address_from(value):
    if isinstance(value, dict):
        if value.get("recipient") and str(value.get("tx_execution_result", "")) == "1":
            return value["recipient"]
        for key, item in value.items():
            if key in ("contract_address", "contractAddress") and isinstance(item, str):
                return item
            found = address_from(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = address_from(item)
            if found:
                return found


account = create_account(account_private_key=account_value("ACCOUNT_3_GENLAYER_PRIVATE_KEY"))
if account_value("ACCOUNT_3_GITHUB_USERNAME") != "sanshos1":
    raise SystemExit("account slot mismatch")
if account.address.lower() != "0xAD049E0Edc298C97552eD60071a35bfc60181FD4".lower():
    raise SystemExit("wallet mismatch")
client = create_client(chain=studionet, account=account)
with open(os.path.join(ROOT, "contracts", "contract.py"), encoding="utf-8") as handle:
    source = handle.read()
transaction = client.deploy_contract(code=source, args=[])
print("deployTx", transaction, flush=True)
receipt = client.wait_for_transaction_receipt(
    transaction_hash=transaction,
    wait_until="finalized",
    retries=180,
    interval=5000,
    full_transaction=True,
)
leaders = receipt.get("consensus_data", {}).get("leader_receipt") or []
leaders = [leaders] if isinstance(leaders, dict) else leaders
if receipt.get("result_name") != "MAJORITY_AGREE" or not any(
    item.get("execution_result") == "SUCCESS" for item in leaders
):
    raise SystemExit("deployment did not finalize successfully")
address = address_from(receipt)
if not address:
    raise SystemExit("finalized receipt did not expose a contract address")
output = {
    "contract": address,
    "deployTx": str(transaction),
    "network": "StudioNet",
    "deployer": account.address,
    "status": "FINALIZED",
    "consensus": "MAJORITY_AGREE",
    "execution": "SUCCESS",
}
with open(os.path.join(ROOT, "deployment.json"), "w", encoding="utf-8") as handle:
    json.dump(output, handle, indent=2)
print(json.dumps(output, indent=2), flush=True)

