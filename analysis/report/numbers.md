# Generated numbers (block 26,118,341, 2026-10-04, https://eth.drpc.org)

All figures below are produced by `analyze.py` from the CSVs in `data/`. Rerun to refresh.

## 1. Supply and demand

| Metric | Value |
|---|---|
| rETH supply | 315,629 |
| rETH exchange rate (ETH per rETH) | 1.1731 |
| ETH represented by rETH (supply x rate) | 370,263 |
| Deposit pool balance (ETH) | 31.7391 |
|   of which node ETH waiting in queue | 8,428 |
|   of which user (rETH) ETH available | -8,396 |
| Megapool validators in queue (express + standard) | 2,107 |
|   express | 1,314 |
|   standard | 793 |
| User ETH needed to fund the whole queue | 58,996 |
| Megapool validators registered | 5,186 |
| Megapool contracts | 361 |
| Minipools total / live (initialised, prelaunch, staking) | 42,317 / 14,099 |
| Registered nodes | 4,159 |
| RPL price (ETH) | 0.0007 |

### rETH supply trend (weekly samples from archive RPC)

| Window | From | To | rETH supply change | ETH-staked change | Per 30 days (ETH) |
|---|---|---|---|---|---|
| Full history in file | 2025-10-01 | 2026-09-30 | -75,553 | -78,515 | -6,471 |
| Trailing ~90 days | 2026-07-01 | 2026-09-30 | -9,687 | -9,288 | -3,062 |
| Since Saturn 1 contracts (18 Feb 2026) | 2026-02-18 | 2026-09-30 | -26,147 | -25,525 | -3,419 |

The trailing-90-day net flow into rETH is **-3,062 ETH per 30 days** (negative or zero): at this rate the 58,996 ETH of queued demand is never funded by organic minting; the queue only moves when validators exit or rETH holders deposit.

### Where the ETH freed by minipool exits went (since Saturn 1)

Staking minipools fell by **3,304** between 2026-02-18 and 2026-09-30. At today's average user capital per staking minipool (22.5 ETH) that freed roughly **74,341 ETH** of rETH capital. Megapools now hold **61,572 ETH** of user capital, all assigned since Saturn 1. ETH behind rETH changed by **-25,525 ETH** over the period, of which about 5,471 ETH is accrued staking rewards, so net redemptions (burns minus mints) were roughly **30,996 ETH**. The deposit pool also held about 12,000 ETH in early February that was consumed at launch. In short: capital released by minipool exits went partly to funding megapool validators and partly out through rETH redemptions; net new rETH demand contributed nothing. Expect the capital now returning from the exits in progress to be split the same way, so it will not fund the whole queue.

## 2. Composition of the validator set

### Staking minipools by node bond and commission

| bond | comm_pct | minipools | nodes | node_eth | user_eth |
|---|---|---|---|---|---|
| 8 | 14 | 8,328 | 841 | 66,624 | 199,872 |
| 8 | 5 | 3,128 | 358 | 25,024 | 75,072 |
| 16 | 20 | 501 | 69 | 8,016 | 8,016 |
| 16 | 19 | 75 | 22 | 1,200 | 1,200 |
| 16 | 18 | 78 | 18 | 1,248 | 1,248 |
| 16 | 17 | 38 | 15 | 608 | 608 |
| 16 | 16 | 15 | 11 | 240 | 240 |
| 16 | 15 | 1,458 | 210 | 23,328 | 23,328 |
| 16 | 14 | 398 | 90 | 6,368 | 6,368 |
| 16 | 13 | 7 | 5 | 112 | 112 |
| 16 | 12 | 3 | 3 | 48 | 48 |
| 16 | 11 | 3 | 3 | 48 | 48 |
| 16 | 10 | 8 | 8 | 128 | 128 |
| 16 | 9 | 9 | 5 | 144 | 144 |
| 16 | 8 | 8 | 4 | 128 | 128 |
| 16 | 5 | 42 | 17 | 672 | 672 |

Staking minipools: **14,099** on **1,353** nodes; node ETH **133,936**, user (rETH) ETH **317,232**. Other live minipools: 0 (initialised/prelaunch).

### Megapool validators by state

| state | validators | megapools | nodes | express_used |
|---|---|---|---|---|
| in_queue | 2,107 | 194 | 194 | 1,314 |
| not_funded (dequeued / never deposited) | 880 | 104 | 104 | 0 |
| prestake | 30 | 3 | 3 | 24 |
| staked | 2,169 | 113 | 113 | 1,733 |

### Active megapool validators by node size

| size_bin | nodes | validators | zero_rpl_nodes | median_rpl_per_borrowed_eth | share_of_active_validators_pct |
|---|---|---|---|---|---|
| 1 | 19 | 19 | 6 | 5.09 | 0.88 |
| 2 | 28 | 56 | 2 | 19.48 | 2.59 |
| 3-4 | 20 | 73 | 5 | 3.71 | 3.37 |
| 5-8 | 12 | 77 | 3 | 11.41 | 3.56 |
| 9-16 | 13 | 165 | 3 | 12.92 | 7.62 |
| 17-32 | 8 | 188 | 3 | 6.78 | 8.69 |
| 33-64 | 7 | 308 | 2 | 6.37 | 14.23 |
| 65+ | 5 | 1,278 | 0 | 7.99 | 59.06 |

Active megapool validators: **2,164** on **112** nodes. Nodes with zero RPL staked on their megapool: **24** holding **12.2%** of active megapool validators. Median RPL per borrowed ETH among nodes with RPL: 17.578. 56 of the megapool nodes also still run staking minipools.

Concentration: Gini of active megapool validators across nodes **0.80**; the 10 largest nodes hold **70.1%** of active megapool validators.

## 3. RPIP-83 arithmetic: rETH needed to migrate today's staking minipools

Assumes every staking minipool operator redeploys all of their node ETH into megapools at the given bond, the protocol's `reduced_bond`.

| megapool bond (ETH) | validators from same node ETH | user ETH needed | user ETH released by exits | net new rETH-ETH needed | as % of current ETH staked |
|---|---|---|---|---|---|
| 1.5 | 89,291 | 2,723,365 | 317,232 | 2,406,133 | 650 |
| 4 | 33,484 | 937,552 | 317,232 | 620,320 | 168 |
| 6 | 22,323 | 580,389 | 317,232 | 263,157 | 71 |
| 8 | 16,742 | 401,808 | 317,232 | 84,576 | 23 |

The same arithmetic for the **current queue** (2,107 validators): user ETH needed **58,996**; node ETH already locked in the deposit pool **8,428**.

If `reduced_bond` were set to 6 ETH today: **86** megapool nodes with **1,910** active validators would be below the new curve, a total shortfall of **3,684 ETH** to top up (RPIP-83 proposes topping up from rewards).

## 3b. Minipools already leaving (beacon-chain status at snapshot)

| beacon_status | minipools | nodes | user_eth | node_eth |
|---|---|---|---|---|
| active_exiting | 2,472 | 10 | 55,320 | 23,784 |
| active_ongoing | 11,572 | 1,324 | 260,712 | 109,592 |
| exited_unslashed | 12 | 1 | 288 | 96 |
| withdrawal_done | 39 | 20 | 832 | 416 |
| withdrawal_possible | 4 | 2 | 80 | 48 |

Exiting minipools by bond and commission:

| bond | comm_pct | minipools | nodes | user_eth |
|---|---|---|---|---|
| 8 | 14 | 1,991 | 19 | 47,784 |
| 8 | 5 | 20 | 3 | 480 |
| 16 | 20 | 2 | 2 | 32 |
| 16 | 19 | 1 | 1 | 16 |
| 16 | 18 | 2 | 1 | 32 |
| 16 | 16 | 1 | 1 | 16 |
| 16 | 15 | 509 | 12 | 8,144 |
| 16 | 14 | 1 | 1 | 16 |

**2,527** staking minipools (17.9% of the set) on **33** nodes are in the beacon exit pipeline. Their user capital, **56,520 ETH**, returns to the deposit pool as they withdraw (the megapool queue needs **58,996 ETH**, but returning ETH is also what rETH redemptions draw on; see the mint/burn table); their node capital is **24,344 ETH**. 4 of the exiting nodes already have a megapool (migrating); 29 do not.

29 nodes are exiting every staking minipool they have.

### Nodes with validators in `active_exiting` status

| node | exiting_minipools | user_eth | node_eth | staking_minipools_total | legacy_rpl_staked | has_megapool | registered |
|---|---|---|---|---|---|---|---|
| 0xacB7CFB56D6835d9E2Fa3E3F273A0450468082D9 | 550 | 12,800 | 4,800 | 550 | 325,000 | False | 2022-09-29 |
| 0x663CbbD93B5eE095AC8386C2a301EB1C47D73aA9 | 450 | 9,600 | 4,800 | 450 | 325,000 | False | 2022-05-13 |
| 0x895F6558f0b02F95F48EF0d580eC885056dcCCC6 | 450 | 9,600 | 4,800 | 450 | 326,417 | False | 2022-09-20 |
| 0x7C5d0950584F961f5c1054c88a71B01207Bf9CB7 | 450 | 9,600 | 4,800 | 450 | 326,417 | False | 2022-06-30 |
| 0x22FFBA127F6741a619fa145516EF4D94B90f093A | 300 | 7,200 | 2,400 | 300 | 439,243 | False | 2023-01-18 |
| 0x78072BA5f77d01B3f5B1098df73176933da02A7A | 260 | 6,240 | 2,080 | 260 | 193,938 | False | 2021-11-09 |
| 0x7A1cF8687d3276774c5f92987948A266181efd2B | 9 | 216 | 72 | 9 | 11,136 | True | 2023-05-13 |
| 0x5a75BD25FE2620f25D05597f906DeCed61b2cE22 | 1 | 24 | 8 | 1 | 576 | False | 2024-01-08 |
| 0xCdA38064AE781249b6BDfbf59B029BBB86b60350 | 1 | 16 | 16 | 1 | 466 | False | 2022-06-05 |
| 0xf778Ed88550da17E0545f0B6fCa74591cB2A81EC | 1 | 24 | 8 | 2 | 233 | False | 2023-05-16 |

**6 nodes with 100+ exiting minipools account for 2,460 of the 2,472 exiting validators.** They were registered 2021-11-09 to 2023-01-18, hold **1,936,015 legacy RPL** between them, have no megapool, and are exiting every minipool they have. The identical RPL balances and express-ticket counts suggest one operator. That RPL is **29.0% of all legacy-staked RPL** (6,677,616), 19.1% of all staked RPL (10,112,561) and 8.5% of RPL supply (22,875,011); once the minipools are finalised it can be unstaked.

## 4. RPIP-71 phase 1: exiting minipools, higher commission first

Liquidity obtainable by exiting minipools, ordered by commission as the RPIP prescribes for the oDAO:

| comm_pct | minipools | nodes | user_eth | node_eth | cum_user_eth | nodes_entirely_in_tier | legacy_rpl_of_single_tier_nodes |
|---|---|---|---|---|---|---|---|
| 20 | 501 | 69 | 8,016 | 8,016 | 8,016 | 24 | 20,224 |
| 19 | 75 | 22 | 1,200 | 1,200 | 9,216 | 4 | 3,412 |
| 18 | 78 | 18 | 1,248 | 1,248 | 10,464 | 4 | 1,435 |
| 17 | 38 | 15 | 608 | 608 | 11,072 | 5 | 2,999 |
| 16 | 15 | 11 | 240 | 240 | 11,312 | 1 | 302 |
| 15 | 1,458 | 210 | 23,328 | 23,328 | 34,640 | 120 | 62,078 |
| 14 | 8,726 | 918 | 206,240 | 72,992 | 240,880 | 702 | 2,653,994 |
| 13 | 7 | 5 | 112 | 112 | 240,992 | 3 | 1,326 |
| 12 | 3 | 3 | 48 | 48 | 241,040 | 1 | 2,539 |
| 11 | 3 | 3 | 48 | 48 | 241,088 | 3 | 2,020 |
| 10 | 8 | 8 | 128 | 128 | 241,216 | 6 | 7,350 |
| 9 | 9 | 5 | 144 | 144 | 241,360 | 2 | 1,971 |
| 8 | 8 | 4 | 128 | 128 | 241,488 | 1 | 392 |
| 5 | 3,170 | 372 | 75,744 | 25,696 | 317,232 | 229 | 291,764 |

`nodes_entirely_in_tier`: nodes whose every staking minipool sits at that commission, i.e. nodes that lose all their validators before any node in a lower tier is touched. `legacy_rpl_of_single_tier_nodes`: legacy RPL those nodes have staked, which would no longer be needed as collateral after exit.

### Simulation: minipools exited to satisfy a given rETH withdrawal demand

`commission_desc` is the RPIP-71 phase 1 rule (random within a commission tier). `random` ignores commission. `eb16_first` / `leb8_first` order by node bond. Node ETH plus user ETH leaves the protocol per exit, so 'TVL removed per ETH of liquidity' is 32/24 = 1.33 for an LEB8 and 32/16 = 2.0 for an EB16.

| withdrawal demand (ETH) | ordering | minipools exited | distinct nodes hit | nodes fully exited | TVL removed per ETH of liquidity | legacy RPL freed (fully exited nodes) |
|---|---|---|---|---|---|---|
| 10,000 | commission_desc | 625.00 | 81.00 | 34.00 | 2.00 | 35,246.06 |
| 10,000 | random | 444.60 | 204.28 | 15.04 | 1.42 | 8,694.73 |
| 10,000 | eb16_first | 417.00 | 217.00 | 8.00 | 1.33 | 1,746.25 |
| 10,000 | leb8_first | 625.00 | 162.00 | 46.00 | 2.00 | 25,767.65 |
| 25,000 | commission_desc | 1,563.00 | 236.00 | 122.00 | 2.00 | 97,279.87 |
| 25,000 | random | 1,111.86 | 374.38 | 39.80 | 1.42 | 24,562.53 |
| 25,000 | eb16_first | 1,042.00 | 328.00 | 26.00 | 1.33 | 15,742.13 |
| 25,000 | leb8_first | 1,563.00 | 264.00 | 110.00 | 2.00 | 55,951.09 |
| 50,000 | commission_desc | 2,817.00 | 516.00 | 198.00 | 1.80 | 164,525.84 |
| 50,000 | random | 2,222.26 | 561.00 | 79.88 | 1.42 | 51,891.57 |
| 50,000 | eb16_first | 2,084.00 | 509.00 | 49.00 | 1.33 | 41,167.38 |
| 50,000 | leb8_first | 2,965.00 | 534.00 | 284.00 | 1.90 | 273,437.73 |
| 100,000 | commission_desc | 4,928.00 | 780.00 | 270.00 | 1.58 | 221,423.56 |
| 100,000 | random | 4,445.04 | 819.10 | 180.16 | 1.42 | 119,536.69 |
| 100,000 | eb16_first | 4,167.00 | 724.00 | 130.00 | 1.33 | 98,005.25 |
| 100,000 | leb8_first | 5,048.00 | 880.00 | 357.00 | 1.62 | 345,148.82 |

## 5. RPIP-71 phase 2: megapool exit criteria under tournament sampling

Maximum liquidity obtainable from all active megapool validators today: **58,608 ETH**; demands above ~10,000 ETH are stress tests, not expected cases.

Tournament of size 4: 4 active megapool validators are drawn at random and the one that best fits the criterion is exited, repeated until the demand is met (each exit returns the validator's user capital, 32 ETH minus the node's bond per validator). `largest_node_first (strong)` always exits the entrant on the biggest node; `size_weighted_bias (mild)` picks an entrant with probability proportional to its node's size, the weakest form of a bias towards larger nodes. `avoid_repeat_nodes` picks the entrant whose node has been hit least so far. `lowest_rpl_per_borrowed_eth_first` and `lowest_absolute_rpl_first` are two readings of 'lower RPL stake first'. Nodes with 1-2 active validators hold **3.5%** of active megapool validators. Averages over 200 runs.

| withdrawal demand (ETH) | criterion | validators exited | distinct nodes hit | nodes fully exited | % of exits on nodes with <=2 validators | % of 1-2 validator nodes hit at least once | median RPL per borrowed ETH of exited validators | Gini of exits across nodes |
|---|---|---|---|---|---|---|---|---|
| 2,000 | random | 74.50 | 26.64 | 0.68 | 3.52 | 5.49 | 30.85 | 0.89 |
| 2,000 | lowest_rpl_per_borrowed_eth_first | 75.39 | 27.66 | 0.99 | 3.95 | 6.21 | 0.54 | 0.86 |
| 2,000 | lowest_absolute_rpl_first | 75.55 | 35.45 | 1.79 | 7.55 | 11.77 | 0.69 | 0.81 |
| 2,000 | fifo_oldest_first | 75.56 | 29.17 | 1.04 | 4.26 | 6.66 | 12.29 | 0.86 |
| 2,000 | furthest_below_6eth_bond | 72.00 | 20.33 | 0.60 | 2.94 | 4.43 | 45.66 | 0.93 |
| 2,000 | largest_node_first (strong) | 72.08 | 6.16 | 0.00 | 0.00 | 0.00 | 61.28 | 0.98 |
| 2,000 | size_weighted_bias (mild) | 72.38 | 9.68 | 0.01 | 0.08 | 0.12 | 61.28 | 0.98 |
| 2,000 | avoid_repeat_nodes | 76.59 | 47.34 | 2.02 | 9.14 | 14.54 | 7.61 | 0.69 |
| 10,000 | random | 370.14 | 61.71 | 4.25 | 3.49 | 25.73 | 23.69 | 0.83 |
| 10,000 | lowest_rpl_per_borrowed_eth_first | 373.33 | 58.22 | 7.07 | 4.21 | 29.55 | 0.56 | 0.82 |
| 10,000 | lowest_absolute_rpl_first | 374.48 | 81.03 | 12.18 | 7.27 | 49.85 | 0.84 | 0.71 |
| 10,000 | fifo_oldest_first | 374.19 | 56.48 | 7.38 | 4.12 | 28.49 | 12.18 | 0.82 |
| 10,000 | furthest_below_6eth_bond | 358.00 | 46.93 | 3.61 | 3.04 | 21.61 | 52.25 | 0.89 |
| 10,000 | largest_node_first (strong) | 359.20 | 12.44 | 0.00 | 0.00 | 0.00 | 61.28 | 0.98 |
| 10,000 | size_weighted_bias (mild) | 360.82 | 22.05 | 0.06 | 0.07 | 0.55 | 61.28 | 0.97 |
| 10,000 | avoid_repeat_nodes | 381.55 | 93.41 | 16.57 | 9.52 | 64.20 | 7.77 | 0.57 |
| 30,000 | random | 1,108.13 | 94.28 | 19.05 | 3.44 | 66.07 | 22.31 | 0.81 |
| 30,000 | lowest_rpl_per_borrowed_eth_first | 1,111.79 | 85.57 | 38.85 | 4.08 | 69.64 | 3.69 | 0.80 |
| 30,000 | lowest_absolute_rpl_first | 1,119.65 | 109.08 | 58.17 | 5.82 | 93.87 | 4.46 | 0.70 |
| 30,000 | fifo_oldest_first | 1,109.72 | 80.84 | 34.36 | 3.46 | 61.07 | 31.04 | 0.83 |
| 30,000 | furthest_below_6eth_bond | 1,072.00 | 73.19 | 18.68 | 3.02 | 52.96 | 60.23 | 0.88 |
| 30,000 | largest_node_first (strong) | 1,082.83 | 22.90 | 0.00 | 0.00 | 0.00 | 61.28 | 0.97 |
| 30,000 | size_weighted_bias (mild) | 1,087.04 | 40.24 | 0.20 | 0.15 | 3.49 | 61.28 | 0.95 |
| 30,000 | avoid_repeat_nodes | 1,132.44 | 110.81 | 69.83 | 6.23 | 97.48 | 7.99 | 0.66 |

### Sybil incentive check

Under `largest_node_first (strong)`, a validator on the largest node is exited whenever it appears in a tournament, so its per-draw exit probability is ~1 against ~1/4 for a size-1 node; the operator removes the bias entirely by splitting into single-validator nodes (one registration transaction each). The largest node today has 798 active validators. Under `lowest_rpl_per_borrowed_eth_first`, 12% of active validators sit on nodes with zero megapool RPL, so the rule reduces to random among them, and any node with even a trivial RPL stake is never exited while a zero-RPL candidate is in the tournament; the RPL needed to move above the median RPL-per-borrowed-ETH of staking nodes is 7.569 RPL per borrowed ETH, i.e. 211.92 RPL per 4-ETH validator at the current 28 ETH of user capital.

## 6. Megapool validators on the beacon chain

| beacon status (head) | active megapool validators |
|---|---|
| active_ongoing | 2,157 |
| pending_initialized | 7 |

### Activation month of active megapool validators

| month | validators activated |
|---|---|
| 2026-06 | 1,651 |
| 2026-07 | 350 |
| 2026-08 | 64 |
| 2026-09 | 85 |
| 2026-10 | 7 |

Beacon data: head slot 15,357,280; 16,268 of 19,229 snapshot pubkeys found on the beacon chain.
