# AI Operating System Reference

This repository implements the public portfolio's shared AI operating-system pattern in a growth-intelligence domain.

The canonical reference lives in [Growth Architecture OS](https://github.com/silvermanjared-web/growth-architecture-os/tree/main/04-ai-systems/ai-operating-system-reference).

Local mapping:

- **context** → configured projects, modes, and operational inputs;
- **capabilities** → `src/core/capabilities.py`;
- **routing** → hub orchestration and named agent dispatch;
- **authority** → explicit read/write effects and confirmation;
- **execution** → agents and bounded file operations;
- **evidence** → structured receipts plus existing logs.

MCP-compatible clients can expose these same capability contracts as tools without changing the underlying authority model.