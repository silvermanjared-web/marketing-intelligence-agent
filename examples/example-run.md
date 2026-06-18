# Example Run

This example shows the intended shape of a local marketing intelligence run using mock inputs. It is illustrative, not connected to live accounts or private data.

## Command

```bash
python hub.py briefing
```

## Sample console output

```text
Marketing Intelligence Agent
Mode: briefing
Run ID: demo-2026-06-18-briefing
Sources checked: 4
Signals detected: 7
Priority items: 3
Status: complete
```

## Sample briefing output

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

## What this demonstrates

The agent is designed to turn scattered operational signals into a short, prioritized briefing. The output should help an operator decide what needs attention, what can wait, and what follow-up workflow should run next.

## Notes

- This example uses mock data.
- Do not commit live email, campaign, account, credential, or client data.
- Real outputs should be reviewed before sharing externally.
