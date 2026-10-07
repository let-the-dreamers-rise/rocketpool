# Saturn 2 decision data from the live Rocket Pool validator set

Snapshot: Ethereum mainnet block 26,118,341 (4 October 2026, 10:18 UTC), beacon head slot 15,357,280.
Everything here is reproducible from `data/` with `python3 analyze.py`; the generated tables are in
`report/numbers.md`, figures in `report/figures/`. Collection used only public RPC `eth_call`s via
Multicall3, one archive RPC for weekly history, and one public beacon API for current validator
status. No keys, no accounts, no paid services.

Scope: numbers for the questions the pDAO is deciding in the Saturn 2 votes (RPIP-71 inclusion and
megapool exit criterion, megapool bond 1.5 / 4 / 6 ETH) and at implementation (RPIP-71 phase 1
ordering, RPIP-83 top-ups). Not covered: RPIP-73 attestation performance, which needs 200 days of
per-epoch beacon data that no public endpoint serves.

## Findings

**1. rETH is shrinking and the megapool queue has been frozen since launch.**
ETH represented by rETH fell from 449,234 (1 Oct 2025) to 370,719 (30 Sep 2026): −78,515 ETH in a
year, −9,288 ETH in the trailing 90 days (−3,062 ETH per 30 days). The queue has sat at 1,900–2,100
validators every week since Saturn 1 (contracts live 18 Feb 2026). Today it is 2,107 validators
(1,314 express, 793 standard) needing 58,996 ETH of user capital; the deposit pool holds 31.7 ETH, of
which 8,428 ETH is node bonds waiting.

Where the capital went since Saturn 1: staking minipools fell by 3,304 (17,424 to 14,120), releasing
roughly 74,000 ETH of rETH capital at today's 22.5 ETH average per pool. Megapools now hold 61,572
ETH of user capital, all assigned since launch. ETH behind rETH changed by −25,525 over the period,
about 5,500 of it accrued rewards, so net rETH redemptions were roughly 31,000 ETH. Net new rETH
demand contributed nothing; released minipool capital went partly to megapool funding and partly out
through redemptions, because rETH trades below its exchange rate and redemptions take ETH whenever
the deposit pool has any.

**2. One operator is exiting 2,460 minipools and holds 29% of all legacy-staked RPL.**
2,472 staking minipools (17.5% of the set) are `active_exiting` at the snapshot: 55,320 ETH of user
capital returning, 23,784 ETH of node capital leaving. 2,460 of them sit on six nodes registered
2021–2023 with 260–550 minipools each, identical RPL balances (325,000 / 326,417) and 1,200 express
tickets each, no megapool, not in the smoothing pool, exiting every pool they have. Together they
stake 1,936,015 legacy RPL: 29.0% of all legacy-staked RPL (6.68M), 19.1% of all staked RPL (10.11M),
8.5% of RPL supply (22.88M). Once the minipools are finalised that RPL can be unstaked. By the
Saturn 1 pattern above, the returning user capital will be split between funding the queue and
rETH redemptions; it will not fund the whole queue.

**3. RPIP-83 arithmetic.** Re-housing today's 14,099 staking minipools (133,936 ETH node capital,
317,232 ETH user capital) in megapools, with operators redeploying all node ETH:

| bond | validators | user ETH needed | released by exits | net new rETH-ETH needed | % of ETH staked today |
|---|---|---|---|---|---|
| 1.5 | 89,291 | 2,723,365 | 317,232 | 2,406,133 | 650% |
| 4 | 33,484 | 937,552 | 317,232 | 620,320 | 168% |
| 6 | 22,323 | 580,389 | 317,232 | 263,157 | 71% |
| 8 | 16,742 | 401,808 | 317,232 | 84,576 | 23% |

With net rETH flow negative, none of these is reachable from organic demand. A 6 ETH
`reduced_bond` today would put 86 of 112 active megapool nodes (1,910 of 2,164 validators) below the
curve, with a combined top-up of 3,684 ETH.

**4. Megapools are concentrated.** 2,164 active megapool validators on 112 nodes; the 10 largest
nodes hold 70.1%, one node has 798, Gini 0.80. 24 nodes (12.2% of validators) stake zero RPL on
their megapool. Nodes with 1–2 validators are 47 of 112 nodes but 3.5% of validators. 56 of the 112
megapool nodes still run staking minipools. Activation months: 1,651 in June 2026, 350 in July, 64
in August, 85 in September. Maximum liquidity obtainable from all active megapool validators:
58,608 ETH.

**5. RPIP-71 phase 1 (oDAO exits minipools, higher commission first).** Every minipool at 16–20%
commission is a 16-ETH bond (8,016 ETH user capital at 20%); the 15% tier is 1,458 16-ETH pools
(23,328 ETH); the 14% tier is 8,726 pools, 206,240 ETH, 918 nodes. Commission is clustered by node:
702 nodes have every minipool at 14%, 229 at 5%, 120 at 15%. With random tie-breaks within a tier:

| demand | ordering | minipools exited | nodes hit | nodes fully exited | TVL removed per ETH of liquidity | legacy RPL freed (fully exited nodes) |
|---|---|---|---|---|---|---|
| 10,000 ETH | commission first | 625 | 81 | 34 | 2.00 | 35,246 |
| 10,000 ETH | random | 445 | 204 | 15 | 1.42 | 8,695 |
| 25,000 ETH | commission first | 1,563 | 236 | 122 | 2.00 | 97,280 |
| 25,000 ETH | random | 1,112 | 374 | 40 | 1.42 | 24,563 |
| 50,000 ETH | commission first | 2,817 | 516 | 198 | 1.80 | 164,526 |
| 50,000 ETH | random | 2,222 | 561 | 80 | 1.42 | 51,892 |

Commission-first returns 16 ETH of liquidity per 32 ETH of TVL until the 16-ETH tiers are
exhausted at ~34,640 ETH of demand, and fully exits two to three times as many nodes as random
selection. Whether TVL or rETH commission matters more is the judgement epineph and knoshua
disagreed on in the RPIP-86 thread; these are the sizes.

**6. RPIP-71 phase 2 (megapool exit criterion, tournament of 4).** Four active megapool validators
are drawn at random and the one that best fits the criterion is exited, repeated until the demand is
met. 10,000 ETH of demand (about 360–380 exits), averaged over 200 runs:

| criterion | nodes hit | nodes fully exited | % of exits on 1–2 validator nodes | % of 1–2 validator nodes hit | median RPL per borrowed ETH of exited |
|---|---|---|---|---|---|
| random | 62 | 4.3 | 3.5 | 26 | 23.7 |
| lowest RPL per borrowed ETH first | 58 | 7.1 | 4.2 | 30 | 0.6 |
| lowest absolute RPL first | 81 | 12.2 | 7.3 | 50 | 0.8 |
| FIFO, oldest first | 56 | 7.4 | 4.1 | 28 | 12.2 |
| furthest below 6 ETH bond | 47 | 3.6 | 3.0 | 22 | 52.3 |
| largest node first (strong form) | 12 | 0 | 0 | 0 | 61.3 |
| size-weighted bias (mild form) | 22 | 0.1 | 0.1 | 0.6 | 61.3 |
| avoid repeat nodes | 93 | 16.6 | 9.5 | 64 | 7.8 |

Random, RPL-per-borrowed-ETH and FIFO land on small nodes roughly in proportion to their 3.5% share.
Both forms of a bias towards large nodes put nearly every exit on the top 12–22 nodes, because one
node holds 798 of 2,164 validators; the strong form is defeated by splitting a node into
single-validator nodes. "Avoid repeat nodes" spreads exits widest and is hardest on small operators:
at 30,000 ETH (a stress case above half of all megapool liquidity) it touches 97% of 1–2 validator
nodes and fully exits 70. "Lowest RPL first" is random among the 12% of validators on zero-RPL nodes,
then shields anyone with a trivial stake: about 7.6 RPL per borrowed ETH, 212 RPL per 4-ETH
validator (~0.15 ETH today), moves a node above the median; the absolute-RPL reading hits small nodes
twice as often as the per-ETH reading.

## Method and caveats

- All 42,317 minipool contracts read; 14,099 are status Staking and not finalised; no initialised
  or prelaunch pools existed at the block.
- All 5,186 megapool validator records: 2,169 staked (5 exiting), 2,107 in queue, 30 in prestake,
  880 created but never funded (dequeued or never deposited; zero deposit value, no beacon record).
- Node RPL and ETH figures from `RocketNodeStaking`; registration time, express tickets and
  smoothing pool from `RocketNodeManager`. Protocol RPL totals read on 6 Oct 2026.
- Beacon status for 16,268 of 19,229 pubkeys; the rest are queued, prestake or never-funded
  megapool validators not on the beacon chain yet. 55 further staking minipools are in later exit
  states (exited, withdrawable, withdrawn), bringing the pools leaving to 2,527 on 33 nodes.
- Weekly history from an archive RPC (`eth.drpc.org`), 1 Oct 2025 to 30 Sep 2026, 53 samples.
  Public RPCs do not serve historical event logs, so mint and burn volumes are reconciled from
  supply and counts rather than read from events; the ~74k / ~31k figures are estimates.
- The phase 2 simulation follows the spec's tournament sampling (`tournament_size` 4) and returns
  each exit's user capital (32 ETH minus the node's bond per validator). It ignores exit hysteresis,
  the withdrawal-queue threshold and the beacon exit queue. "Furthest below 6 ETH bond" assumes
  RPIP-83 is adopted; at the current 4 ETH bond all nodes tie. "Largest node first" and "avoid
  repeat nodes" are the strong forms of the RPIP's "biasing towards"; the size-weighted variant is
  the mild form.
- RPIP-83 arithmetic assumes full redeployment of node ETH; the "net new rETH needed" figures are
  upper bounds on demand and lower bounds on the ETH that leaves.
- The six exiting nodes are described as one operator because of identical balances and ticket
  counts; no name is attached.

## Reproduce

```
pip install web3 pandas matplotlib
python3 collect_snapshot_multicall.py --outdir data --block 26118341 --rpc https://eth.drpc.org
python3 collect_history.py --start 2025-10-01 --out data/history.csv
python3 collect_beacon.py --datadir data --beacon https://lodestar-mainnet.chainsafe.io
python3 analyze.py --datadir data --outdir report --runs 200
```

Code MIT, data and figures CC BY 4.0.
