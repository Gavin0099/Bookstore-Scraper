#!/usr/bin/env python3
"""
⚙️ State Generator — PLAN.md → .governance-state.yaml
Priority: 8 (Governance Tooling)

功能:
  從 PLAN.md 萃取機器可讀的狀態，寫入 .governance-state.yaml。
  解決 PLAN.md 對工具難以 query 的問題（control-plane / data-plane 分離）。

用法:
  python state_generator.py                  # 讀取當前目錄 PLAN.md，輸出 .governance-state.yaml
  python state_generator.py --plan PLAN.md --output .governance-state.yaml
  python state_generator.py --dry-run        # 只輸出到 stdout，不寫檔
  python state_generator.py --format json    # JSON 格式輸出

.governance-state.yaml 結構:
  generated_at:        ISO timestamp
  plan_path:           來源 PLAN.md 路徑
  project:             專案 metadata（類型、複雜度、Owner、freshness status）
  current_phase:       當前 Phase 識別碼與名稱
  active_sprint:       本週聚焦任務列表
  gate_status:         各 Phase gate 通過狀態
  backlog_counts:      P0/P1/P2 各優先級待辦數量
  freshness:           freshness 狀態（從 plan_freshness 模組取得）
"""

import re
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 重用 plan_freshness 的邏輯
try:
    # 同目錄匯入
    from plan_freshness import check_freshness, STATUS_FRESH, STATUS_STALE, STATUS_CRITICAL, STATUS_ERROR
    _has_freshness = True
except ImportError:
    _has_freshness = False


# ── YAML 最小化輸出（不依賴 pyyaml） ─────────────────────────────────────
def _yaml_str(val) -> str:
    """安全地將值序列化為 YAML scalar。"""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    # 需要引號的情況
    if any(c in s for c in (':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '\n', '\r')):
        return f'"{s}"'
    if not s:
        return '""'
    return s


def dict_to_yaml(d: dict, indent: int = 0) -> str:
    """遞迴輸出 dict 為 YAML（僅支援 str/int/bool/None/list/dict）。"""
    lines = []
    prefix = "  " * indent
    for key, val in d.items():
        if isinstance(val, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(dict_to_yaml(val, indent + 1))
        elif isinstance(val, list):
            lines.append(f"{prefix}{key}:")
            for item in val:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        if first:
                            lines.append(f"{prefix}  - {k}: {_yaml_str(v)}")
                            first = False
                        else:
                            lines.append(f"{prefix}    {k}: {_yaml_str(v)}")
                else:
                    lines.append(f"{prefix}  - {_yaml_str(item)}")
        else:
            lines.append(f"{prefix}{key}: {_yaml_str(val)}")
    return "\n".join(lines)


# ── 解析邏輯 ──────────────────────────────────────────────────────────────

def parse_header(text: str) -> dict:
    """解析 PLAN.md blockquote header 欄位。"""
    fields = {}
    for match in re.finditer(r'>\s*\*\*([^*]+)\*\*\s*:\s*(.+)', text):
        key = match.group(1).strip()
        val = match.group(2).strip()
        fields[key] = val
    return fields


def parse_current_phase(text: str) -> dict:
    """
    解析當前 Phase 資訊。

    範例行:
      ├─ [🔄] Phase B: 可採用性基礎       (進行中，預計 2026/04/15)
      **當前 Phase**: **Phase B — 可採用性基礎**
    """
    # 找到 [🔄] 行
    active_match = re.search(
        r'[├└]─\s*\[🔄\]\s*(Phase\s+\w+)[：:]\s*([^\n(]+)',
        text
    )
    phase_id = None
    phase_name = None
    if active_match:
        phase_id = active_match.group(1).strip().replace(" ", "")  # e.g. "PhaseB"
        phase_name = active_match.group(2).strip()

    # 也嘗試從宣告行取得
    decl_match = re.search(
        r'\*\*當前\s*Phase\*\*[：:]\s*\*\*(Phase\s+\w+)[—\-–\s]+([^*\n]+)\*\*',
        text
    )
    if decl_match:
        phase_id = decl_match.group(1).strip().replace(" ", "")
        phase_name = decl_match.group(2).strip()

    return {
        "id": phase_id,
        "name": phase_name,
    }


def parse_gate_status(text: str) -> dict:
    """解析各 Phase 的任務狀態。"""
    gates = {}
    # 尋找如 ├─ [✓] Phase A、├─ [🔄] Phase B、├─ [⏳] Phase C
    for match in re.finditer(
        r'[├└]─\s*\[([✓🔄⏳])\]\s*(Phase\s+\w+)',
        text
    ):
        icon = match.group(1)
        phase = match.group(2).strip().replace(" ", "")
        if icon == "✓":
            gates[phase] = "passed"
        elif icon == "🔄":
            gates[phase] = "in_progress"
        else:
            gates[phase] = "pending"
    return gates


def parse_sprint_tasks(text: str) -> list:
    """
    解析「本週聚焦」的任務清單。

    格式:
      - [ ] 任務名稱 (4h)
      - [x] 完成的任務
    """
    tasks = []
    # 找到「本週聚焦」章節
    sprint_match = re.search(r'##\s*🔥\s*本週聚焦.*?\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not sprint_match:
        return tasks

    block = sprint_match.group(1)
    for m in re.finditer(r'-\s*\[([ xX✓])\]\s*(.+)', block):
        status_char = m.group(1).strip()
        name = m.group(2).strip()
        # 清除時間標記如 (4h)
        name_clean = re.sub(r'\s*\(\d+h\)\s*$', '', name).strip()
        done = status_char in ('x', 'X', '✓')
        tasks.append({"name": name_clean, "done": done})

    return tasks


def parse_backlog_counts(text: str) -> dict:
    """計算 Backlog 中各優先級的待辦數量。"""
    counts = {"P0": 0, "P1": 0, "P2": 0}

    # 找到「待辦清單」章節
    backlog_match = re.search(r'##\s*📊\s*待辦清單.*?\n(.*?)(?=\n##\s*[^#]|\Z)', text, re.DOTALL)
    if not backlog_match:
        return counts

    block = backlog_match.group(1)
    current_priority = None

    for line in block.splitlines():
        p_match = re.search(r'###.*?(P[012])', line)
        if p_match:
            current_priority = p_match.group(1)
            continue
        if current_priority and re.match(r'\s*-\s*\[\s*\]', line):
            counts[current_priority] = counts.get(current_priority, 0) + 1

    return counts


def generate_state(plan_path: Path) -> dict:
    """主邏輯：從 PLAN.md 生成 state dict。"""
    if not plan_path.exists():
        return {
            "error": f"找不到 PLAN.md: {plan_path}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    text = plan_path.read_text(encoding="utf-8")
    header = parse_header(text)

    # Freshness
    freshness_data: dict = {}
    if _has_freshness:
        fr = check_freshness(plan_path)
        freshness_data = {
            "status": fr.status,
            "last_updated": fr.last_updated.isoformat() if fr.last_updated else None,
            "days_since_update": fr.days_since_update,
            "threshold_days": fr.threshold_days,
        }
    else:
        freshness_data = {"status": "UNKNOWN", "note": "plan_freshness module not available"}

    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plan_path": str(plan_path),
        "project": {
            "type": header.get("專案類型", None),
            "tech_stack": header.get("技術棧", None),
            "complexity": header.get("複雜度", None),
            "timeline": header.get("預計工期", None),
            "owner": header.get("Owner", None),
            "freshness_policy": header.get("Freshness", None),
        },
        "current_phase": parse_current_phase(text),
        "gate_status": parse_gate_status(text),
        "active_sprint": parse_sprint_tasks(text),
        "backlog_counts": parse_backlog_counts(text),
        "freshness": freshness_data,
    }
    return state


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="State Generator — 從 PLAN.md 生成 .governance-state.yaml"
    )
    parser.add_argument(
        "--plan", "-p",
        default="PLAN.md",
        help="PLAN.md 路徑（預設: 當前目錄的 PLAN.md）",
    )
    parser.add_argument(
        "--output", "-o",
        default=".governance-state.yaml",
        help="輸出路徑（預設: .governance-state.yaml）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只輸出到 stdout，不寫檔",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="輸出格式（預設: yaml）",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan)
    state = generate_state(plan_path)

    if args.format == "json":
        output_str = json.dumps(state, ensure_ascii=False, indent=2)
    else:
        header_comment = (
            "# .governance-state.yaml\n"
            "# Auto-generated by governance_tools/state_generator.py\n"
            "# DO NOT edit manually — update PLAN.md instead\n"
            "#\n"
        )
        output_str = header_comment + dict_to_yaml(state)

    if args.dry_run:
        print(output_str)
    else:
        out_path = Path(args.output)
        out_path.write_text(output_str + "\n", encoding="utf-8")
        print(f"✅ 已生成: {out_path}")
        if "error" not in state:
            phase = state.get("current_phase", {})
            freshness = state.get("freshness", {})
            print(f"   Phase: {phase.get('id')} — {phase.get('name')}")
            print(f"   Freshness: {freshness.get('status')} ({freshness.get('days_since_update', '?')}d)")
            counts = state.get("backlog_counts", {})
            print(f"   Backlog: P0={counts.get('P0',0)} P1={counts.get('P1',0)} P2={counts.get('P2',0)}")


if __name__ == "__main__":
    main()
