# Cold Chain Seal

## Receiving bench, lot still closed

A temperature log is not a verdict. It becomes useful only when it is read against the exact stability specification, attached to the right custody manifest, and reconciled with what the receiver actually found.

Cold Chain Seal gives the receiver—not the shipper—the last operational word. The shipper opens a lot with a named counterparty and two frozen references. The receiver supplies an immutable sensor export and their receiving inspection. GenLayer validators retrieve all four sources, identify attributable excursion intervals, and settle one of three bounded dispositions:

| Mark | Meaning |
| --- | --- |
| `RELEASE` | no retained exception or condition |
| `CONDITIONAL` | usable only under explicit closed conditions |
| `QUARANTINE` | missing identity, unverifiable excursion, or incompatible evidence |

The receiver then signs the operational handoff with a note. The stored state becomes `RECEIVED` or `QUARANTINED`; the shipper cannot overwrite it.

## Seal sequence

1. `seal_lot` — shipper fixes lot ID, receiver, product, stability specification, and custody manifest.
2. `inspect_receipt` — receiver adds sensor export and physical receiving record; validators compare all four.
3. `acknowledge` — receiver records the disposition note and closes the lot.
4. `cancel_before_receipt` — shipper may withdraw only while the seal is untouched.

Identifiers are normalized once and duplicates fail instead of overwriting history. Four source slots must use four different HTTPS origins. Stored evidence includes URL order, SHA-256 digests, bounded exception intervals with `source_index`, closed conditions, rationale, and the two counterparties.

## The trust label

Host diversity does not prove organizational independence, and a file called “sensor export” is not automatically signed telemetry. Production use must establish who controls each origin, how the sensor export is authenticated, which product specification is authoritative, and who is authorized to receive the lot. These checks are deliberately documented rather than implied.

This contract records a reproducible receiving disposition. It does not replace regulated release procedures, laboratory testing, or a qualified safety decision.

## Bench checks

```bash
python -m pytest -q
genvm-lint lint contracts/contract.py
```

## StudioNet release

The reviewed source at commit `ee1e52e98365c9e5555a862ba412060df36589d3` is deployed at [`0x451482b35d803b9f04f0F1a4A738414d606B7356`](https://explorer-studio.genlayer.com/address/0x451482b35d803b9f04f0F1a4A738414d606B7356). Deployment finalized with `MAJORITY_AGREE / SUCCESS`; the receipt is recorded in `deployment.json`.

`evidence/live-run.json` records a synthetic `SEALED → CANCELLED` authorization rehearsal and canonical readback. It contains no physical shipment and no safety disposition. The evidence-dependent inspection path remains technically tested but not field-verified until independently controlled product, custody, sensor, and receiving sources are available.

