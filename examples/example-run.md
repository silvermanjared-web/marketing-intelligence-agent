# Example Run

This example shows the intended shape of a local marketing intelligence run using mock inputs. It is illustrative, not connected to live accounts, private inboxes, or confidential project data.

The point of this example is not to claim autonomous decision-making. The agent turns scattered signals into a short operator-reviewed brief, then recommends the next workflow to run.

## Command map

| Workflow | Command | Purpose |
|---|---|---|
| Interactive menu | `python hub.py` | Opens the local command menu |
| Briefing | `python hub.py briefing` | Runs the briefing agent and saves a local brief |
| Morning mode | `python hub.py mode morning` | Runs a configured sequence of briefing, scan, organization, and workspace actions |
| Health scan | `python hub.py scan` | Runs project/workspace health checks |
| Audit | `python hub.py audit` | Checks config presence, agent drift, log volume, and mode state |

## Example: briefing run

### Command

```bash
python hub.py briefing
```

### Sample console output

```text
  === MORNING BRIEFING ============================================
  [>>] [08:31:14] Starting agent: briefing_agent
  [OK] [08:31:16] Agent 'briefing_agent' completed in 2.1s
  Run completed in 2.1s
  [OK] [08:31:16] Briefing saved: briefing_latest.txt, briefing_20260619_0831.txt, Desktop
```

### Sample briefing output

```markdown
# Morning Marketing Intelligence Brief

## Executive Summary

Three items require attention today:

1. Paid search pacing is ahead of target in two priority campaigns.
2. Conversion tracking freshness should be checked before the next reporting cycle.
3. One project folder has stale exports that should be archived or refreshed.

## Priority Signals

| Priority | Signal | Why it matters | Suggested action |
|---|---|---|---|
| High | Search pacing above plan | Spend may exceed budget before next review | Check pacing and rebalance budget if needed |
| Medium | Conversion data freshness risk | Reporting may reflect stale performance | Confirm latest import and attribution status |
| Medium | Stale report exports | Operators may use outdated files | Refresh or archive before next readout |

## Recommended Next Step

Run a focused health scan before the executive readout:

```bash
python hub.py scan
```
```

## Example: mode run

### Command

```bash
python hub.py mode morning
```

### Sample console output

```text
  +==========================================================+
  |  MODE: MORNING                                          |
  |  Briefing, health scan, workspace prep                  |
  +==========================================================+
  State: briefing is recent, clutter: 42 files
  [INFO] [08:41:02] Mode 'morning' step 1: skip briefing -- ran within 30m
  [>>] [08:41:02] Mode 'morning' [2/4]: scan
  [OK] [08:41:04] Agent 'health_scanner' completed in 1.8s
  [>>] [08:41:04] Mode 'morning' [3/4]: organize
  [OK] [08:41:06] Agent 'file_organizer' completed in 1.9s

  ____________________________________________________________
  MODE COMPLETE: morning
  Completed: scan, organize
  Skipped:   briefing (ran recently)
  Duration:  4.0s
  ____________________________________________________________
```

## Example: audit run

### Command

```bash
python hub.py audit
```

### Sample console output

```text
  === SYSTEM AUDIT ================================================

  No issues found.

  System state:
    Agents: 4 (__init__, briefing_agent, file_organizer, health_scanner)
    Modes: 3 (morning, deep_work, cleanup)
    Log files: 6, archived briefings: 12
    Overlap check: 'all' delegates to 'mode morning' (no duplication)
    Clutter: 18 files (Desktop + Downloads)
    Disk: 64%
    Briefing recent: no
```

## What this demonstrates

The agent is designed to turn scattered operational signals into prioritized action. The useful pattern is orchestration plus review: modular agents produce a briefing, the hub checks state, redundant steps are skipped, and the operator decides what happens next.

## Notes

- This example uses mock data.
- Do not commit live email, campaign, account, credential, or client data.
- Real outputs should be reviewed before sharing externally.
- Local delivery behavior may vary by machine and configuration.
