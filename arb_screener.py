#!/usr/bin/env python3
"""ParlayAPI arbitrage screener: find guaranteed-profit cross-book opportunities.

Hits ParlayAPI's pre-computed arbitrage endpoint every minute across MLB,
NBA, NFL, NHL, soccer, and UFC. Prints any arb above the configured
profit threshold to stdout, optionally posts to a Discord webhook.

Get a free API key at https://parlay-api.com/signup (1,000 reqs/month,
no credit card). Or upgrade to Pro for $99/mo + WebSocket for sub-second
edge alerts.

Usage:
    pip install -r requirements.txt
    PARLAY_API_KEY=your_key python arb_screener.py

Optional:
    PARLAY_API_KEY=your_key \\
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/... \\
    MIN_PROFIT_PCT=0.005 \\
    POLL_INTERVAL_SECONDS=60 \\
    SPORTS=baseball_mlb,basketball_nba,icehockey_nhl,americanfootball_nfl,mma_mixed_martial_arts,soccer_epl \\
    python arb_screener.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import httpx


BASE_URL = os.environ.get("PARLAY_API_URL", "https://parlay-api.com")
API_KEY = os.environ.get("PARLAY_API_KEY", "")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
MIN_PROFIT_PCT = float(os.environ.get("MIN_PROFIT_PCT", "0.005"))  # 0.5% default
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
SPORTS = [s.strip() for s in os.environ.get(
    "SPORTS",
    "baseball_mlb,basketball_nba,americanfootball_nfl,icehockey_nhl,"
    "mma_mixed_martial_arts,soccer_epl"
).split(",") if s.strip()]


def _fmt_arb(sport_key: str, arb: dict) -> str:
    """Render an arb opportunity as a human-readable line."""
    profit = float(arb.get("profit_pct", 0)) * 100
    home = arb.get("home_team", "?")
    away = arb.get("away_team", "?")
    legs = arb.get("legs", []) or arb.get("bets", [])
    leg_lines = []
    for leg in legs:
        book = leg.get("book") or leg.get("bookmaker", {}).get("title", "?")
        outcome = leg.get("outcome") or leg.get("name", "?")
        price = leg.get("price") or leg.get("american_odds", "?")
        stake_pct = float(leg.get("stake_pct", 0)) * 100 if leg.get("stake_pct") else None
        if stake_pct is not None:
            leg_lines.append(f"    {book}: {outcome} @ {price}  ({stake_pct:.1f}% stake)")
        else:
            leg_lines.append(f"    {book}: {outcome} @ {price}")
    leg_text = "\n".join(leg_lines)
    return (
        f"\n[{sport_key}] {away} @ {home}\n"
        f"  Profit: {profit:.2f}%\n"
        f"{leg_text}"
    )


async def _post_discord(client: httpx.AsyncClient, content: str):
    if not DISCORD_WEBHOOK:
        return
    try:
        await client.post(DISCORD_WEBHOOK, json={"content": content[:1900]})
    except Exception as e:
        print(f"  discord post failed: {e}", file=sys.stderr)


async def scan_sport(client: httpx.AsyncClient, sport_key: str) -> int:
    """Hit /v1/sports/{sport_key}/arbitrage. Print and return arb count."""
    try:
        r = await client.get(
            f"/v1/sports/{sport_key}/arbitrage",
            params={"min_profit": MIN_PROFIT_PCT},
        )
        if r.status_code == 401:
            print("Invalid PARLAY_API_KEY. Get one free at https://parlay-api.com/signup", file=sys.stderr)
            sys.exit(1)
        if r.status_code == 402:
            print("Out of credits. Upgrade at https://parlay-api.com/pricing", file=sys.stderr)
            return 0
        r.raise_for_status()
        arbs = r.json() or []
    except httpx.HTTPError as e:
        print(f"  {sport_key}: error {e}", file=sys.stderr)
        return 0
    if not arbs:
        return 0
    msgs = []
    for arb in arbs:
        msg = _fmt_arb(sport_key, arb)
        print(msg)
        msgs.append(msg)
    if msgs and DISCORD_WEBHOOK:
        await _post_discord(client, "\n".join(msgs))
    return len(arbs)


async def main_loop():
    if not API_KEY:
        print("ERROR: PARLAY_API_KEY env var required.", file=sys.stderr)
        print("Get a free key at https://parlay-api.com/signup", file=sys.stderr)
        sys.exit(1)
    print(f"ParlayAPI arb screener starting")
    print(f"  Sports: {', '.join(SPORTS)}")
    print(f"  Min profit: {MIN_PROFIT_PCT*100:.2f}%")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  Discord webhook: {'configured' if DISCORD_WEBHOOK else 'off'}")
    print()
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"X-API-Key": API_KEY, "User-Agent": "parlay-api-arb-starter/0.1"},
        timeout=15.0,
    ) as client:
        while True:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            tasks = [scan_sport(client, s) for s in SPORTS]
            results = await asyncio.gather(*tasks)
            total = sum(results)
            print(f"[{ts}] scanned {len(SPORTS)} sports, {total} arb(s) found")
            try:
                await asyncio.sleep(POLL_INTERVAL)
            except asyncio.CancelledError:
                return


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\ninterrupted")
