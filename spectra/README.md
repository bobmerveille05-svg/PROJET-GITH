# Spectra

**Intent-driven development orchestration system**

Spectra is a CLI tool that transforms how development teams capture, track, and evolve system specifications. It provides an intent graph to manage dependencies, adaptive ceremony levels based on change risk, constitutional rule enforcement, and complete lifecycle management.

## Features

- 🎯 **Intent Graph**: Network of specs with dependency tracking and impact analysis
- 🎭 **Adaptive Ceremony**: Dynamic workflow based on change risk and complexity
- ⚖️ **Constitution**: Policy engine with customizable rule profiles
- 🔄 **Lifecycle Management**: State machine for spec progression with gates
- 🚀 **Fast-track Fixes**: Streamlined workflow for patch-level changes

## Installation

### From Source

```bash
cd spectra
pip install -e ".[dev]"
```

## Quick Start

### 1. Initialize a Spectra Project

```bash
spectra init
```

This creates a `.spectra/` directory with the database, configuration, and default constitution.

### 2. Create Your First Spec

```bash
spectra spec new user-authentication
```

Edit the generated spec file to define your intent, acceptance criteria, and structure.

### 3. Check Ceremony Level

```bash
spectra ceremony check user-authentication
```

Spectra will suggest the appropriate ceremony level based on complexity and risk.

### 4. Promote Through Lifecycle

```bash
spectra spec promote user-authentication
```

Move the spec through DRAFT → SPECIFIED → IMPLEMENTING → VALIDATING → COMPLETE.

### 5. View Dependency Tree

```bash
spectra spec tree
```

See the full intent graph and how specs relate to each other.

## Core Concepts

### Intent Graph
Specs are organized as a directed graph with typed edges:
- **DEPENDS_ON**: Implementation order
- **REFINES**: Elaboration relationships
- **CONFLICTS_WITH**: Mutually exclusive specs
- **ENABLES**: Unlocks new capabilities

### Ceremony Levels
Dynamic workflow based on change category:
- **EXPLORE** (0): Free-form ideation
- **SKETCH** (1): Basic intent defined
- **DRAFT** (2): Structure + initial tests
- **SPECIFIED** (3): Complete spec + review
- **VALIDATED** (4): CI passing + docs
- **LOCKED** (5): Formal approval required

### Constitution Profiles
Three built-in governance models:
- **Strict**: Everything required, no shortcuts
- **Balanced**: Reasonable defaults for most teams
- **Rapid**: Minimal ceremony, fast iteration

### Lifecycle States
- **DRAFT**: Initial creation
- **SPECIFIED**: Ready for implementation
- **IMPLEMENTING**: Work in progress
- **VALIDATING**: Testing and review
- **COMPLETE**: Done and deployed
- **ARCHIVED**: Historical record

## CLI Reference

### Project Management
- `spectra init [path] [--profile]` - Initialize a new project
- `spectra fix <id|name>` - Fast-track a patch fix

### Spec Commands
- `spectra spec new <name>` - Create a new spec
- `spectra spec show <id|name>` - Display spec details
- `spectra spec list [--state] [--level]` - List all specs
- `spectra spec edit <id|name>` - Edit spec in $EDITOR
- `spectra spec link <src> <tgt> --type <T>` - Create graph edge
- `spectra spec unlink <src> <tgt>` - Remove graph edge
- `spectra spec tree [root]` - Show dependency tree
- `spectra spec impact <id|name>` - Impact analysis
- `spectra spec promote <id|name>` - Advance lifecycle
- `spectra spec demote <id|name> --reason` - Revert lifecycle
- `spectra spec status <id|name>` - Lifecycle + ceremony status
- `spectra spec history <id|name>` - State transition log

### Ceremony Commands
- `spectra ceremony check <id|name>` - Run ceremony checks
- `spectra ceremony suggest <id|name>` - Suggest appropriate level
- `spectra ceremony set <id|name> <level>` - Override ceremony level
- `spectra ceremony report` - Project-wide ceremony status

### Constitution Commands
- `spectra const init [profile]` - Initialize constitution
- `spectra const show` - Display active rules
- `spectra const enforce [id|name]` - Check spec against rules
- `spectra const validate` - Validate constitution syntax
- `spectra const profiles` - List available profiles

## Architecture

Spectra is built with a modular architecture:

```
spectra/
├── core/           # Config, database, events, exceptions
├── intent_graph/   # Graph models, parser, query engine
├── ceremony/       # Adaptive workflow and gates
├── constitution/   # Policy engine and profiles
├── lifecycle/      # State machine and promotion logic
├── cli/            # Typer-based command interface
└── schemas/        # YAML validation schemas
```

All modules communicate through an event bus for loose coupling.

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
ruff check spectra/

# Type checking
mypy spectra/

# Format code
ruff format spectra/
```

## License

MIT License - See LICENSE file for details
