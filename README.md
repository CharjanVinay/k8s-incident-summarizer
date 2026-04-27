# K8s Incident Summarizer — AI-Powered RCA Tool

A lightweight Python tool that takes a Kubernetes alert payload and uses the **Anthropic Claude API** to generate a plain-English Root Cause Analysis (RCA) summary — instantly delivered to your terminal or Slack channel.

Built by a Platform & DevOps Engineer to reduce Mean Time To Resolution (MTTR) during production incidents on AKS clusters.

---

## What It Does

When a Kubernetes alert fires (pod crash loop, OOMKilled, node pressure, etc.), this tool:

1. Reads the alert payload (from Prometheus Alertmanager or a JSON file)
2. Sends it to Claude via the Anthropic API
3. Returns a structured plain-English RCA in seconds

**Example output:**

```
WHAT HAPPENED:
The pod credit-score-api-7d9f8b6c4-xk2pq in the scoring-engine namespace
has been restarting 5 times in the last 10 minutes with exit code 1.

LIKELY CAUSE:
The application is likely encountering an unhandled runtime error or
misconfigured environment variable causing it to crash on startup.
OOMKilled is false, so memory pressure is not the cause.

IMMEDIATE ACTION:
Run: kubectl logs credit-score-api-7d9f8b6c4-xk2pq -n scoring-engine --previous
to inspect the last crash logs and identify the exact error.

FOLLOW-UP:
Review recent config map or secret changes in the scoring-engine namespace
and add a startupProbe to prevent traffic during initialisation.
```

---

## Real-World Context

This tool was built to solve a real problem: during on-call incidents on a production AKS cluster serving financial workloads, the first 5-10 minutes are spent reading raw alert JSON and Kubernetes logs to understand *what happened*. This tool compresses that to under 10 seconds.

**Target reduction in MTTR: 30%+**

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| AI Model | Claude (Anthropic API) |
| Alert Source | Prometheus Alertmanager webhook / JSON file |
| Target Platform | Azure Kubernetes Service (AKS) |
| Zero dependencies | Uses only Python standard library |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/k8s-incident-summarizer.git
cd k8s-incident-summarizer
```

### 2. Get an Anthropic API key

Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key.

### 3. Set your API key

**Linux / Mac:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

### 4. Run with a sample alert

```bash
python automation.py --alert-file alert.json
```

---

## Usage

### From a JSON file
```bash
python automation.py --alert-file alert.json
```

### Piped from stdin (Alertmanager webhook)
```bash
cat alert.json | python automation.py
```

### Custom model
```bash
python automation.py --alert-file alert.json --model claude-haiku-4-5-20251001
```

---

## Alert Format

The tool accepts standard Prometheus Alertmanager webhook payloads. See `alert.json` for a working example.

```json
{
  "status": "firing",
  "commonLabels": {
    "alertname": "KubePodCrashLooping",
    "namespace": "scoring-engine",
    "pod": "credit-score-api-7d9f8b6c4-xk2pq",
    "severity": "critical"
  },
  "commonAnnotations": {
    "description": "Pod restarting 5 times / 10 minutes."
  }
}
```

---

## Project Structure

```
k8s-incident-summarizer/
├── automation.py      # Main script
├── alert.json         # Sample Kubernetes alert payload
├── README.md          # This file
└── .gitignore         # Keeps API keys out of git
```

---

## Roadmap

- [ ] Slack webhook integration — post RCA directly to on-call channel
- [ ] Prometheus Alertmanager webhook server mode
- [ ] Support for multiple alert types (NodeNotReady, PVCPending, HPA scaling)
- [ ] HTML report output
- [ ] Docker container for easy deployment

---

## Author

**Vinay Charjan** — Platform & DevOps Engineer  
Specializing in Azure Kubernetes Service (AKS), Terraform, SRE practices, and AI-assisted DevOps automation.

[LinkedIn](https://www.linkedin.com/in/vinaycharjan/) 

---

## License

MIT License — free to use, modify, and distribute.
