#!/usr/bin/env python3
"""
Fast snapshot of the Rocket Pool validator set using Multicall3, pinned to one block.

Outputs (CSV, in --outdir):
  megapool_validators.csv  one row per megapool validator (5k+)
  megapools.csv            one row per megapool contract
  minipools.csv            one row per non-finalised minipool with status Initialised/Prelaunch/Staking
  nodes.csv                one row per node that appears above (RPL stakes, registration time)
  meta.json                block, timestamp, totals

Only eth_call via Multicall3 (0xcA11bde05977b3631167028862bE2a173976CA11). No keys, no transactions.
"""
import argparse, csv, json, os, sys, time
from decimal import Decimal
from web3 import Web3

ROCKET_STORAGE = "0x1d8f8f00cfa6758d7bE78336684788Fb0ee0Fa46"
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"
E = lambda x: str(Decimal(x) / Decimal(10**18))

def fn(name, outs, ins=()):
    return {"inputs": [{"name": f"a{i}", "type": t} for i, t in enumerate(ins)], "name": name,
            "outputs": [{"name": f"o{i}", "type": t} for i, t in enumerate(outs)],
            "stateMutability": "view", "type": "function"}

VI = "(uint32,uint32,uint32,uint32,bool,bool,bool,bool,bool,bool,bool,bool,uint64,uint64)"
MC_ABI = [{"inputs": [{"components": [{"name": "target", "type": "address"}, {"name": "allowFailure", "type": "bool"}, {"name": "callData", "type": "bytes"}], "name": "calls", "type": "tuple[]"}],
           "name": "aggregate3", "outputs": [{"components": [{"name": "success", "type": "bool"}, {"name": "returnData", "type": "bytes"}], "name": "returnData", "type": "tuple[]"}],
           "stateMutability": "payable", "type": "function"}]

class MC:
    """Multicall3 runner that rotates across several public RPCs on errors / rate limits."""
    def __init__(self, w3, block, batch=400, sleep=0.0, rpcs=()):
        self.w3, self.block, self.batch, self.sleep = w3, block, batch, sleep
        self.w3s = [w3] + [Web3(Web3.HTTPProvider(r, request_kwargs={"timeout": 120})) for r in rpcs]
        self.i_rpc = 0
        self.n_calls = 0
    @property
    def mc(self):
        return self.w3s[self.i_rpc].eth.contract(address=MULTICALL3, abi=MC_ABI)
    def run(self, calls, batch=None):
        """calls: list of (target, calldata_hex, out_types). Returns list of decoded tuples or None."""
        out = []
        batch = batch or self.batch
        for i in range(0, len(calls), batch):
            chunk = calls[i:i + batch]
            for attempt in range(6):
                try:
                    res = self.mc.functions.aggregate3([(Web3.to_checksum_address(t), True, bytes.fromhex(d[2:])) for t, d, _ in chunk]).call(block_identifier=self.block)
                    break
                except Exception as e:
                    wait = min(2 ** attempt, 20)
                    print(f"    multicall error on rpc#{self.i_rpc} ({str(e)[:160]}), rotating, retry in {wait}s", file=sys.stderr)
                    self.i_rpc = (self.i_rpc + 1) % len(self.w3s)
                    time.sleep(wait)
            else:
                raise RuntimeError("multicall failed repeatedly")
            self.n_calls += len(chunk)
            for (ok, data), (_, _, types) in zip(res, chunk):
                out.append(self.w3.codec.decode(types, data) if ok and len(data) else None)
            if self.sleep: time.sleep(self.sleep)
        return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default="https://ethereum-rpc.publicnode.com")
    ap.add_argument("--outdir", default="data")
    ap.add_argument("--block", type=int)
    ap.add_argument("--batch", type=int, default=250)
    ap.add_argument("--rpcs", default="https://eth.drpc.org,https://eth-mainnet.public.blastapi.io,https://eth-pokt.nodies.app",
                    help="comma-separated fallback RPCs rotated on errors")
    ap.add_argument("--sleep", type=float, default=0.2)
    ap.add_argument("--limit-minipools", type=int)
    ap.add_argument("--limit-megapool-validators", type=int)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    w3 = Web3(Web3.HTTPProvider(a.rpc, request_kwargs={"timeout": 120}))
    block = a.block or w3.eth.block_number
    ts = w3.eth.get_block(block).timestamp
    mc = MC(w3, block, a.batch, a.sleep, [r for r in a.rpcs.split(',') if r])
    st = w3.eth.contract(address=ROCKET_STORAGE, abi=[fn("getAddress", ["address"], ["bytes32"])])
    A = lambda n: st.functions.getAddress(Web3.keccak(text="contract.address" + n)).call(block_identifier=block)
    addr = {n: A(n) for n in ["rocketMinipoolManager", "rocketMegapoolManager", "rocketNodeStaking", "rocketNodeManager",
                              "rocketDepositPool", "rocketTokenRETH", "rocketNetworkPrices", "rocketDAOProtocolSettingsNode",
                              "rocketDAOProtocolSettingsNetwork", "rocketDAOProtocolSettingsDeposit"]}
    C = lambda n, abi: w3.eth.contract(address=addr[n], abi=abi)
    enc = lambda c, f, *args: c.encode_abi(abi_element_identifier=f, args=list(args)) if hasattr(c, "encode_abi") else c.encodeABI(fn_name=f, args=list(args))

    mpm = C("rocketMinipoolManager", [fn("getMinipoolCount", ["uint256"]), fn("getMinipoolAt", ["address"], ["uint256"]), fn("getMinipoolPubkey", ["bytes"], ["address"])])
    mgm = C("rocketMegapoolManager", [fn("getValidatorCount", ["uint256"]), fn("getValidatorInfo", ["bytes", VI, "address", "uint32"], ["uint256"])])
    ns = C("rocketNodeStaking", [fn("getNodeStakedRPL", ["uint256"], ["address"]), fn("getNodeMegapoolStakedRPL", ["uint256"], ["address"]), fn("getNodeLegacyStakedRPL", ["uint256"], ["address"]),
                                 fn("getNodeETHBonded", ["uint256"], ["address"]), fn("getNodeETHBorrowed", ["uint256"], ["address"]), fn("getNodeMegapoolETHBonded", ["uint256"], ["address"]), fn("getNodeMegapoolETHBorrowed", ["uint256"], ["address"])])
    nm = C("rocketNodeManager", [fn("getNodeRegistrationTime", ["uint256"], ["address"]), fn("getNodeCount", ["uint256"]), fn("getSmoothingPoolRegistrationState", ["bool"], ["address"]), fn("getExpressTicketCount", ["uint256"], ["address"])])
    mega_abi = [fn("getNodeAddress", ["address"]), fn("getNodeBond", ["uint256"]), fn("getUserCapital", ["uint256"]), fn("getValidatorCount", ["uint32"]), fn("getActiveValidatorCount", ["uint32"]),
                fn("getExitingValidatorCount", ["uint32"]), fn("getDebt", ["uint256"]), fn("getAssignedValue", ["uint256"]), fn("getNodeQueuedBond", ["uint256"]), fn("getUserQueuedCapital", ["uint256"]), fn("getNewValidatorBondRequirement", ["uint256"])]
    mega_proto = w3.eth.contract(abi=mega_abi)
    mini_abi = [fn("getStatus", ["uint8"]), fn("getFinalised", ["bool"]), fn("getNodeAddress", ["address"]), fn("getNodeFee", ["uint256"]), fn("getNodeDepositBalance", ["uint256"]), fn("getUserDepositBalance", ["uint256"]), fn("getStatusTime", ["uint256"])]
    mini_proto = w3.eth.contract(abi=mini_abi)

    # ---- protocol-level numbers
    dp = C("rocketDepositPool", [fn("getBalance", ["uint256"]), fn("getExcessBalance", ["uint256"]), fn("getNodeBalance", ["uint256"]), fn("getUserBalance", ["int256"]), fn("getExpressQueueLength", ["uint256"]), fn("getStandardQueueLength", ["uint256"])])
    reth = C("rocketTokenRETH", [fn("totalSupply", ["uint256"]), fn("getExchangeRate", ["uint256"])])
    pr = C("rocketNetworkPrices", [fn("getRPLPrice", ["uint256"])])
    meta = {"block": block, "timestamp": ts, "rpc": a.rpc,
            "deposit_pool_balance_eth": E(dp.functions.getBalance().call(block_identifier=block)),
            "deposit_pool_excess_eth": E(dp.functions.getExcessBalance().call(block_identifier=block)),
            "deposit_pool_node_balance_eth": E(dp.functions.getNodeBalance().call(block_identifier=block)),
            "deposit_pool_user_balance_eth": E(dp.functions.getUserBalance().call(block_identifier=block)),
            "express_queue_length": dp.functions.getExpressQueueLength().call(block_identifier=block),
            "standard_queue_length": dp.functions.getStandardQueueLength().call(block_identifier=block),
            "reth_supply": E(reth.functions.totalSupply().call(block_identifier=block)),
            "reth_exchange_rate": E(reth.functions.getExchangeRate().call(block_identifier=block)),
            "rpl_price_eth": E(pr.functions.getRPLPrice().call(block_identifier=block)),
            "node_count": nm.functions.getNodeCount().call(block_identifier=block)}
    print(json.dumps(meta, indent=1), file=sys.stderr)

    # ---- megapool validators
    n_mv = mgm.functions.getValidatorCount().call(block_identifier=block)
    lim = min(n_mv, a.limit_megapool_validators or n_mv)
    print(f"megapool validators: {n_mv}, reading {lim}", file=sys.stderr)
    res = mc.run([(addr["rocketMegapoolManager"], enc(mgm, "getValidatorInfo", i), ["bytes", VI, "address", "uint32"]) for i in range(lim)])
    mvs = []
    for i, r in enumerate(res):
        if r is None: continue
        pubkey, info, megapool, vid = r
        megapool = Web3.to_checksum_address(megapool)
        (lastAssign, lastReqVal, lastReqBond, depositValue, staked, exited, inQueue, inPrestake, expressUsed, dissolved, exiting, locked, exitBalance, lockedTime) = info
        mvs.append({"global_index": i, "pubkey": "0x" + pubkey.hex(), "megapool": megapool, "validator_id": vid,
                    "last_assignment_time": lastAssign, "last_requested_value_eth": str(Decimal(lastReqVal) / 1000), "last_requested_bond_eth": str(Decimal(lastReqBond) / 1000),
                    "deposit_value_eth": str(Decimal(depositValue) / 10**9), "staked": staked, "exited": exited, "in_queue": inQueue, "in_prestake": inPrestake,
                    "express_used": expressUsed, "dissolved": dissolved, "exiting": exiting, "locked": locked, "exit_balance_eth": str(Decimal(exitBalance) / 10**9)})
    megapools = sorted({m["megapool"] for m in mvs})
    print(f"  {len(mvs)} validators in {len(megapools)} megapools", file=sys.stderr)
    fields = [f["name"] for f in mega_abi]
    calls = [(mp, enc(mega_proto, f), [o["type"] for o in fx["outputs"]]) for mp in megapools for f, fx in zip(fields, mega_abi)]
    res = mc.run(calls, batch=80)
    mp_rows = {}
    for k, mp in enumerate(megapools):
        vals = res[k * len(fields):(k + 1) * len(fields)]
        row = {"megapool": mp}
        for f, v in zip(fields, vals):
            v = None if v is None else v[0]
            if f == "getNodeAddress" and v is not None: v = Web3.to_checksum_address(v)
            if f in ("getNodeBond", "getUserCapital", "getDebt", "getAssignedValue", "getNodeQueuedBond", "getUserQueuedCapital", "getNewValidatorBondRequirement") and v is not None: v = E(v)
            row[f[3].lower() + f[4:]] = v
        mp_rows[mp] = row
    for m in mvs:
        m["node"] = mp_rows[m["megapool"]]["nodeAddress"]
    with open(os.path.join(a.outdir, "megapools.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(next(iter(mp_rows.values())).keys()) if mp_rows else ["megapool"]); wr.writeheader(); [wr.writerow(r) for r in mp_rows.values()]
    with open(os.path.join(a.outdir, "megapool_validators.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(mvs[0].keys())); wr.writeheader(); [wr.writerow(r) for r in mvs]

    # ---- minipools
    n_mp = mpm.functions.getMinipoolCount().call(block_identifier=block)
    lim = min(n_mp, a.limit_minipools or n_mp)
    print(f"minipools: {n_mp}, reading {lim}", file=sys.stderr)
    addrs = [Web3.to_checksum_address(r[0]) for r in mc.run([(addr["rocketMinipoolManager"], enc(mpm, "getMinipoolAt", i), ["address"]) for i in range(lim)])]
    st_fin = mc.run([(ad, enc(mini_proto, f), [t]) for ad in addrs for f, t in (("getStatus", "uint8"), ("getFinalised", "bool"))])
    live = []
    for k, ad in enumerate(addrs):
        s, f = st_fin[2 * k], st_fin[2 * k + 1]
        s = None if s is None else s[0]; f = None if f is None else f[0]
        if s in (0, 1, 2) and not f: live.append((ad, s))
    print(f"  {len(live)} live (initialised/prelaunch/staking, not finalised)", file=sys.stderr)
    per = [("getNodeAddress", "address"), ("getNodeFee", "uint256"), ("getNodeDepositBalance", "uint256"), ("getUserDepositBalance", "uint256"), ("getStatusTime", "uint256")]
    res = mc.run([(ad, enc(mini_proto, f), [t]) for ad, _ in live for f, t in per])
    pk = mc.run([(addr["rocketMinipoolManager"], enc(mpm, "getMinipoolPubkey", ad), ["bytes"]) for ad, _ in live])
    mps = []
    for k, (ad, s) in enumerate(live):
        v = res[k * len(per):(k + 1) * len(per)]
        g = lambda j: None if v[j] is None else v[j][0]
        mps.append({"minipool": ad, "status": {0: "Initialised", 1: "Prelaunch", 2: "Staking"}[s], "pubkey": ("0x" + pk[k][0].hex()) if pk[k] else "",
                    "node": Web3.to_checksum_address(g(0)) if g(0) else None, "commission": E(g(1)) if g(1) is not None else "", "node_deposit_eth": E(g(2)) if g(2) is not None else "",
                    "user_deposit_eth": E(g(3)) if g(3) is not None else "", "status_time": g(4)})
    with open(os.path.join(a.outdir, "minipools.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(mps[0].keys())); wr.writeheader(); [wr.writerow(r) for r in mps]

    # ---- nodes
    nodes = sorted({m["node"] for m in mvs} | {m["node"] for m in mps if m["node"]})
    print(f"nodes: {len(nodes)}", file=sys.stderr)
    nf = [(ns, "getNodeStakedRPL"), (ns, "getNodeMegapoolStakedRPL"), (ns, "getNodeLegacyStakedRPL"), (ns, "getNodeETHBonded"), (ns, "getNodeETHBorrowed"),
          (ns, "getNodeMegapoolETHBonded"), (ns, "getNodeMegapoolETHBorrowed"), (nm, "getNodeRegistrationTime"), (nm, "getExpressTicketCount"), (nm, "getSmoothingPoolRegistrationState")]
    res = mc.run([(c.address, enc(c, f, n), ["bool" if f == "getSmoothingPoolRegistrationState" else "uint256"]) for n in nodes for c, f in nf])
    nrows = []
    for k, n in enumerate(nodes):
        v = res[k * len(nf):(k + 1) * len(nf)]
        g = lambda j: None if v[j] is None else v[j][0]
        nrows.append({"node": n, "rpl_staked_total": E(g(0)) if g(0) is not None else "", "rpl_staked_megapool": E(g(1)) if g(1) is not None else "", "rpl_staked_legacy": E(g(2)) if g(2) is not None else "",
                      "eth_bonded": E(g(3)) if g(3) is not None else "", "eth_borrowed": E(g(4)) if g(4) is not None else "", "megapool_eth_bonded": E(g(5)) if g(5) is not None else "",
                      "megapool_eth_borrowed": E(g(6)) if g(6) is not None else "", "registration_time": g(7), "express_tickets": g(8), "smoothing_pool": g(9)})
    with open(os.path.join(a.outdir, "nodes.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(nrows[0].keys())); wr.writeheader(); [wr.writerow(r) for r in nrows]
    meta.update({"megapool_validators_registered": n_mv, "megapools": len(megapools), "minipools_total": n_mp, "minipools_live": len(mps), "nodes_in_dataset": len(nodes), "eth_calls_via_multicall": mc.n_calls})
    json.dump(meta, open(os.path.join(a.outdir, "meta.json"), "w"), indent=1)
    print("done", json.dumps(meta), file=sys.stderr)

if __name__ == "__main__":
    main()
