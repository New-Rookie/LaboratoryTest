"""Markdown report generation from ExperimentRun only."""

from __future__ import annotations

import json
from pathlib import Path

from lab.models import ExperimentRun


def write_markdown_report(run: ExperimentRun, output_dir: str | Path = "reports") -> str:
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{run.run_id}.md"

    verdict = run.verdict
    lines: list[str] = []
    lines.append(f"# 实验报告：{run.spec.name}\n")
    lines.append(f"- Run ID：`{run.run_id}`")
    lines.append(f"- 实验类型：`{run.spec.kind}`")
    lines.append(f"- 状态：`{run.status}`")
    lines.append(f"- 开始时间：{run.started_at}")
    lines.append(f"- 结束时间：{run.ended_at or '-'}")
    lines.append("")

    if verdict:
        lines.append("## 结论")
        lines.append(f"- 判定：`{verdict.status}`")
        lines.append(f"- 可信度评分：{verdict.reliability_score}/100")
        lines.append(f"- 摘要：{verdict.summary}")
        if verdict.reasons:
            lines.append("\n### 原因")
            lines.extend([f"- {item}" for item in verdict.reasons])
        if verdict.suggestions:
            lines.append("\n### 建议")
            lines.extend([f"- {item}" for item in verdict.suggestions])
        lines.append("")

    lines.append("## 参数")
    lines.append(json.dumps(run.spec.params, ensure_ascii=False, indent=2))
    lines.append("")
    lines.append("## 指标")
    lines.append(json.dumps(run.metrics, ensure_ascii=False, indent=2))
    lines.append("")

    if run.errors:
        lines.append("## 问题")
        lines.extend([f"- {error}" for error in run.errors])
        lines.append("")

    if run.artifacts:
        lines.append("## 证据文件")
        lines.extend([f"- {key}: `{value}`" for key, value in run.artifacts.items()])

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
