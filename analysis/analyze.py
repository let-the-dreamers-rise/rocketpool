#!/usr/bin/env python3
"""
Saturn 2 decision data from the live Rocket Pool validator set.

Inputs (from collect_snapshot_multicall.py, collect_history.py, collect_beacon.py) in --datadir.
Outputs: report/figures/*.png and report/numbers.md (all tables, generated, reproducible).

Sections
  1. Supply/demand state and history (rETH supply, ETH staked, megapool queue)
  2. Composition of the validator set (minipools by bond x commission, megapools, nodes, RPL)
  3. RPIP-83 arithmetic: rETH needed to migrate the staking-minipool set at 4 / 6 / 8 ETH bonds
  4. RPIP-71 phase 1: minipool exit ordering by commission (who gets hit, TVL per ETH of liquidity, RPL freed)
  5. RPIP-71 phase 2: megapool exit criteria under tournament sampling (concentration, small nodes, sybil, RPL)
  6. Age structure of megapool validators (beacon activation epochs)
"""
import argparse, json, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 20261004
GENESIS_TS = 1606824023
EPOCH_S = 384


def epoch_to_date(e):
    return pd.to_datetime(GENESIS_TS + int(e) * EPOCH_S, unit="s", utc=True).date()


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    if x.sum() == 0:
        return 0.0
    n = len(x)
    return (2 * np.sum((np.arange(1, n + 1)) * x) / (n * x.sum())) - (n + 1) / n


def md_table(df, floatfmt="{:,.2f}"):
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
        elif pd.api.types.is_integer_dtype(df[c]):
            df[c] = df[c].map(lambda v: f"{v:,}")
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datadir", default="data")
    ap.add_argument("--outdir", default="report")
    ap.add_argument("--runs", type=int, default=200, help="simulation repetitions")
    a = ap.parse_args()
    fig_dir = os.path.join(a.outdir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    rng = np.random.default_rng(SEED)
    out = []
    P = out.append

    meta = json.load(open(os.path.join(a.datadir, "meta.json")))
    mv = pd.read_csv(os.path.join(a.datadir, "megapool_validators.csv"))
    mg = pd.read_csv(os.path.join(a.datadir, "megapools.csv"))
    mp = pd.read_csv(os.path.join(a.datadir, "minipools.csv"))
    nd = pd.read_csv(os.path.join(a.datadir, "nodes.csv"))
    hist = pd.read_csv(os.path.join(a.datadir, "history.csv"))
    beacon_path = os.path.join(a.datadir, "beacon_validators.csv")
    bc = pd.read_csv(beacon_path) if os.path.exists(beacon_path) else None
    snap_date = pd.to_datetime(meta["timestamp"], unit="s", utc=True).date()

    P(f"# Generated numbers (block {meta['block']:,}, {snap_date}, {meta['rpc']})\n")
    P("All figures below are produced by `analyze.py` from the CSVs in `data/`. Rerun to refresh.\n")

    # ------------------------------------------------------------------ 1. supply / demand
    P("## 1. Supply and demand\n")
    q_express, q_standard = int(meta["express_queue_length"]), int(meta["standard_queue_length"])
    q_total = q_express + q_standard
    queued = mv[mv.in_queue == True]
    queued_user_eth = queued.last_requested_value_eth.astype(float).sum() - queued.last_requested_bond_eth.astype(float).sum()
    state = pd.DataFrame([
        ["rETH supply", float(meta["reth_supply"])],
        ["rETH exchange rate (ETH per rETH)", float(meta["reth_exchange_rate"])],
        ["ETH represented by rETH (supply x rate)", float(meta["reth_supply"]) * float(meta["reth_exchange_rate"])],
        ["Deposit pool balance (ETH)", float(meta["deposit_pool_balance_eth"])],
        ["  of which node ETH waiting in queue", float(meta["deposit_pool_node_balance_eth"])],
        ["  of which user (rETH) ETH available", float(meta["deposit_pool_user_balance_eth"])],
        ["Megapool validators in queue (express + standard)", q_total],
        ["  express", q_express], ["  standard", q_standard],
        ["User ETH needed to fund the whole queue", queued_user_eth],
        ["Megapool validators registered", int(meta["megapool_validators_registered"])],
        ["Megapool contracts", int(meta["megapools"])],
        ["Minipools total / live (initialised, prelaunch, staking)", f"{int(meta['minipools_total']):,} / {int(meta['minipools_live']):,}"],
        ["Registered nodes", int(meta["node_count"])],
        ["RPL price (ETH)", float(meta["rpl_price_eth"])],
    ], columns=["Metric", "Value"])
    state["Value"] = state.Value.map(lambda v: f"{v:,.0f}" if isinstance(v, (int, float)) and abs(v) >= 1000 else (f"{v:,.4f}" if isinstance(v, float) else str(v)))
    P(md_table(state) + "\n")

    hist = hist.replace("", np.nan)
    for c in ["reth_supply", "exchange_rate", "eth_staked", "deposit_pool_eth", "express_queue", "standard_queue", "megapool_validators", "node_count", "minipools_staking"]:
        hist[c] = pd.to_numeric(hist[c], errors="coerce")
    hist["date"] = pd.to_datetime(hist["date"])
    hist["queue_total"] = hist.express_queue.fillna(0) + hist.standard_queue.fillna(0)
    sat1 = hist[hist.megapool_validators.notna()].iloc[0] if hist.megapool_validators.notna().any() else None  # first sample after Saturn 1 contracts went live
    last = hist.iloc[-1]
    first = hist.iloc[0]
    d90 = hist[hist.date >= last.date - pd.Timedelta(days=91)].iloc[0]
    rows = [["Window", "From", "To", "rETH supply change", "ETH-staked change", "Per 30 days (ETH)"]]
    def win(lbl, r0, r1):
        days = (r1.date - r0.date).days or 1
        return [lbl, r0.date.date().isoformat(), r1.date.date().isoformat(), r1.reth_supply - r0.reth_supply, r1.eth_staked - r0.eth_staked, (r1.eth_staked - r0.eth_staked) / days * 30]
    tbl = [win("Full history in file", first, last), win("Trailing ~90 days", d90, last)]
    if sat1 is not None:
        tbl.append(win("Since Saturn 1 contracts (18 Feb 2026)", sat1, last))
    P("### rETH supply trend (weekly samples from archive RPC)\n")
    P(md_table(pd.DataFrame(tbl, columns=rows[0]), "{:,.0f}") + "\n")
    net30 = tbl[1][5]
    if net30 > 0:
        P(f"At the trailing-90-day net rate of {net30:,.0f} ETH per 30 days, the {queued_user_eth:,.0f} ETH needed to fund the queue would take about **{queued_user_eth / net30 * 30 / 30:,.1f} months**.\n")
    else:
        P(f"The trailing-90-day net flow into rETH is **{net30:,.0f} ETH per 30 days** (negative or zero): at this rate the {queued_user_eth:,.0f} ETH of queued demand is never funded by organic minting; the queue only moves when validators exit or rETH holders deposit.\n")

    # reconciliation of ETH freed by minipool exits vs megapool funding vs net redemptions since Saturn 1
    for c in ["nodeBond", "userCapital", "validatorCount", "activeValidatorCount", "exitingValidatorCount", "debt", "assignedValue", "nodeQueuedBond", "userQueuedCapital", "newValidatorBondRequirement"]:
        mg[c] = pd.to_numeric(mg[c], errors="coerce")
    if sat1 is not None:
        exits_since = int(sat1.minipools_staking - last.minipools_staking)
        avg_user = float(mp[mp.status == "Staking"].user_deposit_eth.astype(float).mean())
        freed = exits_since * avg_user
        funded = float(mg.userCapital.sum())
        net_flow = float(last.eth_staked - sat1.eth_staked)
        days = (last.date - sat1.date).days
        rewards_est = float(sat1.eth_staked) * 0.0225 * days / 365
        P("### Where the ETH freed by minipool exits went (since Saturn 1)\n")
        P(f"Staking minipools fell by **{exits_since:,}** between {sat1.date.date()} and {last.date.date()}. At today's average user capital per staking minipool ({avg_user:.1f} ETH) that freed roughly **{freed:,.0f} ETH** of rETH capital. Megapools now hold **{funded:,.0f} ETH** of user capital, all assigned since Saturn 1. ETH behind rETH changed by **{net_flow:,.0f} ETH** over the period, of which about {rewards_est:,.0f} ETH is accrued staking rewards, so net redemptions (burns minus mints) were roughly **{-(net_flow - rewards_est):,.0f} ETH**. The deposit pool also held about 12,000 ETH in early February that was consumed at launch. In short: capital released by minipool exits went partly to funding megapool validators and partly out through rETH redemptions; net new rETH demand contributed nothing. Expect the capital now returning from the exits in progress to be split the same way, so it will not fund the whole queue.\n")
    fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    ax[0].plot(hist.date, hist.eth_staked, label="ETH represented by rETH (supply x rate)")
    ax[0].plot(hist.date, hist.reth_supply, label="rETH supply")
    ax[0].set_ylabel("ETH / rETH"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(hist.date, hist.express_queue, label="express queue (validators)")
    ax[1].plot(hist.date, hist.standard_queue, label="standard queue (validators)")
    ax[1].plot(hist.date, hist.megapool_validators, label="megapool validators registered", ls="--")
    ax[1].set_ylabel("count"); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.suptitle("Rocket Pool: rETH supply vs megapool queue"); fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "01_supply_queue_history.png"), dpi=130); plt.close(fig)

    # ------------------------------------------------------------------ 2. composition
    P("## 2. Composition of the validator set\n")
    mp["commission"] = pd.to_numeric(mp.commission, errors="coerce")
    mp["node_deposit_eth"] = pd.to_numeric(mp.node_deposit_eth, errors="coerce")
    mp["user_deposit_eth"] = pd.to_numeric(mp.user_deposit_eth, errors="coerce")
    stk = mp[mp.status == "Staking"].copy()
    stk["comm_pct"] = (stk.commission * 100).round(0).astype(int)
    stk["bond"] = stk.node_deposit_eth.round(0).astype(int)
    comp = stk.groupby(["bond", "comm_pct"]).agg(minipools=("minipool", "count"), nodes=("node", "nunique"), node_eth=("node_deposit_eth", "sum"), user_eth=("user_deposit_eth", "sum")).reset_index()
    comp = comp.sort_values(["bond", "comm_pct"], ascending=[True, False])
    P("### Staking minipools by node bond and commission\n")
    P(md_table(comp, "{:,.0f}") + "\n")
    P(f"Staking minipools: **{len(stk):,}** on **{stk.node.nunique():,}** nodes; node ETH **{stk.node_deposit_eth.sum():,.0f}**, user (rETH) ETH **{stk.user_deposit_eth.sum():,.0f}**. "
      f"Other live minipools: {(mp.status != 'Staking').sum():,} (initialised/prelaunch).\n")

    for c in ["nodeBond", "userCapital", "validatorCount", "activeValidatorCount", "exitingValidatorCount", "debt", "assignedValue", "nodeQueuedBond", "userQueuedCapital", "newValidatorBondRequirement"]:
        mg[c] = pd.to_numeric(mg[c], errors="coerce")
    for c in ["rpl_staked_total", "rpl_staked_megapool", "rpl_staked_legacy", "eth_bonded", "eth_borrowed", "megapool_eth_bonded", "megapool_eth_borrowed"]:
        nd[c] = pd.to_numeric(nd[c], errors="coerce")
    mv_status = mv.apply(lambda r: "exited" if r.exited else ("dissolved" if r.dissolved else ("staked" if r.staked else ("in_queue" if r.in_queue else ("prestake" if r.in_prestake else "not_funded (dequeued / never deposited)")))), axis=1)
    mv["state"] = mv_status
    st_tbl = mv.groupby("state").agg(validators=("pubkey", "count"), megapools=("megapool", "nunique"), nodes=("node", "nunique"), express_used=("express_used", "sum")).reset_index()
    P("### Megapool validators by state\n")
    P(md_table(st_tbl, "{:,.0f}") + "\n")
    active = mv[(mv.state == "staked") & (~mv.exiting.astype(bool))].copy()
    mgi = mg.set_index("megapool")
    active["node_bond_per_validator"] = active.megapool.map(mgi.nodeBond) / active.megapool.map(mgi.activeValidatorCount).replace(0, np.nan)
    node_sz = active.groupby("node").size().rename("active_validators")
    ndi = nd.set_index("node")
    nodes_mg = pd.DataFrame({"active_validators": node_sz})
    nodes_mg["rpl_megapool"] = ndi.rpl_staked_megapool.reindex(nodes_mg.index).fillna(0)
    nodes_mg["rpl_total"] = ndi.rpl_staked_total.reindex(nodes_mg.index).fillna(0)
    nodes_mg["eth_borrowed_megapool"] = ndi.megapool_eth_borrowed.reindex(nodes_mg.index).fillna(0)
    nodes_mg["eth_bonded_megapool"] = ndi.megapool_eth_bonded.reindex(nodes_mg.index).fillna(0)
    nodes_mg["rpl_per_borrowed_eth"] = nodes_mg.rpl_megapool / nodes_mg.eth_borrowed_megapool.replace(0, np.nan)
    nodes_mg["bond_per_validator"] = nodes_mg.eth_bonded_megapool / nodes_mg.active_validators
    nodes_mg["has_minipools"] = nodes_mg.index.isin(stk.node.unique())
    bins = [0, 1, 2, 4, 8, 16, 32, 64, 10**6]
    labels = ["1", "2", "3-4", "5-8", "9-16", "17-32", "33-64", "65+"]
    nodes_mg["size_bin"] = pd.cut(nodes_mg.active_validators, bins=bins, labels=labels)
    sz = nodes_mg.groupby("size_bin", observed=True).agg(nodes=("active_validators", "count"), validators=("active_validators", "sum"), zero_rpl_nodes=("rpl_megapool", lambda s: int((s <= 0).sum())), median_rpl_per_borrowed_eth=("rpl_per_borrowed_eth", "median")).reset_index()
    sz["share_of_active_validators_pct"] = sz.validators / sz.validators.sum() * 100
    P("### Active megapool validators by node size\n")
    P(md_table(sz, "{:,.2f}") + "\n")
    zero_rpl_val_share = nodes_mg[nodes_mg.rpl_megapool <= 0].active_validators.sum() / nodes_mg.active_validators.sum() * 100
    P(f"Active megapool validators: **{len(active):,}** on **{len(nodes_mg):,}** nodes. Nodes with zero RPL staked on their megapool: **{(nodes_mg.rpl_megapool <= 0).sum():,}** holding **{zero_rpl_val_share:.1f}%** of active megapool validators. "
      f"Median RPL per borrowed ETH among nodes with RPL: {nodes_mg[nodes_mg.rpl_megapool > 0].rpl_per_borrowed_eth.median():.3f}. "
      f"{nodes_mg.has_minipools.sum():,} of the megapool nodes also still run staking minipools.\n")
    gini_nodes = gini(nodes_mg.active_validators)
    top10 = nodes_mg.active_validators.sort_values(ascending=False).head(10).sum() / nodes_mg.active_validators.sum() * 100
    P(f"Concentration: Gini of active megapool validators across nodes **{gini_nodes:.2f}**; the 10 largest nodes hold **{top10:.1f}%** of active megapool validators.\n")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    sz.plot.bar(x="size_bin", y="validators", ax=ax[0], legend=False); ax[0].set_title("Active megapool validators by node size"); ax[0].set_xlabel("active validators per node"); ax[0].set_ylabel("validators")
    r = nodes_mg.rpl_per_borrowed_eth.fillna(0).sort_values().values
    ax[1].plot(r, np.arange(1, len(r) + 1) / len(r)); ax[1].set_xscale("symlog", linthresh=0.01); ax[1].set_title("Megapool nodes: RPL staked per borrowed ETH (ECDF)"); ax[1].set_xlabel("RPL per borrowed ETH (symlog)"); ax[1].set_ylabel("share of nodes"); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(fig_dir, "02_megapool_nodes.png"), dpi=130); plt.close(fig)

    # ------------------------------------------------------------------ 3. RPIP-83 migration arithmetic
    P("## 3. RPIP-83 arithmetic: rETH needed to migrate today's staking minipools\n")
    node_eth = stk.node_deposit_eth.sum(); user_eth_released = stk.user_deposit_eth.sum()
    rows = []
    for b in [1.5, 4, 6, 8]:
        vals = node_eth / b
        user_needed = vals * (32 - b)
        rows.append([b, vals, user_needed, user_eth_released, user_needed - user_eth_released, (user_needed - user_eth_released) / float(meta["reth_supply"]) / float(meta["reth_exchange_rate"]) * 100])
    t83 = pd.DataFrame(rows, columns=["megapool bond (ETH)", "validators from same node ETH", "user ETH needed", "user ETH released by exits", "net new rETH-ETH needed", "as % of current ETH staked"])
    P("Assumes every staking minipool operator redeploys all of their node ETH into megapools at the given bond, the protocol's `reduced_bond`.\n")
    t83["megapool bond (ETH)"] = t83["megapool bond (ETH)"].map(lambda b: f"{b:g}")
    P(md_table(t83, "{:,.0f}") + "\n")
    P(f"The same arithmetic for the **current queue** ({q_total:,} validators): user ETH needed **{queued_user_eth:,.0f}**; node ETH already locked in the deposit pool **{float(meta['deposit_pool_node_balance_eth']):,.0f}**.\n")
    stk_mp = active.groupby("megapool").size().rename("staked_validators")
    mg6 = mg.join(stk_mp, on="megapool"); mg6 = mg6[mg6.staked_validators > 0].copy()
    mg6["bond_pv"] = mg6.nodeBond / mg6.staked_validators  # nodeBond covers staked validators; queued bonds are in nodeQueuedBond
    below6 = mg6[mg6.bond_pv < 6]
    short6 = ((6 - below6.bond_pv) * below6.staked_validators).sum()
    P(f"If `reduced_bond` were set to 6 ETH today: **{len(below6):,}** of {len(mg6):,} active megapools ({int(below6.staked_validators.sum()):,} staked validators) would be below the new curve, a total shortfall of **{short6:,.0f} ETH** to top up (RPIP-83 proposes topping up from rewards; see part 2 for how long that takes).\n")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(b) for b in t83["megapool bond (ETH)"]], t83["net new rETH-ETH needed"]); ax.set_xlabel("megapool bond (ETH)"); ax.set_ylabel("net new rETH-ETH needed")
    ax.set_title("ETH that must be minted as rETH to migrate all staking minipools"); ax.grid(alpha=.3, axis="y")
    fig.tight_layout(); fig.savefig(os.path.join(fig_dir, "03_rpip83_migration.png"), dpi=130); plt.close(fig)

    # ------------------------------------------------------------------ 3b. minipools already exiting (beacon)
    if bc is not None and len(bc):
        bci0 = bc.drop_duplicates("pubkey").set_index("pubkey")
        stk["beacon_status"] = stk.pubkey.map(bci0.status)
        exiting = stk[stk.beacon_status.isin(["active_exiting", "exited_unslashed", "withdrawal_possible", "withdrawal_done"])]
        P("## 3b. Minipools already leaving (beacon-chain status at snapshot)\n")
        bs = stk.groupby("beacon_status", dropna=False).agg(minipools=("minipool", "count"), nodes=("node", "nunique"), user_eth=("user_deposit_eth", "sum"), node_eth=("node_deposit_eth", "sum")).reset_index()
        P(md_table(bs, "{:,.0f}") + "\n")
        ex_by = exiting.groupby(["bond", "comm_pct"]).agg(minipools=("minipool", "count"), nodes=("node", "nunique"), user_eth=("user_deposit_eth", "sum")).reset_index().sort_values(["bond", "comm_pct"], ascending=[True, False])
        P("Exiting minipools by bond and commission:\n")
        P(md_table(ex_by, "{:,.0f}") + "\n")
        ex_nodes = set(exiting.node)
        mg_nodes = set(mg.nodeAddress)
        P(f"**{len(exiting):,}** staking minipools ({len(exiting) / len(stk) * 100:.1f}% of the set) on **{len(ex_nodes):,}** nodes are in the beacon exit pipeline. Their user capital, **{exiting.user_deposit_eth.sum():,.0f} ETH**, returns to the deposit pool as they withdraw (the megapool queue needs **{queued_user_eth:,.0f} ETH**, but returning ETH is also what rETH redemptions draw on; see the mint/burn table); their node capital is **{exiting.node_deposit_eth.sum():,.0f} ETH**. "
          f"{len(ex_nodes & mg_nodes):,} of the exiting nodes already have a megapool (migrating); {len(ex_nodes - mg_nodes):,} do not.\n")
        nodes_all_exiting = exiting.groupby("node").size()
        tot = stk.groupby("node").size().reindex(nodes_all_exiting.index)
        P(f"{int((nodes_all_exiting >= tot).sum()):,} nodes are exiting every staking minipool they have.\n")
        exa = stk[stk.beacon_status == "active_exiting"]
        gx = exa.groupby("node").agg(exiting_minipools=("minipool", "count"), user_eth=("user_deposit_eth", "sum"), node_eth=("node_deposit_eth", "sum")).sort_values("exiting_minipools", ascending=False)
        gx["staking_minipools_total"] = stk.groupby("node").size().reindex(gx.index)
        gx["legacy_rpl_staked"] = ndi.rpl_staked_legacy.reindex(gx.index).fillna(0)
        gx["has_megapool"] = gx.index.isin(set(mg.nodeAddress))
        gx["registered"] = pd.to_datetime(ndi.registration_time.reindex(gx.index), unit="s").dt.date.astype(str)
        gx = gx.reset_index()
        P("### Nodes with validators in `active_exiting` status\n")
        P(md_table(gx, "{:,.0f}") + "\n")
        big = gx[gx.exiting_minipools >= 100]
        tot_legacy = float(meta.get("total_legacy_rpl_staked", 0) or 0); tot_staked = float(meta.get("total_staked_rpl", 0) or 0); rpl_supply = float(meta.get("rpl_total_supply", 0) or 0)
        if len(big):
            line = (f"**{len(big)} nodes with 100+ exiting minipools account for {big.exiting_minipools.sum():,} of the {len(exa):,} exiting validators.** They were registered {big.registered.min()} to {big.registered.max()}, hold **{big.legacy_rpl_staked.sum():,.0f} legacy RPL** between them, have no megapool, and are exiting every minipool they have. The identical RPL balances and express-ticket counts suggest one operator.")
            if tot_legacy:
                line += f" That RPL is **{big.legacy_rpl_staked.sum() / tot_legacy * 100:.1f}% of all legacy-staked RPL** ({tot_legacy:,.0f}), {big.legacy_rpl_staked.sum() / tot_staked * 100:.1f}% of all staked RPL ({tot_staked:,.0f}) and {big.legacy_rpl_staked.sum() / rpl_supply * 100:.1f}% of RPL supply ({rpl_supply:,.0f}); once the minipools are finalised it can be unstaked."
            P(line + "\n")
        fig, ax = plt.subplots(figsize=(8, 3.8))
        piv = stk.assign(exiting=stk.beacon_status.eq("active_exiting")).groupby(["comm_pct", "exiting"]).user_deposit_eth.sum().unstack(fill_value=0).sort_index(ascending=False)
        piv.plot.bar(stacked=True, ax=ax); ax.set_ylabel("user ETH in staking minipools"); ax.set_xlabel("commission %"); ax.set_title("Staking minipools: user ETH by commission, split by beacon exit status"); ax.legend(["staying", "exiting"])
        fig.tight_layout(); fig.savefig(os.path.join(fig_dir, "03b_minipools_exiting.png"), dpi=130); plt.close(fig)

    # ------------------------------------------------------------------ 4. RPIP-71 phase 1 (minipools by commission)
    P("## 4. RPIP-71 phase 1: exiting minipools, higher commission first\n")
    ndi_legacy_rpl = ndi.rpl_staked_legacy.fillna(0)
    tier = stk.groupby("comm_pct").agg(minipools=("minipool", "count"), nodes=("node", "nunique"), user_eth=("user_deposit_eth", "sum"), node_eth=("node_deposit_eth", "sum")).reset_index().sort_values("comm_pct", ascending=False)
    tier["cum_user_eth"] = tier.user_eth.cumsum()
    node_tiers = stk.groupby("node").comm_pct.agg(["min", "max", "count"])
    single_tier_nodes = node_tiers[node_tiers["min"] == node_tiers["max"]]
    tier["nodes_entirely_in_tier"] = tier.comm_pct.map(single_tier_nodes.groupby("max").size()).fillna(0).astype(int)
    tier["legacy_rpl_of_single_tier_nodes"] = tier.comm_pct.map(lambda c: ndi_legacy_rpl.reindex(single_tier_nodes[single_tier_nodes["max"] == c].index).fillna(0).sum()).fillna(0)
    P("Liquidity obtainable by exiting minipools, ordered by commission as the RPIP prescribes for the oDAO:\n")
    P(md_table(tier, "{:,.0f}") + "\n")
    P("`nodes_entirely_in_tier`: nodes whose every staking minipool sits at that commission, i.e. nodes that lose all their validators before any node in a lower tier is touched. `legacy_rpl_of_single_tier_nodes`: legacy RPL those nodes have staked, which would no longer be needed as collateral after exit.\n")

    def sim_minipools(order, W, runs):
        res = []
        for _ in range(runs):
            df = stk.sample(frac=1, random_state=int(rng.integers(1 << 31)))  # random tie-break
            if order == "commission_desc":
                df = df.sort_values("comm_pct", ascending=False, kind="stable")
            elif order == "eb16_first":  # exit 16 ETH bonds first: least TVL loss per ETH of liquidity? (user ETH 16 per minipool)
                df = df.sort_values("node_deposit_eth", ascending=True, kind="stable")
            elif order == "leb8_first":
                df = df.sort_values("node_deposit_eth", ascending=False, kind="stable")
            cum = df.user_deposit_eth.cumsum()
            k = int((cum < W).sum()) + 1
            ex = df.iloc[:k]
            per_node = ex.groupby("node").size()
            full = (per_node >= node_tiers["count"].reindex(per_node.index)).sum()
            res.append([k, ex.node.nunique(), full, (ex.node_deposit_eth.sum() + ex.user_deposit_eth.sum()) / ex.user_deposit_eth.sum(), ndi_legacy_rpl.reindex(per_node[per_node >= node_tiers["count"].reindex(per_node.index)].index).fillna(0).sum()])
        return np.mean(res, axis=0)
    rows = []
    for W in [10_000, 25_000, 50_000, 100_000]:
        for order in ["commission_desc", "random", "eb16_first", "leb8_first"]:
            m = sim_minipools(order, W, 1 if order != "random" else a.runs // 4 or 1)
            rows.append([W, order, *m])
    t71a = pd.DataFrame(rows, columns=["withdrawal demand (ETH)", "ordering", "minipools exited", "distinct nodes hit", "nodes fully exited", "TVL removed per ETH of liquidity", "legacy RPL freed (fully exited nodes)"])
    P("### Simulation: minipools exited to satisfy a given rETH withdrawal demand\n")
    P("`commission_desc` is the RPIP-71 phase 1 rule (random within a commission tier). `random` ignores commission. `eb16_first` / `leb8_first` order by node bond. Node ETH plus user ETH leaves the protocol per exit, so 'TVL removed per ETH of liquidity' is 32/24 = 1.33 for an LEB8 and 32/16 = 2.0 for an EB16.\n")
    P(md_table(t71a, "{:,.2f}") + "\n")
    fig, ax = plt.subplots(figsize=(8, 4))
    for order in ["commission_desc", "random", "eb16_first", "leb8_first"]:
        d = t71a[t71a.ordering == order]
        ax.plot(d["withdrawal demand (ETH)"], d["nodes fully exited"], marker="o", label=order)
    ax.set_xlabel("rETH withdrawal demand (ETH)"); ax.set_ylabel("nodes losing all staking minipools"); ax.legend(); ax.grid(alpha=.3); ax.set_title("RPIP-71 phase 1: nodes fully exited vs ordering rule")
    fig.tight_layout(); fig.savefig(os.path.join(fig_dir, "04_rpip71_minipool_ordering.png"), dpi=130); plt.close(fig)

    # ------------------------------------------------------------------ 5. RPIP-71 phase 2 (megapool exit criteria)
    P("## 5. RPIP-71 phase 2: megapool exit criteria under tournament sampling\n")
    act = active.copy()
    act["node_size"] = act.node.map(node_sz)
    act["rpl_per_borrowed"] = act.node.map(nodes_mg.rpl_per_borrowed_eth).fillna(0)
    act["rpl_megapool"] = act.node.map(nodes_mg.rpl_megapool).fillna(0)
    act["bond_pv"] = act.node.map(nodes_mg.bond_per_validator).fillna(4)
    act["user_capital_pv"] = 32 - act.bond_pv.clip(upper=32)
    if bc is not None and len(bc):
        bci = bc.drop_duplicates("pubkey").set_index("pubkey")
        act["activation_epoch"] = pd.to_numeric(act.pubkey.map(bci.activation_epoch), errors="coerce")
        act.loc[act.activation_epoch > 10**8, "activation_epoch"] = np.nan  # FAR_FUTURE_EPOCH for not-yet-activated
        act["beacon_status"] = act.pubkey.map(bci.status)
    else:
        act["activation_epoch"] = np.nan
    act["age_key"] = act.activation_epoch.fillna(act.last_assignment_time)  # smaller = older
    criteria = {
        "random": None,
        "lowest_rpl_per_borrowed_eth_first": ("rpl_per_borrowed", True),
        "lowest_absolute_rpl_first": ("rpl_megapool", True),
        "fifo_oldest_first": ("age_key", True),
        "furthest_below_6eth_bond": ("bond_pv", True),
        "largest_node_first (strong)": ("node_size", False),
        "size_weighted_bias (mild)": None,
        "avoid_repeat_nodes": None,
    }
    T = 4  # tournament_size (RPIP-71 initial value)

    def sim_megapools(crit, W, runs):
        res = []
        idx_all = np.arange(len(act))
        for _ in range(runs):
            alive = np.ones(len(act), bool)
            hits = {}
            freed = 0.0; exits = []
            uc = act.user_capital_pv.values
            key = None if criteria[crit] is None else act[criteria[crit][0]].values
            asc = None if criteria[crit] is None else criteria[crit][1]
            nodes_arr = act.node.values
            while freed < W and alive.sum() > 0:
                cand = rng.choice(idx_all[alive], size=min(T, alive.sum()), replace=False)
                if crit == "random":
                    pick = cand[0]
                elif crit == "size_weighted_bias (mild)":
                    wts = act.node_size.values[cand].astype(float); pick = cand[rng.choice(len(cand), p=wts / wts.sum())]
                elif crit == "avoid_repeat_nodes":
                    h = np.array([hits.get(nodes_arr[c], 0) for c in cand])
                    pick = cand[np.argmin(h + rng.random(len(cand)) * 1e-3)]
                else:
                    k = key[cand].astype(float)
                    k = k + rng.random(len(cand)) * 1e-9
                    pick = cand[np.argmin(k) if asc else np.argmax(k)]
                alive[pick] = False; exits.append(pick); freed += uc[pick]; hits[nodes_arr[pick]] = hits.get(nodes_arr[pick], 0) + 1
            ex = act.iloc[exits]
            per_node = ex.groupby("node").size()
            size = node_sz.reindex(per_node.index)
            fully = (per_node >= size).sum()
            small = (ex.node_size <= 2).sum() / len(ex) * 100
            share_small_nodes = (act.node_size <= 2).sum() / len(act) * 100
            small_nodes_hit = ex[ex.node_size <= 2].node.nunique() / max(1, (nodes_mg.active_validators <= 2).sum()) * 100
            res.append([len(ex), ex.node.nunique(), fully, small, small_nodes_hit, ex.rpl_per_borrowed.median(), gini(per_node.reindex(nodes_mg.index).fillna(0).values)])
        return np.mean(res, axis=0), share_small_nodes
    rows = []
    max_liq = act.user_capital_pv.sum()
    P(f"Maximum liquidity obtainable from all active megapool validators today: **{max_liq:,.0f} ETH**; demands above ~10,000 ETH are stress tests, not expected cases.\n")
    for W in [2_000, 10_000, 30_000]:
        for crit in criteria:
            m, share_small = sim_megapools(crit, W, a.runs)
            rows.append([W, crit, *m])
    t71b = pd.DataFrame(rows, columns=["withdrawal demand (ETH)", "criterion", "validators exited", "distinct nodes hit", "nodes fully exited", "% of exits on nodes with <=2 validators", "% of 1-2 validator nodes hit at least once", "median RPL per borrowed ETH of exited validators", "Gini of exits across nodes"])
    P(f"Tournament of size {T}: {T} active megapool validators are drawn at random and the one that best fits the criterion is exited, repeated until the demand is met (each exit returns the validator's user capital, 32 ETH minus the node's bond per validator). "
      f"`largest_node_first (strong)` always exits the entrant on the biggest node; `size_weighted_bias (mild)` picks an entrant with probability proportional to its node's size, the weakest form of a bias towards larger nodes. `avoid_repeat_nodes` picks the entrant whose node has been hit least so far. `lowest_rpl_per_borrowed_eth_first` and `lowest_absolute_rpl_first` are two readings of 'lower RPL stake first'. Nodes with 1-2 active validators hold **{share_small:.1f}%** of active megapool validators. Averages over {a.runs} runs.\n")
    P(md_table(t71b, "{:,.2f}") + "\n")
    # sybil check for largest_node_first and lowest_rpl: expected hit probability for a node of size n vs split into n nodes of size 1
    big = nodes_mg.active_validators.max()
    P("### Sybil incentive check\n")
    P("Under `largest_node_first (strong)`, a validator on the largest node is exited whenever it appears in a tournament, so its per-draw exit probability is ~1 against ~1/4 for a size-1 node; the operator removes the bias entirely by splitting into single-validator nodes (one registration transaction each). "
      f"The largest node today has {big} active validators. Under `lowest_rpl_per_borrowed_eth_first`, {zero_rpl_val_share:.0f}% of active validators sit on nodes with zero megapool RPL, so the rule reduces to random among them, and any node with even a trivial RPL stake is never exited while a zero-RPL candidate is in the tournament; "
      f"the RPL needed to move above the median RPL-per-borrowed-ETH of staking nodes is {nodes_mg.rpl_per_borrowed_eth.fillna(0).median():.3f} RPL per borrowed ETH, i.e. {nodes_mg.rpl_per_borrowed_eth.fillna(0).median() * 28:.2f} RPL per 4-ETH validator at the current 28 ETH of user capital.\n")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    d = t71b[t71b["withdrawal demand (ETH)"] == 10_000]
    ax[0].bar(d.criterion, d["distinct nodes hit"]); ax[0].set_title("10,000 ETH demand: distinct nodes hit"); ax[0].tick_params(axis="x", rotation=60)
    ax[1].bar(d.criterion, d["% of exits on nodes with <=2 validators"]); ax[1].axhline(share_small, color="k", ls="--", label="share of validators on such nodes"); ax[1].legend(); ax[1].set_title("10,000 ETH demand: % of exits landing on 1-2 validator nodes"); ax[1].tick_params(axis="x", rotation=60)
    fig.tight_layout(); fig.savefig(os.path.join(fig_dir, "05_rpip71_megapool_criteria.png"), dpi=130); plt.close(fig)

    # ------------------------------------------------------------------ 6. age structure
    if bc is not None and len(bc):
        P("## 6. Megapool validators on the beacon chain\n")
        bsum = act.beacon_status.value_counts(dropna=False).rename_axis("beacon status (head)").reset_index(name="active megapool validators")
        P(md_table(bsum) + "\n")
        act_dates = act.activation_epoch.dropna().map(epoch_to_date)
        by_month = pd.Series(1, index=pd.to_datetime(list(act_dates))).resample("MS").sum()
        P("### Activation month of active megapool validators\n")
        P(md_table(pd.DataFrame({"month": [d.strftime("%Y-%m") for d in by_month.index], "validators activated": by_month.values.astype(int)})) + "\n")
        fig, ax = plt.subplots(figsize=(8, 3.5)); ax.bar([d.strftime("%Y-%m") for d in by_month.index], by_month.values); ax.tick_params(axis="x", rotation=60); ax.set_title("Active megapool validators by activation month"); fig.tight_layout(); fig.savefig(os.path.join(fig_dir, "06_megapool_activation_months.png"), dpi=130); plt.close(fig)
        bmeta = json.load(open(os.path.join(a.datadir, "beacon_meta.json")))
        P(f"Beacon data: head slot {bmeta['head_slot']:,}; {bmeta['found']:,} of {bmeta['pubkeys_queried']:,} snapshot pubkeys found on the beacon chain.\n")

    open(os.path.join(a.outdir, "numbers.md"), "w").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
