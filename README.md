# nanrunner-hermes

Dedicated, disposable **GitHub Actions** runner for the NaNLMind HERMES plugin.

- The job runs only on manual **Actions → Test HERMES + Gemma (Ollama) → Run workflow**.
- The only external model credential is the repository's **Actions secret named `OLLAMA`**. Do **not** paste its value into any source file, YAML, README, commit, issue, or log.
- The job does not require Koyeb, NANNET administrative tokens, other GitHub repository secrets, or a privileged PAT.
- It checks out the HERMES plugin from a **specific commit** in `shemshallah/NaNLMind_HERMES`, installs a pinned Hermes Agent version, validates the plugin, and makes **one bounded authenticated Gemma cloud call** with Ollama.
- Installing Hermes and plugin-testing never receives `OLLAMA`. The secret is made available **only in the final cloud inference step**.
- A successful inference proves that the model answered. It **does not establish that Ollama usage was free**, since balances/credits are account-specific. Verify the Ollama usage and billing dashboard.
- This repository contains no key material and no model binaries. GitHub-hosted runners are ephemeral.

## Setup

1. Open [repository secrets](https://github.com/shemshallah/nanrunner-hermes/settings/secrets/actions) and choose **New repository secret**.
2. Set the **Name** to `OLLAMA` and paste your Ollama API key only into the **Secret** field. Save.
3. Open [Actions](https://github.com/shemshallah/nanrunner-hermes/actions), select **Test HERMES + Gemma (Ollama)** and choose **Run workflow**.

The workflow deliberately fails before any cloud request if the secret is missing.

## Boundaries

This is an integration smoke test, **not** HERMES's final production NANNET/NaNROUTER lease issuer. The HERMES native NaN16DE guest remains separate from host HTTPS and credential storage. No model training, NANNET live traffic, or Koyeb deployment occurs in this job.

**Security:** A key pasted into a conversation should be replaced with a fresh key before use.
