# Marketing Intelligence Agent

A lightweight system for automating marketing intelligence workflows, including performance monitoring, risk detection, and executive reporting. Designed to reduce manual reporting overhead and improve decision speed across complex paid media portfolios.

## Problem

Performance marketing generates high volumes of fragmented data across channels, platforms, and tools. Most teams rely on dashboards and reports but lack consistent synthesis into actionable decisions. This system addresses that gap by automating the synthesis layer — turning raw inputs into a single, decision-ready briefing.

## Architecture

```
hub.py (orchestrator)
├── briefing_agent      — morning intelligence synthesis
├── health_scanner      — project and campaign health checks
├── file_organizer      — report and asset organization
└── config/modes.json   — composable workflow definitions
```

The orchestrator dispatches modular agents via dynamic import. Each agent exposes a run() interface and returns structured output. Workflows are defined through configuration rather than hardcoded sequences.

Core Concepts

* Modular agents with a consistent run(*args) -> dict interface
* Config-driven workflows (“modes”) for repeatable execution
* State-aware execution to avoid redundant work
* Signal scoring to prioritize high-value inputs and suppress noise

Capabilities

* Intelligence Briefing — synthesizes inputs into a decision-ready report with scored prioritization
* Health Scanner — evaluates project hygiene, credential exposure risk, and system drift
* Smart Organizer — categorizes and routes files with dry-run preview
* Composable Workflows — chain agents through configurable modes
* Trend Memory — tracks signals over time for pattern detection

Stack

Python 3.12+
SQLite (local state)
macOS automation (AppleScript)
Gmail API (read-only)

No cloud dependencies. Fully local execution.

## Usage

```bash
# Interactive menu
python hub.py

# Direct commands
python hub.py briefing          # Morning intelligence report
python hub.py mode morning      # Full coordinated boot sequence
python hub.py scan              # Project health check
python hub.py mode deep_work    # Launch focused workspace
python hub.py audit             # System health audit
```

## Configuration

Copy the example configs and customize:

```bash
cp config/projects.example.json config/projects.json
cp config/modes.example.json config/modes.json
```

Design Principles

* Diagnostic first — measure before acting
* Signal over noise — prioritize what matters
* Config over code — workflows are defined, not hardcoded
* State-aware — avoid redundant execution
* Anti-drift — built-in system auditing

Why This Exists

This project reflects how I approach marketing operations: structured systems, repeatable workflows, and a focus on signal over noise. The same principles applied to campaign architecture, reporting, and team operations at scale.
