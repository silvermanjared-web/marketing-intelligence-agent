# Governance

The agent may observe broadly inside configured public-safe inputs, but it may mutate only through named capabilities with declared boundaries.

Principles:

- capability discovery before execution;
- read and write effects are explicit;
- confirmation for consequential writes;
- receipts after execution;
- no credential or private-data persistence in the repository;
- human review for recommendations that move budget, change targeting, or affect external systems;
- bounded cleanup after implementation, then stop.