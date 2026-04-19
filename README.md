# Marketing Intelligence Agent

A lightweight system for automating marketing intelligence workflows, including performance monitoring, risk detection, and executive reporting. Designed to reduce manual reporting overhead and improve decision speed across complex paid media portfolios.

## Problem

Performance marketing generates high volumes of fragmented data across channels, platforms, and tools. Most teams drown in dashboards and reports without synthesizing signals into decisions. This system closes that gap by automating the synthesis layer — turning raw data from multiple sources into a single decision-ready briefing.

## Architecture

```
hub.py (orchestrator)
├── briefing_agent      — morning intelligence synthesis
├── health_scanner      — project and campaign health checks
├── file_organizer      — report and asset organization
└── config/modes.json   — composable workflow definitions
```

The orchestrator dispatches to modular agents via dynamic import. Each agent exposes a `run()` interface and returns structured output. Workflows are composed from config — not hardcoded sequences.

### Core Concepts

- **Agents** are stateless modules with a single `run(*args) -> dict` interface
- **Modes** are config-driven workflow compositions (e.g., "morning" runs briefing -> scan -> organize)
- **State-aware execution** — the system checks machine state before each step and skips redundant work
- **Signal scoring** — email triage uses weighted pattern matching to surface what matters and suppress noise

## Capabilities

- **Morning Intelligence Briefing** — synthesizes email, calendar, and project data into a decision-ready report with confidence-scored triage
- **Health Scanner** — checks project repos for git hygiene, credential exposure, staleness, and dependency health
- **Smart Organizer** — categorizes and routes files by type with dry-run preview
- **Composable Modes** — define custom workflows in JSON that chain agents with conditional logic
- **Trend Memory** — tracks signals over time for pattern detection

## Stack

- Python 3.12+
- SQLite (local data layer)
- macOS automation (AppleScript for window management, app launching)
- Gmail API (read-only inbox stats)
- No cloud dependencies, no databases, no daemons

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

## Design Principles

- **Diagnostic first** — measure before acting
- **Signal over noise** — score and filter, don't just list
- **Config over code** — workflows are JSON, not Python
- **State-aware** — skip what's already done
- **Anti-drift** — `audit` command detects system bloat

## Why This Exists

This reflects how I approach marketing operations: structured systems, repeatable workflows, and a relentless focus on signal over noise. The same diagnostic-first, systems-driven methodology I apply to campaign architecture and team operations.
