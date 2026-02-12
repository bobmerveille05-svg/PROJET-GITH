# CLI Reference

Complete reference for all Spectra CLI commands.

## Global Options

Available on all commands:

```bash
--project-dir PATH, -p PATH   # Project directory (auto-detect if not specified)
--verbose, -v                 # Verbose output
--json                        # Output as JSON
```

## Commands

### `spectra init`

Initialize a new Spectra project.

```bash
spectra init [PATH] [OPTIONS]
```

**Arguments:**
- `PATH`: Directory to initialize (default: current directory)

**Options:**
- `--profile, -p TEXT`: Constitution profile (strict/balanced/rapid) [default: balanced]

**Examples:**
```bash
# Initialize in current directory
spectra init

# Initialize in specific directory with strict profile
spectra init ./my-project --profile strict
```

---

### `spectra version`

Show version information.

```bash
spectra version
```

---

## Spec Commands (`spectra spec`)

### `spec new`

Create a new spec from template.

```bash
spectra spec new NAME
```

**Arguments:**
- `NAME`: Spec name

**Examples:**
```bash
spectra spec new user-authentication
spectra spec new "Payment Processing"
```

---

### `spec show`

Display spec details.

```bash
spectra spec show SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Examples:**
```bash
spectra spec show user-authentication
spectra spec show user-auth-123
```

---

### `spec list`

List all specs with optional filters.

```bash
spectra spec list [OPTIONS]
```

**Options:**
- `--state TEXT`: Filter by lifecycle state
- `--level INT`: Filter by ceremony level

**Examples:**
```bash
# List all specs
spectra spec list

# List specs in IMPLEMENTING state
spectra spec list --state IMPLEMENTING

# List specs at ceremony level 3
spectra spec list --level 3
```

---

### `spec edit`

Edit spec in $EDITOR.

```bash
spectra spec edit SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Examples:**
```bash
spectra spec edit user-authentication
```

---

### `spec link`

Create a link between two specs.

```bash
spectra spec link SOURCE TARGET [OPTIONS]
```

**Arguments:**
- `SOURCE`: Source spec ID or name
- `TARGET`: Target spec ID or name

**Options:**
- `--type TEXT`: Edge type [default: depends_on]
  - `depends_on`: Implementation dependency
  - `refines`: Refinement relationship
  - `enables`: Enabling relationship
  - `conflicts_with`: Conflict marker

**Examples:**
```bash
# Create dependency
spectra spec link feature-x feature-y

# Mark refinement
spectra spec link detailed-spec high-level-spec --type refines

# Mark conflict
spectra spec link approach-a approach-b --type conflicts_with
```

---

### `spec unlink`

Remove a link between specs.

```bash
spectra spec unlink SOURCE TARGET
```

---

### `spec tree`

Show dependency tree.

```bash
spectra spec tree [ROOT]
```

**Arguments:**
- `ROOT`: Root spec ID or name (optional)

**Examples:**
```bash
# Show full tree
spectra spec tree

# Show tree from specific root
spectra spec tree auth-system
```

---

### `spec impact`

Analyze impact of changing a spec.

```bash
spectra spec impact SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Examples:**
```bash
spectra spec impact database-schema
```

**Output:**
- Risk level (LOW/MEDIUM/HIGH/CRITICAL)
- Direct dependents
- Transitive dependents
- Total affected specs

---

### `spec promote`

Promote spec to next lifecycle state.

```bash
spectra spec promote SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Behavior:**
- Checks ceremony gates
- Validates constitution rules
- Records transition in history
- Emits SPEC_PROMOTED event

**Examples:**
```bash
spectra spec promote user-authentication
```

---

### `spec demote`

Demote spec to previous lifecycle state.

```bash
spectra spec demote SPEC_REF --reason REASON
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Options:**
- `--reason TEXT`: Reason for demotion (required)

**Examples:**
```bash
spectra spec demote feature-x --reason "Tests failing, need rework"
```

---

### `spec status`

Show lifecycle and ceremony status.

```bash
spectra spec status SPEC_REF
```

---

### `spec history`

Show lifecycle transition history.

```bash
spectra spec history SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Output:**
- All state transitions
- Timestamps
- Actors
- Reasons

**Examples:**
```bash
spectra spec history user-authentication
```

---

## Ceremony Commands (`spectra ceremony`)

### `ceremony check`

Run ceremony checks for a spec.

```bash
spectra ceremony check SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Output:**
- Current ceremony level
- Check results (pass/fail)
- Progress percentage

**Examples:**
```bash
spectra ceremony check user-authentication
```

---

### `ceremony suggest`

Suggest appropriate ceremony level for a spec.

```bash
spectra ceremony suggest SPEC_REF
```

**Arguments:**
- `SPEC_REF`: Spec ID or name

**Output:**
- Assessed change category
- Suggested ceremony level
- Assessment factors

**Examples:**
```bash
spectra ceremony suggest database-migration
```

---

### `ceremony set`

Override ceremony level for a spec.

```bash
spectra ceremony set SPEC_REF LEVEL
```

**Arguments:**
- `SPEC_REF`: Spec ID or name
- `LEVEL`: Ceremony level (0-5)

**Note:** Overrides are checked against constitution rules.

---

### `ceremony report`

Show project-wide ceremony status.

```bash
spectra ceremony report
```

**Output:**
- Spec count by ceremony level
- Total specs

---

## Constitution Commands (`spectra const`)

### `const init`

Initialize constitution from profile.

```bash
spectra const init [PROFILE]
```

**Arguments:**
- `PROFILE`: Profile name (strict/balanced/rapid) [default: balanced]

**Examples:**
```bash
spectra const init strict
```

---

### `const show`

Display active constitution rules.

```bash
spectra const show
```

**Output:**
- Profile name and description
- Settings
- All rules with type, severity, enabled status

---

### `const enforce`

Check spec(s) against constitution rules.

```bash
spectra const enforce [SPEC_REF]
```

**Arguments:**
- `SPEC_REF`: Spec ID or name (optional, checks all if omitted)

**Examples:**
```bash
# Check single spec
spectra const enforce user-authentication

# Check all specs
spectra const enforce
```

---

### `const validate`

Validate constitution file syntax.

```bash
spectra const validate
```

**Note:** Validates the constitution YAML against schema.

---

### `const profiles`

List available constitution profiles.

```bash
spectra const profiles
```

**Output:**
- Available profiles
- Descriptions
- Rule counts

---

## Exit Codes

- `0`: Success
- `1`: Error (invalid command, failed operation, etc.)

---

## Environment Variables

- `EDITOR`: Editor to use for `spec edit` (default: vi)
- `SPECTRA_PROJECT`: Override project directory

---

## Tips

### Quick Workflow

```bash
# 1. Initialize project
spectra init --profile balanced

# 2. Create a spec
spectra spec new my-feature

# 3. Edit the spec
spectra spec edit my-feature

# 4. Check ceremony level
spectra ceremony check my-feature

# 5. Enforce constitution
spectra const enforce my-feature

# 6. Promote when ready
spectra spec promote my-feature
```

### Viewing Dependencies

```bash
# See what depends on a spec
spectra spec impact auth-system

# See full tree
spectra spec tree

# See tree from specific root
spectra spec tree auth-system
```

### Tracking Progress

```bash
# List specs by state
spectra spec list --state IMPLEMENTING

# Check lifecycle history
spectra spec history my-feature

# Project-wide ceremony report
spectra ceremony report
```

---

## Common Errors

### "Not in a Spectra project"

**Cause:** No `.spectra/` directory found in current or parent directories.

**Solution:** Run `spectra init` or `cd` into a Spectra project.

### "Spec not found"

**Cause:** Invalid spec ID or name.

**Solution:** Use `spectra spec list` to see available specs.

### "Ceremony requirements not met"

**Cause:** Trying to promote without satisfying ceremony gates.

**Solution:** Run `spectra ceremony check <spec>` to see what's missing.

### "Constitution violations"

**Cause:** Spec doesn't satisfy constitution rules.

**Solution:** Run `spectra const enforce <spec>` to see violations, then fix the spec.
