#!/usr/bin/env python3
"""
Fetch current beacon-chain state (status, balance, activation/exit epoch) for every pubkey in the
snapshot, from a public beacon API. Writes data/beacon_validators.csv. Head state only; no history.
"""
import argparse, csv, json, os, sys, time, urllib.request

def post(url, body, tries=6):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print(f"  error {str(e)[:120]}, retry", file=sys.stderr); time.sleep(min(2 ** t, 20))
    raise RuntimeError("beacon api failed")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beacon", default="https://ethereum-beacon-api.publicnode.com")
    ap.add_argument("--datadir", default="data")
    ap.add_argument("--batch", type=int, default=200)
    a = ap.parse_args()
    pubkeys = []
    for f in ("megapool_validators.csv", "minipools.csv"):
        p = os.path.join(a.datadir, f)
        if os.path.exists(p):
            pubkeys += [r["pubkey"] for r in csv.DictReader(open(p)) if r.get("pubkey") and len(r["pubkey"]) == 98]
    pubkeys = sorted(set(pubkeys))
    print(f"{len(pubkeys)} pubkeys", file=sys.stderr)
    head = json.load(urllib.request.urlopen(f"{a.beacon}/eth/v1/beacon/headers/head", timeout=60))["data"]["header"]["message"]["slot"]
    out = csv.DictWriter(open(os.path.join(a.datadir, "beacon_validators.csv"), "w", newline=""),
                         fieldnames=["pubkey", "index", "status", "balance_gwei", "effective_balance_gwei", "slashed", "activation_eligibility_epoch", "activation_epoch", "exit_epoch", "withdrawable_epoch", "withdrawal_credentials"])
    out.writeheader()
    found = 0
    for i in range(0, len(pubkeys), a.batch):
        chunk = pubkeys[i:i + a.batch]
        res = post(f"{a.beacon}/eth/v1/beacon/states/head/validators", {"ids": chunk})
        for v in res["data"]:
            vv = v["validator"]
            out.writerow({"pubkey": vv["pubkey"], "index": v["index"], "status": v["status"], "balance_gwei": v["balance"], "effective_balance_gwei": vv["effective_balance"],
                          "slashed": vv["slashed"], "activation_eligibility_epoch": vv["activation_eligibility_epoch"], "activation_epoch": vv["activation_epoch"],
                          "exit_epoch": vv["exit_epoch"], "withdrawable_epoch": vv["withdrawable_epoch"], "withdrawal_credentials": vv["withdrawal_credentials"]})
            found += 1
        if (i // a.batch) % 10 == 0: print(f"  {i}/{len(pubkeys)} found {found}", file=sys.stderr)
        time.sleep(0.2)
    json.dump({"head_slot": int(head), "pubkeys_queried": len(pubkeys), "found": found}, open(os.path.join(a.datadir, "beacon_meta.json"), "w"))
    print(f"done: {found} of {len(pubkeys)} found on beacon chain at head slot {head}", file=sys.stderr)

if __name__ == "__main__":
    main()
