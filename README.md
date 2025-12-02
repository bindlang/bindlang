# bindlang ⦿╯

**Deferred Semantic Binding for Python**

---

## Overview

bindlang is a Python library built on a philosophy called deferred semantic binding. Instead of resolving meaning immediately, a symbol stays latent until runtime context (who, when, where, system state) satisfies its conditions. Think of it as a contract that waits for the right moment to activate.

Each symbol carries its own gate conditions. The system only marks it as bound when all gates pass. This keeps semantic contracts portable, maintains immutability for serialization, and records every binding attempt for audit and dependency tracing. For a deeper explanation, see [Foundation](docs/theory/FOUNDATION.md).

### Potential Use Cases

- **Approval workflows** - Approval chains, policy enforcement, audit trails
- **Multi-agent coordination** - Coordinate agents through dependency tracking and quorum patterns
- **LLM context management** - Compress conversation state, expand on demand
- **Narrative compression** - Store latent symbols, bind when needed

---

## Installation

```bash
pip install bindlang
```

**Requirements**: Python 3.10+, Pydantic 2.0+

---

## Documentation

- **[Reference](docs/reference/index.md)** - API reference, quickstart and usage patterns
- **[Architecture](docs/ARCHITECTURE.md)** - Core components and design decisions
- **[Foundation](docs/theory/FOUNDATION.md)** - Theoretical foundation and design principles

---

## License

MIT
