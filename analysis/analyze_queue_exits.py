#!/usr/bin/env python3
"""
Part 2: timing of the exits in progress, who the returning ETH funds (on-chain queue order),
and how long a 6 ETH megapool bond takes to reach from rewards.

Inputs: data/minipools.csv, data/beacon_validators.csv, data/queue.csv, data/megapools.csv,
        data/nodes.csv, data/meta.json. Output: report/numbers_part2.md, report/figures/07_*, 08_*.
"""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GENESIS = 1606824023
EPOCH_S = 384
ep2date = lambda e: pd.to_datetime(GENESIS + int(e) * EPOCH_S, unit="s", utc=True)

def md(df, f="{:,.2f}"):
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]): d[c] = d[c].map(lambda v: "" if pd.isna(v) else f.format(v))
        elif pd.api.types.is_integer_dtype(d[c]): d[c] = d[c].map(lambda v: f"{v:,}")
    cols = list(d.columns)
    return "\n".join(["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for _, r in d.iterrows()])

os.makedirs("report/figures", exist_ok=True)
meta = json.load(open("data/meta.json"))
mp = pd.read_csv("data/minipools.csv"); bc = pd.read_csv("data/beacon_validators.csv").drop_duplicates("pubkey").set_index("pubkey")
q = pd.read_csv("data/queue.csv"); mg = pd.read_csv("data/megapools.csv"); nd = pd.read_csv("data/nodes.csv").set_index("node")
bmeta = json.load(open("data/beacon_meta.json")); head_epoch = bmeta["head_slot"] // 32
out = []; P = out.append
P(f"# Part 2: exit timing, queue funding, bond top-up (block {meta['block']:,}, beacon head epoch {head_epoch:,})\n")

# ---------------------------------------------------------------- 7. when the exiting ETH lands
mp["status_b"] = mp.pubkey.map(bc.status)
ex = mp[mp.status_b == "active_exiting"].copy()
ex["exit_epoch"] = pd.to_numeric(ex.pubkey.map(bc.exit_epoch)); ex["wd_epoch"] = pd.to_numeric(ex.pubkey.map(bc.withdrawable_epoch))
ex["exit_date"] = ex.exit_epoch.map(ep2date).dt.date; ex["wd_date"] = ex.wd_epoch.map(ep2date).dt.date
P("## 7. When the exiting minipools' ETH comes back\n")
P(f"{len(ex):,} minipools are `active_exiting`. Exit epochs run {int(ex.exit_epoch.min()):,} to {int(ex.exit_epoch.max()):,} "
  f"({ex.exit_date.min()} to {ex.exit_date.max()}), withdrawable epochs {int(ex.wd_epoch.min()):,} to {int(ex.wd_epoch.max()):,} "
  f"({ex.wd_date.min()} to {ex.wd_date.max()}). The beacon head at the snapshot was epoch {head_epoch:,} ({ep2date(head_epoch).date()}), so the whole batch exits within about "
  f"{(ex.exit_epoch.max() - head_epoch) * EPOCH_S / 86400:.1f} days of the snapshot. Balances are then paid out by the beacon withdrawal sweep (a few days more), after which the minipool's user share returns to the deposit pool on `distributeBalance`.\n")
byday = ex.groupby("wd_date").agg(minipools=("minipool", "count"), user_eth=("user_deposit_eth", "sum"), node_eth=("node_deposit_eth", "sum")).reset_index()
byday["cum_user_eth"] = byday.user_eth.cumsum()
P("Withdrawable date of the exiting minipools (user ETH is what the deposit pool receives):\n")
P(md(byday, "{:,.0f}") + "\n")
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.bar(byday.wd_date.astype(str), byday.user_eth); ax.set_ylabel("user ETH becoming withdrawable"); ax.set_title("Exiting minipools: user ETH by withdrawable date"); ax.tick_params(axis="x", rotation=45)
fig.tight_layout(); fig.savefig("report/figures/07_exit_timeline.png", dpi=130); plt.close(fig)

# ---------------------------------------------------------------- 8. who the returning ETH funds
P("## 8. Who the returning ETH funds: the queue in on-chain order\n")
mgi = mg.set_index("megapool")
q["node"] = q.megapool.map(mgi.nodeAddress)
q["user_eth_needed"] = q.requested_eth - q.supplied_eth
P(f"The express queue holds {int((q.queue == 'express').sum()):,} entries and the standard queue {int((q.queue == 'standard').sum()):,}, from {q.megapool.nunique():,} megapools. "
  f"Every entry needs {q.user_eth_needed.iloc[0]:.0f} ETH of user capital. `express_queue_rate` is 4, so assignments go 4 express then 1 standard. Express tickets outstanding across all nodes: **{int(nd.express_tickets.sum()):,}** on {int((nd.express_tickets > 0).sum()):,} nodes, enough to keep the express queue fed for a long time.\n")
qn = q.groupby("node").agg(queued=("validator_id", "count"), express=("queue", lambda s: int((s == "express").sum()))).sort_values("queued", ascending=False)
qn["share_of_queue_pct"] = qn.queued / len(q) * 100; qn["cum_share_pct"] = qn.share_of_queue_pct.cumsum()
P("Queue concentration by node (top 15):\n"); P(md(qn.head(15).reset_index(), "{:,.1f}") + "\n")
P(f"The 6 largest queued nodes hold **{qn.queued.head(6).sum():,}** of {len(q):,} queued validators ({qn.queued.head(6).sum() / len(q) * 100:.0f}%). {int((qn.queued == 1).sum()):,} nodes have a single validator queued.\n")

def fund(eth):
    """simulate assignment: 4 express, 1 standard, 28 ETH each, in on-chain order"""
    e = q[q.queue == "express"].sort_values("position").to_dict("records"); s = q[q.queue == "standard"].sort_values("position").to_dict("records")
    funded = []; i = j = 0; cycle = 0
    while eth >= 28 and (i < len(e) or j < len(s)):
        take_express = (cycle % 5 != 4 and i < len(e)) or j >= len(s)
        r = e[i] if take_express else s[j]
        if take_express: i += 1
        else: j += 1
        funded.append(r); eth -= 28; cycle += 1
    return pd.DataFrame(funded)
ret_user = ex.user_deposit_eth.sum()
rows = []
for label, frac in [("all returning user ETH goes to the queue", 1.0), ("two thirds (rest burned by rETH redemptions)", 2 / 3), ("one third", 1 / 3)]:
    f = fund(ret_user * frac)
    rows.append([label, ret_user * frac, len(f), int((f.queue == "express").sum()), int((f.queue == "standard").sum()), f.node.nunique(), f.groupby("node").size().max(), f.groupby("node").size().sort_values(ascending=False).head(6).sum() / max(1, len(f)) * 100])
t = pd.DataFrame(rows, columns=["scenario", "ETH to queue", "validators funded", "express", "standard", "nodes funded", "most to one node", "share to top 6 nodes %"])
P(f"Scenarios for the **{ret_user:,.0f} ETH** of user capital in the exiting minipools:\n"); P(md(t, "{:,.0f}") + "\n")
f_all = fund(ret_user)
P(f"Under the first scenario the queue is left with {len(q) - len(f_all):,} entries, all standard-queue ({int(((q.queue == 'standard').sum()) - (f_all.queue == 'standard').sum()):,} standard entries unfunded) because the 4:1 rate drains the express queue first.\n")
fn = f_all.groupby("node").size().sort_values(ascending=False).head(10).rename("validators funded").reset_index()
fn["queued now"] = fn.node.map(qn.queued); fn["megapool RPL staked"] = fn.node.map(nd.rpl_staked_megapool).round(0); fn["still runs minipools"] = fn.node.isin(mp.node.unique())
P("Top 10 beneficiaries if all returning ETH funds the queue:\n"); P(md(fn, "{:,.0f}") + "\n")
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.plot(np.arange(1, len(qn) + 1), qn.cum_share_pct.values); ax.set_xscale("log"); ax.set_xlabel("nodes, largest queued first (log)"); ax.set_ylabel("cumulative % of queue"); ax.set_title("Megapool queue concentration"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig("report/figures/08_queue_concentration.png", dpi=130); plt.close(fig)

# ---------------------------------------------------------------- 9. years to a 6 ETH bond from rewards
P("## 9. RPIP-83: years to top up to 6 ETH from rewards alone\n")
for c in ["nodeBond", "activeValidatorCount"]: mg[c] = pd.to_numeric(mg[c], errors="coerce")
mv = pd.read_csv("data/megapool_validators.csv")
staked = mv[(mv.staked == True) & (mv.exiting == False)].groupby("megapool").size().rename("staked_validators")
act = mg.join(staked, on="megapool"); act = act[act.staked_validators > 0].copy()
act["activeValidatorCount"] = act.staked_validators  # nodeBond covers staked validators; queued bonds sit in nodeQueuedBond
act["bond_pv"] = act.nodeBond / act.staked_validators
act["shortfall_pv"] = (6 - act.bond_pv).clip(lower=0)
rows = []
for apr in [0.025, 0.03, 0.035]:
    for label, voter in [("no RPL (node share 5% only)", 0.0), ("RPL staked (node 5% + voter 9%)", 0.09)]:
        per_val = act.bond_pv * apr + (0.05 + voter) * (32 - act.bond_pv) * apr  # ETH per validator per year retained
        yrs = act.shortfall_pv / per_val
        w = act.activeValidatorCount
        rows.append([f"{apr*100:.1f}%", label, float((per_val * w).sum() / w.sum()), float(np.average(yrs, weights=w)), float((yrs[act.shortfall_pv > 0]).median())])
t9 = pd.DataFrame(rows, columns=["gross staking APR", "operator rewards", "retained ETH per validator per year", "validator-weighted years to 6 ETH", "median years (nodes below 6)"])
P("Megapool operator rewards per validator under UARS: own bond at the APR, plus node share (5%) and, if RPL is staked, voter share (9%) of the rewards on the borrowed ETH. Rewards retained to raise the bond from today's level to 6 ETH:\n")
P(md(t9, "{:,.2f}") + "\n")
P(f"{int((act.shortfall_pv > 0).sum()):,} of {len(act):,} active megapools are below 6 ETH per validator; total shortfall {float((act.shortfall_pv * act.activeValidatorCount).sum()):,.0f} ETH. At 3% gross and no RPL, a 4 ETH validator retains about {4*0.03 + 0.05*28*0.03:.3f} ETH a year, so the 2 ETH gap takes about {2/(4*0.03 + 0.05*28*0.03):.0f} years; with RPL staked about {2/(4*0.03 + 0.14*28*0.03):.0f} years. The RPIP's own 11 to 13 year figure is the no-RPL case.\n")

open("report/numbers_part2.md", "w").write("\n".join(out)); print("\n".join(out))
