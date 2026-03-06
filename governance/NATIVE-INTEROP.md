# 🛠 NATIVE-INTEROP.md
**Native Interop Protocol — v3.0**

> **Version**: 3.0 | **Priority**: 7 (Physical Safety)
>
> P/Invoke & ABI Guardrails — Executable Specification.
> Violating any rule → **STOP immediately, escalate per `HUMAN-OVERSIGHT.md`**.

---

## 0. Scope

Must be loaded and enforced when the task involves:
P/Invoke, native library calls (`.dll`/`.so`/`.framework`), ABI/binary marshalling, data/resource transfer between C# and unmanaged languages.

⚠️ Applicability unclear → **STOP and ask**

---

## 1. Data Integrity

### 1.1 Layout Safety (Mandatory)

All cross-language `struct`s **must**: `[StructLayout(LayoutKind.Sequential)]` + explicit `Pack`.

❌ Relying on default alignment / compiler inference → native calls forbidden.

### 1.2 String Encoding (Mandatory)

Default UTF-8. C# uses `[MarshalAs(UnmanagedType.LPUTF8Str)]`.
Native side must explicitly define: whether string is copied, whether pointer is retained.

❌ String lifetime undefined → STOP.

### 1.3 Memory Ownership (Highest-Risk Red Line)

All cross-boundary memory **must** explicitly define: allocator, deallocator, ownership transfer.

- Forbidden: double free, implicit ownership
- Native allocation → must provide matching `FreeXXX()` API
- C# side → `try/finally` or `SafeHandle`

❌ Cannot answer "who frees this?" → **REJECT**

---

## 2. Resource Management

### 2.1 SafeHandle (Mandatory)

Native pointers **must NOT** be exposed as raw `IntPtr` beyond the Adapter layer → wrap in `SafeHandle`.

❌ `IntPtr` in Service/Domain → architecture violation.

### 2.2 IDisposable (Mandatory)

Adapters holding native resources **must** implement `IDisposable` + Finalizer.
`Dispose` must be idempotent, safe against repeated calls.

---

## 3. Platform & ABI

### 3.1 Calling Convention (Mandatory)

On Windows: `CallingConvention` **must** be explicitly specified.
❌ Default / inferred forbidden.

### 3.2 Platform Probing (Mandatory)

Before loading any native library, **must** execute `IsPlatformSupported()`: OS, architecture (x64/arm64), ABI compatibility.

❌ Load without probing → REJECT.

### 3.3 Library Loading (Cross-Platform Red Line)

❌ Hard-coded names / absolute paths forbidden.

Must: prefer `LibraryImport`, use `NativeLibrary.SetDllImportResolver`, centralize in `Infrastructure.NativeLibraryLoader`.

Failure → throw `PlatformNotSupportedException`.

---

## 4. Error Boundary

### 4.1 Error Severity Classification (Mandatory)

All native errors **must** be classified into one of two categories:

| Category | Examples | Handling |
|---|---|---|
| **Logic Error** (recoverable) | File not found, invalid parameter, device disconnected, timeout | Translate to `Result<T, E>` → may propagate to Domain |
| **Panic / Crash** (unrecoverable) | Access Violation, memory corruption, stack overflow, segfault | **FailFast at Infrastructure layer** → must NOT enter Domain |

**Rules for Panic/Crash:**
- Must be caught at the outermost Infrastructure boundary
- Must log diagnostic info before termination
- Must trigger `Environment.FailFast()` — NOT wrapped in `Result<T, E>`
- Uncertain whether recoverable → **treat as Panic** (fail-safe default)

### 4.2 Native Error Isolation (Mandatory)

Native layer **must NOT** throw exceptions across boundaries → return `int/enum/struct` status codes.
C++/ObjC uses `try/catch` converting to return codes.

#### Crash Handling (Extreme cases)

```csharp
public class CriticalNativeCrashException : Exception
{
    public CriticalNativeCrashException(string message, int errorCode, string platform)
        : base($"{message} (Code: {errorCode}, Platform: {platform})") { }
}
```

This exception is for **logging and diagnostics only** — must NOT be caught and silently continued.

### 4.3 Adapter Error Translation (Mandatory)

Logic errors → `Result<T, E>` or equivalent per `ARCHITECTURE.md`.
❌ Raw numeric error codes entering Domain forbidden.
❌ Panic-level errors wrapped as `Result` forbidden.

---

## 5. Testing

Integrates with `TESTING.md`. All native interop **must**:

- Characterization / contract tests locking behavior
- Verify: memory layout correctness, resource release, error translation
- **Error classification tests**: verify panic-level errors trigger FailFast, not Result
- L2: integration tests on ≥2 platforms

---

## 6. ADR Triggers

Memory ownership strategy, cross-platform loading differences, ABI/calling convention, `LibraryImport` vs `DllImport`
→ **must create ADR**. Format per `ARCHITECTURE.md` §6.

---

## 🧭 Final Principle

> **Native interop is a trust boundary. Anything unclear is unsafe by definition.**
>
> Cannot explain how data crosses the boundary, who frees resources, what happens on failure → **STOP.**
