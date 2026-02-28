---
applyTo: '**'
---
---
applyTo: '**'
---
# Copilot Instructions — PortfoTrack

This repository contains **PortfoTrack**, a local-only personal portfolio tracking tool.
GitHub Copilot should follow the constraints, architecture, and design principles defined below
when generating or suggesting code.

---

## 1. Project Scope & Constraints

- **Local-only application**
  - Runs on a single local machine
  - No network calls, no cloud dependencies

- **File-based persistence only**
  - Use JSON or CSV
  - No database, ORM, or external storage engines

- **Domain focus**
  - Asset-class–level tracking only
  - No security-level price tracking
  - Amount-based snapshots in KRW as the base currency

---

## 2. Core Goals

Copilot-generated code should prioritize:

1. Tracking progress toward a **target asset allocation**
2. Detecting **portfolio drift** after the target is reached
3. Providing **minimal, rule-based rebalancing guidance**

Avoid:
- Optimization-heavy logic
- Prediction or forecasting
- Automated trading signals

---

## 3. Architectural Principles

### Layered Design (Strict)

Keep responsibilities separated:

- **Domain**
  - Pure business logic
  - No I/O, no web handlers, no file system access
  - Examples: `Asset`, `TargetAllocation`, `Tolerance`

- **Storage**
  - JSON serialization/deserialization
  - Versioned file formats
  - Deterministic file naming

- **Web**
  - Flask-based local web interface
  - Thin route handlers
  - Delegates logic to services or domain

Copilot **must not** mix these layers.

---

## 4. Error Handling Policy

### User errors vs programmer errors

- **User input errors**
  - Use custom error hierarchy (`AppError`, etc.)
  - Examples:
    - Invalid request parameters
    - Missing required fields
    - Wrong value type

- **Programmer / invariant violations**
  - Use native Python exceptions (`RuntimeError`, `TypeError`, `KeyError`)
  - Do NOT wrap these in application error classes

Assertions:
- ❌ Not allowed in production code
- ✅ Allowed only in tests

---

## 5. Persistence Rules

- JSON files must:
  - Be human-readable
  - Include explicit schema expectations
  - Be versioned if structure may evolve

- Filenames:
  - Date-based (date only, no time)
  - Asia/Seoul timezone
  - Deterministic and reproducible

Copilot should not introduce:
- Auto-migrations
- Hidden side effects
- Implicit overwrites without intent

---

## 6. Web Interface Rules

- Routes are explicit and RESTful
- API endpoints return JSON; page routes render templates
- Entry point: `python -m portfotrack` or `portfotrack` command
  - Accepts `--host` (default: 127.0.0.1) and `--port` (default: 5000)

Route handlers:
- Use Flask blueprints grouped by domain
- Delegate business logic to services
- Return appropriate HTTP status codes and JSON responses

---

## 7. Code Style & Documentation

- Python version: **3.12+**
- Prefer:
  - `dataclass`
  - `TypedDict`
  - Explicit type annotations

Docstrings:
- Google style
- Required for all public functions and classes
- Describe **invariants and intent**, not obvious mechanics

---

## 8. TDD & Testing Expectations (Mandatory)

This project follows **TDD**.

### 8.1 Default workflow (Red → Green → Refactor)

When implementing or changing behavior, Copilot should:

1. **Write/Update tests first (RED)**
   - Add a failing test that captures the intended behavior.
   - Prefer unit tests at the domain/service boundary.
2. **Minimal implementation (GREEN)**
   - Implement only what is needed to pass tests.
   - Avoid premature abstraction, generalization, or optimization.
3. **Refactor (REFACTOR)**
   - Improve naming, structure, and duplication only after tests pass.
   - Keep refactors behavior-preserving.

### 8.2 Test design rules

- Use `pytest`.
- Prefer small, focused unit tests.
- Tests should document behavior, not implementation details.
- Avoid integration-heavy fixtures unless necessary.
- Import inside test functions is acceptable if it improves readability.
- **New tests go under `tests/` and mirror the package structure**
  (e.g. `portfotrack/storage/...` → `tests/storage/...`)

### 8.3 Coverage expectations (practical)

For new or modified logic, tests must cover:
- Happy path
- At least one failure/edge case
- Error policy boundaries:
  - User error → custom `AppError` hierarchy
  - Programmer/invariant violation → native Python exceptions

### 8.4 No untested production changes

- Copilot should not propose production code changes without
  providing corresponding tests (unless explicitly asked to skip tests).

### 8.5 Commit & Pre-commit Policy (Mandatory)
#### 8.5.1 Pre-commit Execution Requirement
Before creating a commit, the agent **must explicitly execute pre-commit hooks** and verify that all checks pass.

Required workflow:
1. Stage changes.
2. Run:
```sql
pre-commit run --all-files
```
3. Confirm:
* Formatting passes
* Lint passes
* Type checks pass
* Tests pass
4. Only after all checks succeed may the commit be created.

Rules:
* ❌ Never bypass hooks (--no-verify is forbidden).
* ❌ Never commit while checks are failing.
* If any hook fails:
  * Fix the issue.
  * Re-run pre-commit.
  * Confirm all checks pass before committing.

Copilot-generated changes must therefore:
* Already conform to formatting standards.
* Contain no lint violations.
* Include passing tests.
* Avoid unused imports or dead code.

The agent should treat pre-commit success as a hard gate before commit.

#### 8.5.2 Commit Message Convention (Commitizen + Scope Required)
This project follows **Commitizen / Conventional Commits**
and **requires a scope**.

Required format:
```php-template
<type>(<scope>): <short summary>
```

Constraints:
* `type` must follow conventional commit types:
  * `feat`
  * `fix`
  * `refactor`
  * `test`
  * `chore`
  * `docs`
* `scope` must represent the affected module or layer:
  * `domain`
  * `storage`
  * `web`
  * `services`
  * `tests`
  * `config`
  * etc.
* Summary must be:
  * Short
  * Single line
  * Imperative mood
  * No trailing period
  * No unnecessary explanation

Examples:
```scss
feat(domain): add target ratio validation
fix(storage): handle missing assets key
refactor(web): simplify route handlers
test(domain): add tolerance edge case
chore(config): configure pre-commit hooks
docs(readme): clarify persistence rules
```
Avoid:
* Missing scope
* Multi-line summaries
* Verbose explanations in the title
* Non-standard prefixes
* Capitalized summary sentences

Commit titles must remain concise.
Detailed explanations belong in the commit body (optional), not the summary.

---

## 9. What Copilot Should NOT Do

- Introduce databases or external services
- Add async without a clear reason
- Over-engineer abstractions
- Optimize prematurely
- Guess financial advice or strategies

---

## 10. Guiding Philosophy

PortfoTrack values:

- Simplicity over cleverness
- Reproducibility over automation
- Maintenance over optimization
- Explicitness over convenience

When in doubt, Copilot should choose the **simplest correct solution**
that aligns with long-term maintainability.
