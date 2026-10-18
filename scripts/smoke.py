import json
import os
import re
import time

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
import genlayer_py.contracts.actions as contract_actions


def compatible_calldata(method=None, args=None, kwargs=None):
    output = {}
    if method is not None:
        output["method"] = method
    if args:
        output["args"] = args
    if kwargs:
        output["kwargs"] = kwargs
    return output


contract_actions.make_calldata_object = compatible_calldata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.abspath(os.path.join(ROOT, "..", "..", "..", ".."))


def value(name):
    with open(os.path.join(WORKSPACE, "accounts.env"), encoding="utf-8") as handle:
        text = handle.read()
    return re.search(rf'^\s*{name}\s*=\s*"?([^"\r\n]+)', text, re.M).group(1).strip()


shipper = create_account(account_private_key=value("ACCOUNT_3_GENLAYER_PRIVATE_KEY"))
receiver = create_account(account_private_key=value("ACCOUNT_1_GENLAYER_PRIVATE_KEY"))
client = create_client(chain=studionet, account=shipper)
with open(os.path.join(ROOT, "deployment.json"), encoding="utf-8") as handle:
    address = json.load(handle)["contract"]


def write(name, args):
    tx_hash = client.write_contract(address=address, function_name=name, args=args)
    print(name + "Tx", tx_hash, flush=True)
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx_hash,
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
        raise SystemExit(name + " failed")
    return str(tx_hash)


lot_id = "CCS-SMOKE-" + str(int(time.time()))
transactions = {
    "seal": write(
        "seal_lot",
        [
            lot_id,
            receiver.address,
            "Synthetic calibration lot; no physical goods",
            "https://github.com/sanshos1/cold-chain-seal",
            "https://offcut-relay.ranko5180.chatgpt.site",
        ],
    )
}
transactions["cancel"] = write("cancel_before_receipt", [lot_id])
stored = client.read_contract(address=address, function_name="get_lot", args=[lot_id])
if stored.get("state") != "CANCELLED" or stored.get("shipper", "").lower() != shipper.address.lower():
    raise SystemExit("canonical readback mismatch")
output = {
    "recordType": "synthetic authorization smoke test; no physical shipment or safety disposition",
    "lotId": lot_id,
    "contractAddress": address,
    "transactions": transactions,
    "readback": stored,
}
os.makedirs(os.path.join(ROOT, "evidence"), exist_ok=True)
with open(os.path.join(ROOT, "evidence", "live-run.json"), "w", encoding="utf-8") as handle:
    json.dump(output, handle, indent=2)
print(json.dumps(output), flush=True)
