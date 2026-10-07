#!/usr/bin/env python3
"""Read the megapool deposit queues (express and standard) in order from LinkedListStorage.scan. Writes data/queue.csv."""
import argparse, csv, sys
from web3 import Web3
ROCKET_STORAGE = "0x1d8f8f00cfa6758d7bE78336684788Fb0ee0Fa46"
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rpc", default="https://eth.drpc.org"); ap.add_argument("--block", type=int); ap.add_argument("--out", default="data/queue.csv"); a = ap.parse_args()
    w3 = Web3(Web3.HTTPProvider(a.rpc, request_kwargs={"timeout": 120})); block = a.block or w3.eth.block_number
    st = w3.eth.contract(address=ROCKET_STORAGE, abi=[{"inputs": [{"name": "k", "type": "bytes32"}], "name": "getAddress", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}])
    lls_addr = st.functions.getAddress(Web3.keccak(text="contract.addresslinkedListStorage")).call(block_identifier=block)
    abi = [{"inputs": [{"name": "ns", "type": "bytes32"}, {"name": "s", "type": "uint256"}, {"name": "c", "type": "uint256"}], "name": "scan",
            "outputs": [{"components": [{"name": "receiver", "type": "address"}, {"name": "validatorId", "type": "uint32"}, {"name": "suppliedValue", "type": "uint32"}, {"name": "requestedValue", "type": "uint32"}], "name": "entries", "type": "tuple[]"}, {"name": "nextIndex", "type": "uint256"}], "stateMutability": "view", "type": "function"},
           {"inputs": [{"name": "ns", "type": "bytes32"}], "name": "getLength", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
           {"inputs": [{"name": "ns", "type": "bytes32"}], "name": "getHeadIndex", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
    lls = w3.eth.contract(address=lls_addr, abi=abi)
    rows = []
    for name in ("express", "standard"):
        ns = Web3.keccak(text=f"deposit.queue.{name}")
        n = lls.functions.getLength(ns).call(block_identifier=block); head = lls.functions.getHeadIndex(ns).call(block_identifier=block)
        print(f"{name}: length {n}, head index {head}", file=sys.stderr)
        idx = head; pos = 0
        while True:
            entries, nxt = lls.functions.scan(ns, idx, 200).call(block_identifier=block)
            for e in entries:
                rows.append({"queue": name, "position": pos, "megapool": e[0], "validator_id": e[1], "supplied_eth": e[2] / 1000, "requested_eth": e[3] / 1000}); pos += 1
            if nxt == 0 or not entries: break
            idx = nxt
    with open(a.out, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); [wr.writerow(r) for r in rows]
    print(f"wrote {len(rows)} queue entries at block {block}", file=sys.stderr)
if __name__ == "__main__": main()
