#!/usr/bin/env python3
"""AI-Powered Kubernetes Incident Summarizer.

Reads a Kubernetes alert payload and sends it to Claude via the Anthropic API,
then prints a plain-English root cause summary.

Usage:
  python automation.py --alert-file alert.json
  cat alert.json | python automation.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request

# ── CORRECT API ENDPOINT (v1/messages, NOT v1/complete) ──────────────────────
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# ── CORRECT MODEL NAME ────────────────────────────────────────────────────────
# claude-haiku-4-5-20251001 = fastest and cheapest, perfect for this use case
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def build_prompt(alert_text: str) -> str:
    """Build the prompt we send to Claude."""
    return textwrap.dedent(
        f"""
        You are an expert SRE incident analyst.
        Given a Kubernetes alert payload, write a concise root cause analysis summary.
        Keep it in plain English for an on-call engineer.

        Structure your response exactly like this:

        WHAT HAPPENED:
        (one or two sentences)

        LIKELY CAUSE:
        (one or two sentences)

        IMMEDIATE ACTION:
        (one clear action to take right now)

        FOLLOW-UP:
        (one next step after the immediate fix)

        Kubernetes alert payload:
        {alert_text}
        """
    ).strip()


def call_claude(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call the Anthropic API and return Claude's response text."""

    # ── Read API key from environment variable ────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "\n[ERROR] ANTHROPIC_API_KEY environment variable is not set.\n"
            "Set it in your terminal before running:\n"
            "  Windows CMD:   set ANTHROPIC_API_KEY=your-key-here\n"
            "  Windows PS:    $env:ANTHROPIC_API_KEY='your-key-here'\n"
        )

    # ── CORRECT request body format for /v1/messages ─────────────────────────
    payload = {
        "model": model,
        "max_tokens": 512,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")

    # ── CORRECT headers for current API ──────────────────────────────────────
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,                    # lowercase x-api-key
            "anthropic-version": "2023-06-01",        # required version header
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"Claude API error {exc.code}: {exc.reason}\nDetail: {message}"
        )
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error calling Claude API: {exc}")

    # ── CORRECT response parsing for /v1/messages ─────────────────────────────
    # Response shape: { "content": [ { "type": "text", "text": "..." } ] }
    result = json.loads(response_text)

    try:
        return result["content"][0]["text"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected API response format:\n{result}")


def load_alert_text(alert_file: str | None) -> str:
    """Load alert JSON from a file or stdin."""
    if alert_file:
        try:
            with open(alert_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise RuntimeError(f"Alert file not found: {alert_file}")

    if sys.stdin.isatty():
        raise RuntimeError(
            "No alert payload provided.\n"
            "Usage: python automation.py --alert-file alert.json"
        )

    return sys.stdin.read().strip()


def normalize_alert(alert_text: str) -> str:
    """Pretty-print JSON if valid, otherwise pass through as plain text."""
    if not alert_text:
        raise RuntimeError("Alert payload is empty.")
    try:
        parsed = json.loads(alert_text)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return alert_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Kubernetes alert into a plain-English RCA summary using Claude."
    )
    parser.add_argument(
        "--alert-file",
        help="Path to a Kubernetes alert JSON file.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("Loading alert payload...")
    alert_text = load_alert_text(args.alert_file)
    normalized = normalize_alert(alert_text)

    print("Sending to Claude for analysis...")
    print("-" * 50)

    try:
        summary = call_claude(normalized, model=args.model)
    except RuntimeError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    print(summary)
    print("-" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
