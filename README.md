# parlay-api-arb-starter

A 130-line Python script that uses [ParlayAPI](https://parlay-api.com) to find live cross-book arbitrage opportunities every minute and (optionally) post them to a Discord webhook.

Fork it, change the sports list and profit threshold, run it on your laptop or a $5 VPS. That's it.

## What is arbitrage?

When two sportsbooks disagree enough on the price of a market that you can stake a fraction of your bankroll on each outcome and profit no matter what happens. ParlayAPI pre-computes these across 21+ books in real time so you don't need to do the math yourself.

## Requirements

- Python 3.10+
- A ParlayAPI key (free tier works for this; get one at https://parlay-api.com/signup)
- (Optional) A Discord webhook URL if you want push notifications

## Install

```bash
git clone https://github.com/JacobiusMakes/parlay-api-arb-starter.git
cd parlay-api-arb-starter
pip install -r requirements.txt
```

## Run

```bash
PARLAY_API_KEY=your_key python arb_screener.py
```

You'll see output like:

```
ParlayAPI arb screener starting
  Sports: baseball_mlb, basketball_nba, americanfootball_nfl, icehockey_nhl, mma_mixed_martial_arts, soccer_epl
  Min profit: 0.50%
  Poll interval: 60s
  Discord webhook: off

[2026-05-01T19:30:00Z] scanned 6 sports, 0 arb(s) found

[baseball_mlb] Boston Red Sox @ Houston Astros
  Profit: 1.24%
    DraftKings: Boston Red Sox @ +135  (42.6% stake)
    FanDuel: Houston Astros @ -125  (57.4% stake)

[2026-05-01T19:31:00Z] scanned 6 sports, 1 arb(s) found
```

## Configuration

All via environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PARLAY_API_KEY` | (required) | Get free at https://parlay-api.com/signup |
| `DISCORD_WEBHOOK_URL` | (off) | If set, every arb is also posted to Discord |
| `MIN_PROFIT_PCT` | `0.005` (0.5%) | Minimum profit threshold. 0.005 = 0.5% per stake. |
| `POLL_INTERVAL_SECONDS` | `60` | How often to re-scan |
| `SPORTS` | MLB, NBA, NFL, NHL, MMA, EPL | Comma-separated sport_keys |
| `PARLAY_API_URL` | `https://parlay-api.com` | Override for staging/testing |

Example with all flags:

```bash
PARLAY_API_KEY=your_key \
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc \
MIN_PROFIT_PCT=0.01 \
POLL_INTERVAL_SECONDS=30 \
SPORTS=baseball_mlb,basketball_nba \
python arb_screener.py
```

## Run on a VPS / cron

Drop it in any Python-running container or VPS. To run continuously with auto-restart, use `systemd`, `pm2`, or:

```bash
while true; do
  PARLAY_API_KEY=your_key python arb_screener.py
  sleep 5
done
```

## Discord webhook setup

1. In your Discord server, **Server Settings → Integrations → Webhooks → New Webhook**
2. Pick the channel + copy the URL
3. Set `DISCORD_WEBHOOK_URL=...` and re-run

## Free tier limits

The free tier of ParlayAPI gives you 1,000 credits/month, no card required. Each scan = 1 credit per sport. So:

- 6 sports × 1 credit × 60-second poll = 6 credits/minute = 8,640/day
- That'll run through your free tier in ~3 hours

If you want to run continuously, upgrade to a paid tier; current prices and credit sizes are on the [pricing page](https://parlay-api.com/pricing). WebSocket streaming (edge alerts in real time, no polling) is available on Business tier and up.

## More features to try

The starter is intentionally minimal. Once you have it running, look at the [ParlayAPI docs](https://parlay-api.com/docs) for:

- `/v1/sports/{sport_key}/ev`: pre-computed +EV bets vs no-vig consensus
- `/v1/sports/{sport_key}/compare`: side-by-side line comparison
- `/v1/prediction-markets/{sport_key}`: Kalshi + Polymarket arbitrage vs sportsbooks
- `/v1/historical/sports/{sport_key}/odds`: backtesting data (1.15M+ rows back to 2005)
- WebSocket: `wss://parlay-api.com/ws/odds/{sport_key}` for sub-second updates (Business tier and up)

Or hook ParlayAPI directly into Claude / Cursor / Continue / Devin via the [official MCP server](https://github.com/JacobiusMakes/parlay-api-mcp): `pip install parlayapi-mcp`, or use the hosted endpoint with no install: `POST https://parlay-api.com/mcp/http`.

## Disclaimers

- This code finds opportunities; it does not place bets. Connecting to a sportsbook API and placing real bets carries legal, regulatory, and financial risk.
- Arbitrage windows close fast. By the time you see one, it may already be gone. Real arb operators run sub-second WebSocket pipelines (Business tier and up).
- Do not bet money you cannot afford to lose. Sports betting is gambling.

## License

MIT. Fork, modify, ship.

## Get a free API key

https://parlay-api.com/signup

---

Part of the [ParlayAPI](https://parlay-api.com) ecosystem: a real-time sports odds API with a free tier of 1,000 credits per month, no card required. Explore all the tools at [github.com/JacobiusMakes](https://github.com/JacobiusMakes).
