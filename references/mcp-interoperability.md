# MCP and Client Interoperability

The capability registry is transport-neutral.

A client should discover the registry, expose admitted capabilities as its own tools where appropriate, preserve the `effect` and `requires_confirmation` fields, invoke the capability, and return the receipt.

MCP is useful as a transport and discovery protocol. It does not replace the repository's authority contract.