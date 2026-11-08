# nanrunner-hermes

Dedicated, disposable **GitHub Actions** runner for the NaNLMind HERMES plugin.

- Every commit runs a **credential-free** Linux Hermes/plugin admission check. The **only step that reads the Ollama key** runs when manually selected under **Actions → Test HERMES + Gemma (Ollama) → Run workflow**.
- The only external model credential is the repository's **Actions secret named `OLLAMA`**. Do **not** paste its value into any source file, YAML, README, commit, issue, or log.
- The job does not require Koyeb, NANNET administrative tokens, other GitHub repository secrets, or a privileged PAT.
- It checks out the HERMES plugin from a **specific commit** in `shemshallah/NaNLMind_HERMES`, restores a pinned pre-installed Hermes Agent runtime from a repository Release or cache, validates the plugin, and makes **one bounded authenticated Gemma cloud call** with Ollama.
- Installing Hermes and plugin-testing never receives `OLLAMA`. The secret is made available **only in the final cloud inference step**.
- A successful inference proves that the model answered. It **does not establish that Ollama usage was free**, since balances/credits are account-specific. Verify the Ollama usage and billing dashboard.
- This repository contains no key material or model weights. GitHub-hosted runners are ephemeral, but the preinstalled Hermes executable and Python runtime are persisted in a versioned GitHub Release and Actions cache (not as huge committed Git blobs).

## Setup

1. Open [repository secrets](https://github.com/shemshallah/nanrunner-hermes/settings/secrets/actions) and choose **New repository secret**.
2. Set the **Name** to `OLLAMA` and paste your Ollama API key only into the **Secret** field. Save.
3. Open [Actions](https://github.com/shemshallah/nanrunner-hermes/actions), select **Test HERMES + Gemma (Ollama)** and choose **Run workflow**.

A manually triggered cloud test fails before sending a request if the secret is missing. The ordinary push test does not load the secret at all.

## Boundaries

This is an integration smoke test, **not** HERMES's final production NANNET/NaNROUTER lease issuer. The HERMES native NaN16DE guest remains separate from host HTTPS and credential storage. No model training, NANNET live traffic, or Koyeb deployment occurs in this job.

**Security:** A key pasted into a conversation should be replaced with a fresh key before use.

## Preinstalled runtime

The credential-free `Publish pre-installed Hermes runtime (pinned)` workflow packages a Hermes Agent install at upstream commit `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19` for Ubuntu 24.04 x86-64. Archive and SHA-256 manifest live in this repo's [Releases](https://github.com/shemshallah/nanrunner-hermes/releases).

Every job now attempts **Actions cache → Release archive → pinned upstream bootstrap**. The bootstrap is for the first run before the release exists. The archive includes `~/.hermes` and `~/.local/bin/hermes`, excluding config, credentials, logs, history, and caches. Restored bytes must pass SHA-256 and pinned-commit/CLI checks. No `OLLAMA` secret is available during bundling or cache save. GitHub-hosted runners remain disposable; this restores an already-installed runtime instead of keeping a machine alive.

To update Hermes, change the pinned commit, Release tag and cache key together, then rebuild a new immutable release.

**Verified on GitHub Actions:** [fresh, uncached Release restore](https://github.com/shemshallah/nanrunner-hermes/actions/runs/42455579393) completed successfully in **19 seconds** (2026-11-07 Pacific). Subsequent admission runs should prefer the repository cache, with the Release as durable fallback.

## Gemini-class model bridge: Hermes -> Gemma on Ollama Cloud

The live session test invokes the **actual installed Hermes CLI** with `--provider ollama-cloud --model gemma4:31b` and the repository secret `OLLAMA` injected only into the cloud job as `OLLAMA_API_KEY`. The test opens a named Hermes session, supplies a random two-word phrase in turn one, **resumes the same session**, and asks Gemma to recall it in turn two without restating the phrase. It fails closed if there is no valid response, or if context is lost. The direct Ollama API smoke test also runs. This proves a Hermes-to-Gemma conversation, not just a direct REST call.

Run manually from **Actions -> Test HERMES + Gemma (Ollama) -> Run workflow**. For a local conversation with an injected provider key, run `hermes chat --safe-mode --provider ollama-cloud --model gemma4:31b -c gemma-session --create-if-missing`, then `hermes chat --resume gemma-session`. GitHub-hosted jobs are ephemeral; session history is retained only within the job, not automatically shared between jobs or mapped into BS0:0. No model replies or provider diagnostics are written to public logs.
