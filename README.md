# Weight Lens

[Open the dashboard](https://zhangbobo123.github.io/auren-weight-lens/) or inspect the [captured calls](docs/evidence.json).

An independent, read-only integration of AUREN's public risk API. It compares two BTC/ETH allocations and computes the difference in the returned metrics without pretending that a more evenly weighted portfolio must have less market risk. Both portfolios are synthetic, not recommendations.

Run with Python 3.9+ and network access (standard library only):

```sh
python lens.py --btc 80 50 --out docs
```

Open `docs/index.html` offline afterwards. Each run makes two HTTPS POST requests to `/risk`. The evidence file preserves each exact input, result and receipt time. Missing metrics display as unavailable rather than zero; live numbers may change. No credentials or wallet required.
