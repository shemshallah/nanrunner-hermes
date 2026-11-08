#!/usr/bin/env python3
"""Single bounded Gemma cloud smoke call for the dedicated nanrunner-hermes.

ONLY read OLLAMA from GitHub Actions secret-injected environment. Never log
credentials, request headers, provider error bodies, or generated content.
Ollama's response does not reveal whether account-level credits covered usage.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request


URL = "https://ollama.com/api/chat"
MODEL = "gemma4:31b-cloud"
MAX_OUTPUT_TOKENS = 48
MAX_RESPONSE_BYTES = 65536


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main() -> int:
    key = os.environ.get("OLLAMA", "")
    if not key or len(key) > 1024 or any(c in key for c in ("\n", "\r", "\x00")):
        print("ERROR: Add repository Actions secret OLLAMA; no request made.", file=sys.stderr)
        return 2

    body = json.dumps({
        "model": MODEL,
        "stream": False,
        "think": False,
        "messages": [{"role": "user", "content": "Answer in one word: READY"}],
        "options": {"num_predict": MAX_OUTPUT_TOKENS, "temperature": 0},
    }, separators=(",", ":")).encode("utf-8")

    request = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cache-Control": "no-store",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(
        NoRedirects, urllib.request.HTTPSHandler(context=ssl.create_default_context())
    )
    try:
        with opener.open(request, timeout=90) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Intentionally never read or print provider error body.
        code = exc.code
        if code in (401, 403):
            msg = "credential rejected or model access denied"
        elif code in (402, 429):
            msg = "quota/rate limit or credit restriction"
        elif code == 404:
            msg = "Gemma cloud model or route not found"
        elif code in (301, 302, 303, 307, 308):
            msg = "redirect refused to avoid forwarding the bearer"
        else:
            msg = "upstream request failed"
        print(f"ERROR: Ollama HTTP {code}: {msg}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError, TimeoutError):
        print("ERROR: Ollama API transport unavailable", file=sys.stderr)
        return 1

    if len(raw) > MAX_RESPONSE_BYTES:
        print("ERROR: Unexpectedly large Ollama response", file=sys.stderr)
        return 1
    try:
        data = json.loads(raw)
        answer = data["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("empty completion")
        prompt = data.get("prompt_eval_count")
        completion = data.get("eval_count")
        if prompt is not None and (not isinstance(prompt, int) or prompt < 0):
            raise ValueError("invalid prompt count")
        if completion is not None and (not isinstance(completion, int) or completion < 0):
            raise ValueError("invalid completion count")
    except (ValueError, KeyError, TypeError) as exc:
        print("ERROR: Ollama response failed completion validation", file=sys.stderr)
        return 1

    print("PASS: Ollama authenticated Gemma cloud completion")
    print("Model: " + MODEL)
    print("Output length: " + str(len(answer)))
    print("Prompt tokens: " + str(prompt) if prompt is not None else "Prompt tokens: not reported")
    print("Output tokens: " + str(completion) if completion is not None else "Output tokens: not reported")
    print("Free usage vs billing: NOT proven by this call; check Ollama account usage.")
    # GitHub summary intentionally contains no model-generated content or secrets.
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("### Ollama Gemma cloud: PASS\n\n")
            stream.write("Authenticated single request to `gemma4:31b-cloud` succeeded.\n\n")
            stream.write("This response **does not prove free-tier eligibility or credit balance**.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
