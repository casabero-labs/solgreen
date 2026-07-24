from __future__ import annotations

from solgreen.diagnostics.llm_input import LLMEpisodeInput


def build_prompt(input_data: LLMEpisodeInput) -> str:
    ep = input_data.episode
    lines = [
        "# Solar diagnostics prompt",
        "",
        f"Plant: {input_data.plant_id}",
        f"Episode type: {ep.episode_type}",
        f"Period: {ep.start.isoformat()} → {ep.end.isoformat()} ({ep.duration})",
        f"Samples: {ep.sample_count} (coverage {ep.coverage_pct:.1f}%)",
        f"Source: {ep.source_summary}",
        "",
    ]

    if ep.signals:
        lines.append("## Signals (averages)")
        lines.append("")
        for key, val in ep.signals.items():
            lines.append(f"- {key}: {val:.1f}")
        lines.append("")

    fired = [r for r in input_data.fired_rules if r.fired]
    if fired:
        lines.append("## Activated rules")
        lines.append("")
        for i, r in enumerate(fired, 1):
            lines.append(f"E{i}: [{r.rule_id}] fired at {r.period_start.isoformat()}")
            for ev in r.evidence:
                lines.append(f"  - {ev}")
        lines.append("")

    if input_data.data_quality_summary:
        lines.append("## Data quality")
        lines.append("")
        lines.append(input_data.data_quality_summary)
        lines.append("")

    if input_data.manual_excerpts:
        lines.append("## Authorized manual excerpts")
        lines.append("")
        for excerpt in input_data.manual_excerpts:
            lines.append(f"- {excerpt}")
        lines.append("")

    lines.extend(
        [
            "## Instructions",
            "",
            "Respond in JSON with this exact schema:",
            "",
            "{",
            '  "summary": "string (1-3 sentences)",',
            '  "hypotheses": [{"description": "string", "support_level": "strong|moderate|weak", "evidence_refs": [int]}],',
            '  "alternatives": ["string"],',
            '  "missing_info": ["string"],',
            '  "suggested_actions": ["string"],',
            '  "warnings": ["string"]',
            "}",
            "",
            "## Rules",
            "",
            "- NEVER declare a cause as 'confirmed' — use support_level instead.",
            "- NEVER invent severity levels — reference only the activated rules.",
            "- ALWAYS cite evidence by E-number (evidence_refs).",
            "- If you lack information, say so in missing_info.",
            f"- Max tokens: {input_data.max_tokens}",
        ]
    )

    return "\n".join(lines)
