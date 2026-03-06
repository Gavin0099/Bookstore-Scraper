# 🧪 TESTING.md
**Testing Strategy & Quality Gates — v4.0**

> **Version**: 4.0 | **Priority**: 6 (Quality Gatekeeper)
>
> Defines **under what conditions we can reasonably trust a piece of code**.
> Tests are guardrails, not KPIs, not coverage competitions.

Conflict resolution per `SYSTEM_PROMPT.md` §3.

---

## 1. Core Philosophy

**Purpose of tests**: prevent regression, protect refactoring, **lock expected behavior**.

❌ Coverage is not a quality metric ❌ Tests without behavioral meaning = no tests

**Behavior over implementation**: tests care only about inputs, outputs, side effects. Not private methods, call order, or implementation details.

> Tests green after refactoring → behavior preserved.

---

## 2. Test Levels

### L0 — Minimal Confidence
Conditions: small scope, trivial rollback, no core behavior affected.
Acceptable: smoke tests, manual checklists, characterization tests.
⚠️ Must not be used to bypass required tests.

### L1 — Maintainable (Default)
**Minimum acceptable bar.** Must include: unit tests (Domain) + failure paths + boundary conditions.
Any item missing → **implementation forbidden**.

### L2 — Critical
Must include: full unit + contract + integration tests + regression tests + human-reviewable acceptance criteria.

---

## 3. Test Types

| Type | Purpose |
|---|---|
| Unit Test | Pure logic, rules, invariants |
| Contract Test | Boundary protocol consistency |
| Integration Test | Verify I/O actually works |
| Characterization Test | Lock legacy behavior |
| Smoke Test | Minimal usability validation |

### Cross-Platform Requirements

| LEVEL | Requirement |
|---|---|
| L0 | Not enforced |
| L1 | Consider cross-platform consistency; native interop recommended on 2 platforms |
| **L2** | **Native interop must have integration tests on ≥2 platforms** |

Additional: UI via `Avalonia.Headless`; data contracts verify `StructLayout`/Endianness/`Marshal.SizeOf`.

---

## 4. Failure Paths (Mandatory for L1+)

Every feature must include at minimum: **1 invalid input + 1 boundary value + 1 failure path**.

❌ Testing only the happy path = test failure.

---

## 5. Platform Variance Test Checklist

For L1+ tasks involving cross-platform code, the agent **must** consider and test the following platform-sensitive areas where applicable:

| Area | Example | Test Strategy |
|---|---|---|
| Path separators | `Path.DirectorySeparatorChar` (`\` vs `/`) | Parameterized test with both separators |
| String encoding | `wchar_t` size (2 bytes Win vs 4 bytes macOS) | Assert `Marshal.SizeOf` per platform |
| Struct alignment | `Pack` / `LayoutKind` differences | Verify `Marshal.SizeOf` matches native expectation |
| Line endings | `\r\n` vs `\n` | Normalize before comparison |
| File system case sensitivity | macOS (default insensitive) vs Linux (sensitive) | Test with mixed-case paths |
| Environment variables | `HOME` vs `USERPROFILE` | Abstract via interface or runtime check |
| Native library names | `.dll` vs `.dylib` vs `.so` | Verify `NativeLibraryLoader` resolution |
| Boolean marshalling | C# `bool` (1 byte) vs ObjC `BOOL` (signed char) | Contract test at boundary |
| UI thread model | Avalonia `Dispatcher.UIThread` | Verify no cross-thread property mutations |

This checklist is a **reference**, not an exhaustive requirement.

---

## 6. I/O & Hard-to-Test Areas

Untestable ≠ untested. I/O / native / time / environment deps: unit tests not forced, but **must** be isolated, replaceable, observable.

**Allowed strategies**: Fake/Stub, recorded responses, integration seams.

### Native Interop (Mandatory)

- Characterization / contract tests locking `NativeAdapter` behavior
- Simulate native errors → verify `Result<T, E>` translation
- Resource management: `using`/`Dispose` assert release
- ❌ Mocking that hides real risk is forbidden

---

## 7. Red Lines

❌ Tests written only to satisfy process ❌ Mocking that masks risk
❌ Tests detached from behavior ❌ Tests passing on single platform only

---

## 8. Test Gap Records (Mandatory)

When a test is currently infeasible, **must** record: reason, risk, remediation condition.

❌ No remediation condition → hidden tech debt → REJECT.

---

## 9. Definition of Done

Behavior explicitly defined + failure paths covered + safe to refactor within test guardrails + results human-readable and reviewable.

---

## 10. Recommended Tools (Non-mandatory)

| Purpose | Tool |
|---|---|
| Unit testing | `xUnit` |
| Integration testing | Custom TestServer |
| UI / Headless | `Avalonia.Headless` |
| Mocking | `NSubstitute` |
| Cross-platform | `Testcontainers` |

---

## 🧭 Final Principle

> **If tests cannot explain why this code is safe, they are not acceptable tests.**
