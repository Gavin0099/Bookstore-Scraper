#!/usr/bin/env python3
"""
✅ Contract Validator — Governance Contract 合規性驗證工具
Priority: 8 (Governance Tooling)

功能:
  驗證 AI 回覆是否包含合規的 [Governance Contract] 區塊
  (定義於 SYSTEM_PROMPT.md §2 ⑦)

用法:
  echo "<AI 回覆>" | python contract_validator.py
  python contract_validator.py --file response.txt
  python contract_validator.py --file response.txt --format json

退出碼:
  0 = 合規
  1 = 不合規 (缺欄位或格式錯誤)
  2 = 找不到 [Governance Contract] 區塊
"""

import re
import sys
import json
import argparse
from dataclasses import dataclass, field
from typing import Optional


# ── 合法值定義（對應 SYSTEM_PROMPT.md §2 ①） ──────────────────────────
VALID_LANG  = {"C++", "C#", "ObjC", "Swift", "JS"}
VALID_LEVEL = {"L0", "L1", "L2"}
VALID_SCOPE = {"feature", "refactor", "bugfix", "I/O", "tooling", "review"}
VALID_PRESSURE_LEVELS = {"SAFE", "WARNING", "CRITICAL", "EMERGENCY"}

REQUIRED_LOADED = {"SYSTEM_PROMPT", "HUMAN-OVERSIGHT"}


@dataclass
class ValidationResult:
    compliant: bool
    contract_found: bool
    fields: dict
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def extract_contract_block(text: str) -> Optional[str]:
    """
    從文字中擷取 [Governance Contract] 區塊內容。

    支援兩種格式:
      1. 純文字區塊 (直接跟在 [Governance Contract] 後)
      2. Markdown code block 包裹的區塊
    """
    # 格式 1: markdown code block
    pattern_code = r'```[^\n]*\n\[Governance Contract\]\n(.*?)```'
    match = re.search(pattern_code, text, re.DOTALL)
    if match:
        return match.group(0)

    # 格式 2: 純文字（[Governance Contract] 後直到空行或文末）
    pattern_plain = r'\[Governance Contract\]\n((?:[A-Z_]+\s*=\s*.+\n?)+)'
    match = re.search(pattern_plain, text)
    if match:
        return match.group(0)

    return None


def parse_contract_fields(block: str) -> dict:
    """解析 KEY = VALUE 欄位，回傳 dict。"""
    fields = {}
    for line in block.splitlines():
        if "=" in line and not line.strip().startswith("[") and not line.strip().startswith("`"):
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key:
                fields[key] = value
    return fields


def validate_contract(text: str) -> ValidationResult:
    """
    主驗證邏輯。

    Returns:
        ValidationResult with errors list (blocking) and warnings list (non-blocking)
    """
    block = extract_contract_block(text)

    if block is None:
        return ValidationResult(
            compliant=False,
            contract_found=False,
            fields={},
            errors=["[Governance Contract] 區塊不存在於回覆中"],
        )

    fields = parse_contract_fields(block)
    errors = []
    warnings = []

    # ── LANG ──────────────────────────────────────────────────────────
    lang = fields.get("LANG", "").strip()
    if not lang:
        errors.append("LANG 欄位缺失")
    elif lang not in VALID_LANG:
        errors.append(f"LANG 值無效: '{lang}'，合法值: {sorted(VALID_LANG)}")

    # ── LEVEL ─────────────────────────────────────────────────────────
    level = fields.get("LEVEL", "").strip()
    if not level:
        errors.append("LEVEL 欄位缺失")
    elif level not in VALID_LEVEL:
        errors.append(f"LEVEL 值無效: '{level}'，合法值: {sorted(VALID_LEVEL)}")

    # ── SCOPE ─────────────────────────────────────────────────────────
    scope = fields.get("SCOPE", "").strip()
    if not scope:
        errors.append("SCOPE 欄位缺失")
    elif scope not in VALID_SCOPE:
        errors.append(f"SCOPE 值無效: '{scope}'，合法值: {sorted(VALID_SCOPE)}")

    # ── PLAN ──────────────────────────────────────────────────────────
    plan = fields.get("PLAN", "").strip()
    if not plan:
        warnings.append("PLAN 欄位缺失 — 若專案有 PLAN.md，此欄位為必填")

    # ── LOADED ────────────────────────────────────────────────────────
    loaded_raw = fields.get("LOADED", "").strip()
    if not loaded_raw:
        errors.append("LOADED 欄位缺失")
    else:
        loaded_docs = {doc.strip() for doc in loaded_raw.split(",")}
        missing_required = REQUIRED_LOADED - loaded_docs
        if missing_required:
            errors.append(
                f"LOADED 缺少必要文件: {sorted(missing_required)} "
                f"(SYSTEM_PROMPT 和 HUMAN-OVERSIGHT 必須永遠載入)"
            )

    # ── CONTEXT ───────────────────────────────────────────────────────
    context = fields.get("CONTEXT", "").strip()
    if not context:
        errors.append("CONTEXT 欄位缺失")
    else:
        if "—" not in context and "--" not in context:
            errors.append("CONTEXT 缺少 '—' 分隔符（格式: <名稱> — <負責>; NOT: <不負責>）")
        if "NOT:" not in context:
            errors.append("CONTEXT 缺少 'NOT:' 子句（必須明確宣告不負責的範圍）")

    # ── PRESSURE ──────────────────────────────────────────────────────
    pressure = fields.get("PRESSURE", "").strip()
    if not pressure:
        errors.append("PRESSURE 欄位缺失")
    else:
        pressure_level = pressure.split("(")[0].strip()
        if pressure_level not in VALID_PRESSURE_LEVELS:
            errors.append(
                f"PRESSURE 等級無效: '{pressure_level}'，"
                f"合法值: {sorted(VALID_PRESSURE_LEVELS)}"
            )
        if "(" not in pressure or "/" not in pressure:
            warnings.append("PRESSURE 建議包含行數資訊，格式: SAFE (45/200)")

    # ── AGENT_ID / SESSION（optional，但若有 AGENT_ID 則 SESSION 為必填） ──
    agent_id = fields.get("AGENT_ID", "").strip()
    session = fields.get("SESSION", "").strip()

    if agent_id:
        # SESSION 格式驗證: YYYY-MM-DD-NN
        import re as _re
        if not session:
            errors.append(
                "AGENT_ID 存在時 SESSION 為必填（格式: YYYY-MM-DD-NN，例: 2026-03-05-01）"
            )
        elif not _re.fullmatch(r'\d{4}-\d{2}-\d{2}-\d+', session):
            errors.append(
                f"SESSION 格式錯誤: '{session}'，正確格式: YYYY-MM-DD-NN（例: 2026-03-05-01）"
            )
    elif session:
        # 有 SESSION 但無 AGENT_ID → 只是警告
        warnings.append("SESSION 存在但 AGENT_ID 缺失（建議一起填寫）")

    return ValidationResult(
        compliant=len(errors) == 0,
        contract_found=True,
        fields=fields,
        errors=errors,
        warnings=warnings,
    )


def format_human(result: ValidationResult) -> str:
    """Human-readable 輸出格式。"""
    lines = []

    if not result.contract_found:
        lines.append("🚨 [Governance Contract] 區塊不存在")
        lines.append("   AI 回覆不合規 — 請要求 AI 重新初始化並輸出合規區塊")
        return "\n".join(lines)

    lines.append("📋 [Governance Contract] 驗證結果")
    lines.append("")

    # 欄位摘要
    for key in ["LANG", "LEVEL", "SCOPE", "PLAN", "LOADED", "CONTEXT", "PRESSURE", "AGENT_ID", "SESSION"]:
        val = result.fields.get(key, "⚠️  缺失")
        lines.append(f"  {key:<10} = {val}")

    lines.append("")

    if result.errors:
        lines.append(f"❌ 不合規 — {len(result.errors)} 個錯誤:")
        for err in result.errors:
            lines.append(f"   • {err}")
    else:
        lines.append("✅ 合規")

    if result.warnings:
        lines.append("")
        lines.append(f"⚠️  {len(result.warnings)} 個警告 (不阻擋):")
        for w in result.warnings:
            lines.append(f"   • {w}")

    return "\n".join(lines)


def format_json(result: ValidationResult) -> str:
    """JSON 輸出格式（供 CI / 自動化使用）。"""
    output = {
        "compliant": result.compliant,
        "contract_found": result.contract_found,
        "fields": result.fields,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Contract Validator — 驗證 AI 回覆是否包含合規的 [Governance Contract] 區塊"
    )
    parser.add_argument(
        "--file", "-f",
        help="AI 回覆文字檔路徑（省略則從 stdin 讀取）"
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="輸出格式 (預設: human)"
    )
    args = parser.parse_args()

    # 讀取輸入
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"❌ 錯誤: 找不到檔案 '{args.file}'", file=sys.stderr)
            sys.exit(2)
    else:
        text = sys.stdin.read()

    # 驗證
    result = validate_contract(text)

    # 輸出
    if args.format == "json":
        print(format_json(result))
    else:
        print(format_human(result))

    # 退出碼
    if not result.contract_found:
        sys.exit(2)
    elif not result.compliant:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
