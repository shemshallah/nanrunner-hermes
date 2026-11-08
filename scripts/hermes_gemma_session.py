#!/usr/bin/env python3
"""Real Hermes Agent -> Ollama Cloud Gemma two-turn session verification.

Never print upstream response bodies, model output, keys, or subprocess stderr.
The only credential is OLLAMA_API_KEY supplied to the isolated Actions job.
"""
from __future__ import annotations

import os
import re
import secrets
import subprocess
import sys
import uuid

MODEL = "gemma4:31b"
TIMEOUT_SECONDS = 240
ADJECTIVES = ("amber", "cobalt", "cedar", "violet", "silver", "gentle")
NOUNS = ("heron", "orbit", "lantern", "river", "comet", "meadow")


def choose_phrase() -> str:
    return secrets.choice(ADJECTIVES) + " " + secrets.choice(NOUNS)


def valid_key(env: dict[str, str]) -> bool:
    key = env.get("OLLAMA_API_KEY", "")
    return bool(key and len(key) <= 1024 and not any(c in key for c in "\r\n\x00"))


def call_hermes(args: list[str], env: dict[str, str]) -> str:
    try:
        p = subprocess.run(["hermes", "chat", *args], capture_output=True,
                           text=True, env=env, timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("Hermes subprocess unavailable or timed out") from None
    if p.returncode != 0:
        raise RuntimeError(f"Hermes subprocess exited {p.returncode}")
    if not p.stdout.strip():
        raise RuntimeError("Hermes returned no model output")
    return p.stdout


def recalled(text: str, phrase: str) -> bool:
    words = re.findall(r"[a-z]+", re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text).casefold())
    target = phrase.split()
    return any(words[i:i + len(target)] == target for i in range(len(words) - len(target) + 1))


def main() -> int:
    env = dict(os.environ)
    if not valid_key(env):
        print("ERROR: GitHub Actions OLLAMA secret not available to Hermes", file=sys.stderr)
        return 2

    env["HERMES_GATEWAY_NO_SUPERVISE"] = "1"
    title = "nanrunner-gemma-" + uuid.uuid4().hex[:16]
    phrase = choose_phrase()
    prompt = "Remember this exact two-word phrase for the next turn: " + phrase + ". Reply only ACK."
    followup = "What exact two-word phrase did I give you in my previous message? Reply with only those two words."

    try:
        call_hermes(["--safe-mode", "--provider", "ollama-cloud", "--model", MODEL,
                     "--max-turns", "1", "-c", title, "--create-if-missing",
                     "-q", prompt], env)
        # No model/provider override on resume: proves the saved session route.
        answer = call_hermes(["--resume", title, "-q", followup], env)
    except RuntimeError as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1

    if not recalled(answer, phrase):
        print("ERROR: Gemma failed to recall turn-one phrase in resumed Hermes session", file=sys.stderr)
        return 1

    print("PASS: Two Hermes turns used Ollama Cloud Gemma")
    print("PASS: Hermes resumed the same session with preserved context")
    print("PASS: Gemma recalled private turn-one test phrase")
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fp:
            fp.write("### Hermes -> Ollama Cloud Gemma: PASS\n\n")
            fp.write("Persisted session resumed; turn-two response recalled turn-one phrase.\n")
            fp.write("No model content, API key or provider error body was logged.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
