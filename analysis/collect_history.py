#!/usr/bin/env python3
"""
Weekly history of Rocket Pool supply/demand variables, read from an archive RPC.

Columns: date, block, reth_supply, exchange_rate, eth_staked (= supply*rate), deposit_pool_eth,
deposit_pool_excess_eth, express_queue, standard_queue, megapool_validators, node_count,
minipools_staking. Queue/megapool columns are blank before the Saturn 1 contracts existed.

Usage: python3 collect_history.py --archive https://eth.drpc.org --start 2025-10-01 --out data/history.csv
"""
import argparse, csv, datetime as dt, sys, time
from decimal import Decimal
from web3 import Web3

ROCKET_STORAGE = "0x1d8f8f00cfa6758d7bE78336684788Fb0ee0Fa46"
E = lambda x: Decimal(x) / Decimal(10**18)

def fn(name, outs, ins=()):
    return {"inputs": [{"name": f"a{i}", "type": t} for i, t in enumerate(ins)], "name": name,
            "outputs": [{"name": f"o{i}", "type": t} for i, t in enumerate(outs)], "stateMutability": "view", "type": "function"}

def block_at(w3, ts, lo, hi):
    """largest block with timestamp <= ts (binary search)."""
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if w3.eth.get_block(mid).timestamp <= ts: lo = mid
        else: hi = mid - 1
    return lo

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="https://eth.drpc.org")
    ap.add_argument("--fallbacks", default="https://eth-mainnet.public.blastapi.io,https://eth-pokt.nodies.app")
    ap.add_argument("--head-rpc", default="https://ethereum-rpc.publicnode.com")
    ap.add_argument("--start", default="2025-10-01")
    ap.add_argument("--step-days", type=int, default=7)
    ap.add_argument("--out", default="data/history.csv")
    a = ap.parse_args()
    head = Web3(Web3.HTTPProvider(a.head_rpc, request_kwargs={"timeout": 60}))
    rpcs = [a.archive] + [x for x in a.fallbacks.split(",") if x]
    arch = [Web3(Web3.HTTPProvider(r, request_kwargs={"timeout": 60})) for r in rpcs]
    latest = head.eth.block_number
    latest_ts = head.eth.get_block(latest).timestamp
    start_ts = int(dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc).timestamp())
    # RocketStorage address lookups are time-dependent (upgrades), so resolve per block.
    def call(name, f, outs, block, ins=(), args=()):
        for w3 in arch:
            try:
                st = w3.eth.contract(address=ROCKET_STORAGE, abi=[fn("getAddress", ["address"], ["bytes32"])])
                ad = st.functions.getAddress(Web3.keccak(text="contract.address" + name)).call(block_identifier=block)
                if int(ad, 16) == 0: return None
                c = w3.eth.contract(address=ad, abi=[fn(f, outs, ins)])
                return getattr(c.functions, f)(*args).call(block_identifier=block)
            except Exception as e:
                msg = str(e)
                if "revert" in msg.lower() or "no data" in msg.lower(): return None
                time.sleep(1)
        return None
    rows = []
    ts = start_ts
    lo = 15_500_000  # public RPCs prune older headers; fine for 2025+
    while ts <= latest_ts:
        blk = block_at(head, ts, lo, latest); lo = blk
        d = dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()
        sup = call("rocketTokenRETH", "totalSupply", ["uint256"], blk)
        rate = call("rocketTokenRETH", "getExchangeRate", ["uint256"], blk)
        dpb = call("rocketDepositPool", "getBalance", ["uint256"], blk)
        dpx = call("rocketDepositPool", "getExcessBalance", ["uint256"], blk)
        eq = call("rocketDepositPool", "getExpressQueueLength", ["uint256"], blk)
        sq = call("rocketDepositPool", "getStandardQueueLength", ["uint256"], blk)
        mv = call("rocketMegapoolManager", "getValidatorCount", ["uint256"], blk)
        nc = call("rocketNodeManager", "getNodeCount", ["uint256"], blk)
        ms = call("rocketMinipoolManager", "getStakingMinipoolCount", ["uint256"], blk)
        row = {"date": d, "block": blk, "reth_supply": E(sup) if sup is not None else "", "exchange_rate": E(rate) if rate is not None else "",
               "eth_staked": (E(sup) * E(rate)) if sup is not None and rate is not None else "",
               "deposit_pool_eth": E(dpb) if dpb is not None else "", "deposit_pool_excess_eth": E(dpx) if dpx is not None else "",
               "express_queue": eq if eq is not None else "", "standard_queue": sq if sq is not None else "",
               "megapool_validators": mv if mv is not None else "", "node_count": nc if nc is not None else "", "minipools_staking": ms if ms is not None else ""}
        rows.append(row); print(row, file=sys.stderr)
        ts += a.step_days * 86400
    # add the latest block as the final row
    with open(a.out, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader(); [wr.writerow(r) for r in rows]
    print(f"wrote {len(rows)} rows to {a.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
