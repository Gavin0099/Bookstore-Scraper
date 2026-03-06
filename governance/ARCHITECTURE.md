# 🏗️ ARCHITECTURE.md
**Architecture Governance & Boundary Rules — v4.0**

> **Version**: 4.0 | **Priority**: 5 (Structural Red Lines)
>
> Defines **how the system is partitioned, what may change, and what are hard red lines**.
> Avalonia cross-platform & native interop focus.

Conflict resolution per `SYSTEM_PROMPT.md` §3.

---

## 0. Loading Condition

- **Tier 1** — mandatory when: new features, refactors, boundary changes
- All L1/L2 tasks **must load**

---

## 1. Core Principles

**Architecture > Implementation**: boundaries, responsibilities, data flow come before classes and libraries.
Architecture cannot be articulated first → **implementation forbidden**.

**Explicit Boundaries**: every component must answer —
Is this Domain / Application / Adapter / Infrastructure? Responsible for what? **NOT** responsible for what?

❌ Unclassifiable = architecture violation

---

## 2. Bounded Context

### 2.1 Mandatory Questions (L1+)

- Which Bounded Context does this belong to?
- Involves native APIs / platform variance / external systems?
- ACL required?

Any answer unclear → **STOP**

### 2.2 L0 Exception

Full L0 definition in `AGENT.md` §2. Architecture addendum:
❌ No Domain ↔ Infrastructure crossing ❌ No native/I/O/state interaction.
Uncertain → upgrade to L1.

### 2.3 Anti-Corruption Layer (ACL)

**Mandatory**: native API models conflict with Domain language, native layer has state/side effects/async, translation/validation/caching/error conversion needed.

**Discouraged**: behavior is stable/pure/stateless, clearly non-replaceable, purely computational.

> "Replaceable" ≠ "abstract everything immediately"

---

## 3. Domain vs Infrastructure

### Domain Hard Red Lines

Domain **must NOT**: call P/Invoke, depend on `.dll`/`.so`/`.framework`, be aware of OS/platform/UI/time/environment variables.

Domain interacts with capabilities only via abstract interfaces.

### Infrastructure (Anti-False-Positive)

Infrastructure absorbs instability and real-world complexity.

The following are **NOT** Infrastructure leakage: pure data transformations, OS-agnostic utilities, compile-time constants.

❌ Do not reject valid designs due to doctrinal overreach.

---

## 4. Interface Rules

**Mandatory**: platform behavior differs, native resource lifetimes, ABI/binary instability.

**Discouraged**: logic permanently stable, no replacement path, no boundary risk.

---

## 5. Examples

### ❌ Over-Engineering

```csharp
public interface IClockProvider { DateTime Now(); }
```
Only used for UI time display → unnecessary abstraction.

### ✅ Hard Boundary

```csharp
public interface IFirmwareClock { FirmwareTimestamp Read(); }
```
Native calls + cross-platform + hardware semantics → abstraction mandatory.

---

## 6. ADR (Architecture Decision Record)

### 6.1 Triggers

- Memory ownership strategy
- Cross-platform loading strategy differences
- ABI / calling convention decisions
- `LibraryImport` vs `DllImport` selection
- Any decision affecting boundary partitioning

### 6.2 Conflict Check (Closed-Loop Verification)

Before producing a new ADR, the agent **must**:

1. List all existing ADR titles from `docs/adr/`
2. Identify any potential conflicts with the proposed decision
3. If conflict exists:
   - Either mark the old ADR as `Superseded (by ADR-XXXX)` in the new ADR
   - Or escalate to human if the conflict is ambiguous
4. Reference related ADRs in the "Related Documents" section

❌ Producing an ADR without checking for conflicts → governance violation.

### 6.3 Location

```
docs/adr/
├── 0001-native-library-loading-strategy.md
└── ...
```

### 6.4 Template

```markdown
# ADR-XXXX: [Title]

## Status
Proposed | Accepted | Deprecated | Superseded (by ADR-YYYY)

## Context
What problem prompted this decision?

## Decision
What was chosen?

## Rationale
Why? What alternatives were rejected?

## Consequences
- Positive: ...
- Negative: ...
- Risks: ...

## Conflict Check
- Reviewed existing ADRs: [list titles checked]
- Conflicts: None | Supersedes ADR-XXXX

## Related Documents
Links to governance docs, code, or other ADRs
```

---

## 🧭 Final Principle

> **Architecture prevents catastrophic mistakes, not punishes trivial changes.**
> **Governance reduces risk, not halts progress.**
