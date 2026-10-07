# Saturn 2 decision data: Rocket Pool validator-set snapshot and analysis

Read `REPORT.md` for findings. `report/numbers.md` holds every generated table; `report/figures/` the charts.

| File | What it does |
|---|---|
| `collect_snapshot_multicall.py` | Reads every minipool and megapool validator, every megapool, and node RPL/ETH figures at a pinned block through Multicall3 (public RPCs, rotated on rate limits). Writes `data/minipools.csv`, `data/megapool_validators.csv`, `data/megapools.csv`, `data/nodes.csv`, `data/meta.json`. |
| `collect_history.py` | Weekly rETH supply, exchange rate, deposit pool, queue lengths, megapool and minipool counts from an archive RPC. Writes `data/history.csv`. |
| `collect_beacon.py` | Current beacon-chain status, balance and activation epoch for every pubkey, from a public beacon API. Writes `data/beacon_validators.csv`. |
| `analyze.py` | Supply/demand, composition, RPIP-83 bond arithmetic, exiting minipools, RPIP-71 phase 1 ordering and phase 2 tournament simulations, activation months. Writes `report/numbers.md` and `report/figures/*.png`. |

```
pip install web3 pandas matplotlib
python3 collect_snapshot_multicall.py --outdir data --block 26118341 --rpc https://eth.drpc.org
python3 collect_history.py --start 2025-10-01 --out data/history.csv
python3 collect_beacon.py --datadir data --beacon https://lodestar-mainnet.chainsafe.io
python3 analyze.py --datadir data --outdir report --runs 200
```

Snapshot in this repository: block 26,118,341 (4 Oct 2026), beacon head slot 15,357,280. Only
`eth_call` and beacon GET/POST reads are used; no keys, no transactions. Code MIT; data and figures CC BY 4.0.
