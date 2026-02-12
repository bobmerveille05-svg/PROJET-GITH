# Spectra Architecture

## Overview

Spectra is an intent-driven development orchestration system built with a modular, event-driven architecture. The system is designed around four core innovations that work together through a central event bus.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                    (Typer + Rich)                            │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────┬──────────────┬──────────────┐
             │              │              │              │
    ┌────────▼────────┐    │    ┌─────────▼────────┐    │
    │  Intent Graph   │    │    │    Ceremony      │    │
    │  (Innovation 1) │    │    │  (Innovation 2)  │    │
    └────────┬────────┘    │    └─────────┬────────┘    │
             │              │              │              │
    ┌────────▼────────┐    │    ┌─────────▼────────┐    │
    │  Constitution   │    │    │    Lifecycle     │    │
    │  (Innovation 3) │    │    │   (Extended 9)   │    │
    └────────┬────────┘    │    └─────────┬────────┘    │
             │              │              │              │
             └──────────────┴──────────────┴──────────────┘
                            │
                   ┌────────▼────────┐
                   │    Event Bus    │
                   │  (Async Comms)  │
                   └────────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
    │   Config     │ │  Database  │ │  File Sys   │
    │ (YAML files) │ │  (SQLite)  │ │  (.spectra/)│
    └──────────────┘ └────────────┘ └─────────────┘
```

## Core Components

### 1. Core Infrastructure (`spectra/core/`)

Foundation layer providing:
- **Config Management**: Project configuration and YAML persistence
- **Database**: SQLite schema and connection management  
- **Event Bus**: Synchronous event dispatch for cross-module communication
- **Exceptions**: Typed exception hierarchy

### 2. Intent Graph (`spectra/intent_graph/`)

Knowledge graph tracking specs and relationships:
- **Models**: Node and edge data structures
- **Parser**: YAML spec parsing and validation
- **Store**: Dual persistence (YAML files + SQLite index)
- **Query Engine**: NetworkX-based graph queries (dependencies, impact analysis, cycles)
- **Absorber**: Delta absorption after merges
- **Visualizer**: Terminal and DOT format output

### 3. Adaptive Ceremony (`spectra/ceremony/`)

Dynamic workflow based on change risk:
- **Levels**: 6 ceremony levels (EXPLORE → LOCKED)
- **Checks**: Individual requirement validators
- **Assessor**: Risk/complexity analysis
- **Enforcer**: Gate logic and blocker detection
- **Workflow Builder**: Dynamic workflow generation

### 4. Constitution (`spectra/constitution/`)

Policy engine with rule evaluation:
- **Schema**: Pydantic models for YAML validation
- **Loader**: Constitution file loading and merging
- **Engine**: Rule evaluation engine
- **Profiles**: Built-in governance models (strict/balanced/rapid)
- **Validators**: Auto-validation plugins

### 5. Lifecycle Management (`spectra/lifecycle/`)

State machine for spec progression:
- **Models**: State definitions and transitions
- **State Machine**: Transition validation
- **Promotion**: Promote/demote with ceremony and constitution gates
- **History**: Audit trail and time-in-state tracking

### 6. CLI (`spectra/cli/`)

Typer-based command interface:
- **Main**: Entry point and global options
- **Commands**: Command modules (spec, ceremony, const, init)
- **Rich Output**: Terminal formatting

## Data Flow

### Creating a Spec

```
User: spectra spec new feature-x
  │
  ├──> Parse template
  ├──> Generate ID
  ├──> Create YAML file (.spectra/specs/feature-x.yaml)
  ├──> Insert into database (specs table)
  ├──> Extract edges from YAML
  ├──> Insert edges (edges table)
  └──> Emit SPEC_CREATED event
         │
         └──> Event handlers:
              - Constitution auto-check
              - Cycle detection
```

### Promoting a Spec

```
User: spectra spec promote feature-x
  │
  ├──> Load spec from database
  ├──> Determine next state (state machine)
  ├──> Check ceremony gate (CeremonyEnforcer)
  │     └──> Run required checks
  ├──> Check constitution (ConstitutionEngine)
  │     └──> Evaluate all rules
  ├──> Update spec state
  ├──> Record transition (lifecycle_transitions table)
  └──> Emit SPEC_PROMOTED event
```

## Database Schema

### Core Tables

**specs**: Spec metadata and index
- id (PK), name, intent, ceremony_level, lifecycle_state, trust_score, metadata, timestamps

**edges**: Graph relationships
- source_id, target_id, edge_type, weight

**lifecycle_transitions**: State change audit trail
- spec_id, from_state, to_state, actor, reason, timestamp

**events**: Event bus persistence
- id, event_type, source, payload, created_at

**ceremony_checks**: Check results
- spec_id, check_name, passed, details, checked_at

**constitution_violations**: Rule violations
- spec_id, rule_name, severity, message, detected_at

See `spectra/core/database.py` for complete schema including Phase 2-4 tables.

## Event System

All modules communicate through a synchronous event bus. Key events:

**Spec Events**: SPEC_CREATED, SPEC_UPDATED, SPEC_DELETED, SPEC_LINKED

**Lifecycle Events**: SPEC_PROMOTED, SPEC_DEMOTED, STATE_CHANGED

**Ceremony Events**: CEREMONY_LEVEL_CHANGED, CEREMONY_CHECK_RUN, CEREMONY_GATE_BLOCKED

**Constitution Events**: CONSTITUTION_VIOLATION, RULE_EVALUATED

Event handlers are registered in `spectra/core/wiring.py`.

## File System Layout

```
.spectra/
├── config.yaml           # Project configuration
├── constitution.yaml     # Active constitution rules
├── db/
│   └── spectra.db       # SQLite database
├── specs/               # YAML spec files
│   ├── spec-1.yaml
│   └── spec-2.yaml
└── snapshots/           # Temporal snapshots (Phase 4)
```

## Extension Points

Spectra is designed for extensibility:

1. **Custom Ceremony Checks**: Add checks in `spectra/ceremony/checks.py`
2. **Constitution Rules**: Define rules in YAML or Python profiles
3. **Event Handlers**: Subscribe to events for custom logic
4. **Validators**: Add validators in `spectra/constitution/validators/`

## Design Principles

1. **YAML as Source of Truth**: Specs are YAML files, SQLite is an index
2. **Event-Driven**: Modules communicate via events, not direct imports
3. **Stateless CLI**: Each CLI invocation rebuilds state from database
4. **Forward-Compatible**: Database schema includes all phase tables
5. **Fail-Safe**: Constitution and ceremony can be bypassed in rapid mode

## Performance Considerations

- NetworkX graph rebuilt on each CLI invocation (acceptable for CLI usage)
- SQLite WAL mode for better concurrency
- Indexes on common query fields
- YAML parsing cached in memory during single CLI execution

## Future Phases

**Phase 2**: Conflict Detection + Agent Orchestration  
**Phase 3**: Feedback Loop + Spec Testing + Metrics  
**Phase 4**: Drift Detection + Temporal Rewind + Trust Scoring

See implementation plan for details.
