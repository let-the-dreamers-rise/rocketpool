# Part 2: exit timing, queue funding, bond top-up (block 26,118,341, beacon head epoch 479,915)

## 7. When the exiting minipools' ETH comes back

2,472 minipools are `active_exiting`. Exit epochs run 481,623 to 482,028 (2026-10-12 to 2026-10-13), withdrawable epochs 481,879 to 482,284 (2026-10-13 to 2026-10-14). The beacon head at the snapshot was epoch 479,915 (2026-10-04), so the whole batch exits within about 9.4 days of the snapshot. Balances are then paid out by the beacon withdrawal sweep (a few days more), after which the minipool's user share returns to the deposit pool on `distributeBalance`.

Withdrawable date of the exiting minipools (user ETH is what the deposit pool receives):

| wd_date | minipools | user_eth | node_eth | cum_user_eth |
|---|---|---|---|---|
| 2026-10-13 | 710 | 14,976 | 7,744 | 14,976 |
| 2026-10-14 | 1,762 | 40,344 | 16,040 | 55,320 |

## 8. Who the returning ETH funds: the queue in on-chain order

The express queue holds 1,314 entries and the standard queue 793, from 194 megapools. Every entry needs 28 ETH of user capital. `express_queue_rate` is 4, so assignments go 4 express then 1 standard. Express tickets outstanding across all nodes: **33,849** on 1,375 nodes, enough to keep the express queue fed for a long time.

Queue concentration by node (top 15):

| node | queued | express | share_of_queue_pct | cum_share_pct |
|---|---|---|---|---|
| 0x9A8dc6dcD9fDC7efAdbED3803bf3Cd208C91d7C1 | 249 | 249 | 11.8 | 11.8 |
| 0x38362937B202Cb3e28cE71bABbc68dd265B9638c | 200 | 0 | 9.5 | 21.3 |
| 0x8dEA24025cF3080FE46af8511c1Be871302B2d63 | 189 | 178 | 9.0 | 30.3 |
| 0x8AF2565bE72735484c1114a856B5C96735db1eD6 | 175 | 0 | 8.3 | 38.6 |
| 0xc0E7C12756954454937943316B2Ad99e4eBE11aC | 113 | 113 | 5.4 | 43.9 |
| 0xFbEd2f322c918363F6E663E00e923574027C5231 | 106 | 106 | 5.0 | 49.0 |
| 0xaEfb7da80eC25f4e7871A4bDC9Bd8e9Dba94d643 | 64 | 40 | 3.0 | 52.0 |
| 0x4f9DAFfa3Ab242EA906F6674953e42758f0597b9 | 56 | 56 | 2.7 | 54.7 |
| 0x7818614Ff330B1c5C0C00f10710412f48927D1c6 | 43 | 0 | 2.0 | 56.7 |
| 0x9C9E7e6EF247D80CE6e4dEd2a9911B4746543E28 | 41 | 36 | 1.9 | 58.7 |
| 0x4b0E54354d9932a37Cc54aE270a48C29Ca8AD70e | 34 | 34 | 1.6 | 60.3 |
| 0xA5f740E21b4B68f8aB662F64Ea93A7cb0F1d824b | 30 | 30 | 1.4 | 61.7 |
| 0x4CdE259C77fCE161d6a6250371a3e56f83887dB0 | 28 | 28 | 1.3 | 63.0 |
| 0x27DC67Ce834803A02f4aCF407db3E653Cf22c279 | 25 | 22 | 1.2 | 64.2 |
| 0xF6fd4eC926d83AdaDd725E67D4005763832f4679 | 25 | 25 | 1.2 | 65.4 |

The 6 largest queued nodes hold **1,032** of 2,107 queued validators (49%). 60 nodes have a single validator queued.

Scenarios for the **55,320 ETH** of user capital in the exiting minipools:

| scenario | ETH to queue | validators funded | express | standard | nodes funded | most to one node | share to top 6 nodes % |
|---|---|---|---|---|---|---|---|
| all returning user ETH goes to the queue | 55,320 | 1,975 | 1,314 | 661 | 194 | 249 | 46 |
| two thirds (rest burned by rETH redemptions) | 36,880 | 1,317 | 1,054 | 263 | 116 | 249 | 54 |
| one third | 18,440 | 658 | 527 | 131 | 44 | 249 | 73 |

Under the first scenario the queue is left with 132 entries, all standard-queue (132 standard entries unfunded) because the 4:1 rate drains the express queue first.

Top 10 beneficiaries if all returning ETH funds the queue:

| node | validators funded | queued now | megapool RPL staked | still runs minipools |
|---|---|---|---|---|
| 0x9A8dc6dcD9fDC7efAdbED3803bf3Cd208C91d7C1 | 249 | 249 | 0 | False |
| 0x8dEA24025cF3080FE46af8511c1Be871302B2d63 | 189 | 189 | 0 | False |
| 0x8AF2565bE72735484c1114a856B5C96735db1eD6 | 175 | 175 | 0 | False |
| 0xc0E7C12756954454937943316B2Ad99e4eBE11aC | 113 | 113 | 416,142 | True |
| 0xFbEd2f322c918363F6E663E00e923574027C5231 | 106 | 106 | 3,947 | False |
| 0x38362937B202Cb3e28cE71bABbc68dd265B9638c | 70 | 200 | 0 | False |
| 0xaEfb7da80eC25f4e7871A4bDC9Bd8e9Dba94d643 | 64 | 64 | 79,066 | False |
| 0x4f9DAFfa3Ab242EA906F6674953e42758f0597b9 | 56 | 56 | 0 | False |
| 0x7818614Ff330B1c5C0C00f10710412f48927D1c6 | 43 | 43 | 27,957 | False |
| 0x9C9E7e6EF247D80CE6e4dEd2a9911B4746543E28 | 41 | 41 | 80,664 | False |

## 9. RPIP-83: years to top up to 6 ETH from rewards alone

Megapool operator rewards per validator under UARS: own bond at the APR, plus node share (5%) and, if RPL is staked, voter share (9%) of the rewards on the borrowed ETH. Rewards retained to raise the bond from today's level to 6 ETH:

| gross staking APR | operator rewards | retained ETH per validator per year | validator-weighted years to 6 ETH | median years (nodes below 6) |
|---|---|---|---|---|
| 2.5% | no RPL (node share 5% only) | 0.14 | 14.60 | 14.81 |
| 2.5% | RPL staked (node 5% + voter 9%) | 0.20 | 9.96 | 10.10 |
| 3.0% | no RPL (node share 5% only) | 0.16 | 12.17 | 12.35 |
| 3.0% | RPL staked (node 5% + voter 9%) | 0.24 | 8.30 | 8.42 |
| 3.5% | no RPL (node share 5% only) | 0.19 | 10.43 | 10.58 |
| 3.5% | RPL staked (node 5% + voter 9%) | 0.28 | 7.11 | 7.22 |

111 of 112 active megapools are below 6 ETH per validator; total shortfall 4,272 ETH. At 3% gross and no RPL, a 4 ETH validator retains about 0.162 ETH a year, so the 2 ETH gap takes about 12 years; with RPL staked about 8 years. The RPIP's own 11 to 13 year figure is the no-RPL case.
