from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import typer
import yaml
from rich import print
from tabulate import tabulate
from dotenv import load_dotenv

try:
    from .utils import load_csv, resolve_data_path, generate_data_summary
    from .agents import planner as planner_agent
    from .agents import data_agent
    from .agents import insight_agent
    from .agents import evaluator as evaluator_agent
    from .agents import creative_generator
    from .agents import llm as llm_agent
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils import load_csv, resolve_data_path, generate_data_summary
    from src.agents import planner as planner_agent
    from src.agents import data_agent
    from src.agents import insight_agent
    from src.agents import evaluator as evaluator_agent
    from src.agents import creative_generator
    from src.agents import llm as llm_agent


app = typer.Typer(add_completion=False)


def load_config() -> dict:
    load_dotenv()
    cfg_path = Path("config/config.yaml")
    if not cfg_path.exists():
        print("[red]Missing config/config.yaml[/red]")
        raise SystemExit(1)
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def _log_event(log_file, event_type: str, data: Dict[str, Any]):
    """Log event to JSONL file."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data,
    }
    log_file.write(json.dumps(log_entry) + "\n")
    log_file.flush()


@app.command()
def analyze(task: str = typer.Argument(..., help="e.g., Analyze ROAS drop in last 7 days")):
    cfg = load_config()

    use_sample = bool(cfg.get("use_sample_data", True))
    paths = cfg.get("paths", {})
    csv_path = resolve_data_path(
        use_sample=use_sample,
        sample_path=paths.get("sample_csv", "data/synthetic_fb_ads_undergarments.csv"),
        env_var=paths.get("data_csv_env", "DATA_CSV"),

    )

    if csv_path is None:
        print("[red]No CSV path resolved. Set DATA_CSV or enable sample data.[/red]")
        raise SystemExit(2)

    load_result = load_csv(csv_path)
    df = load_result.df

    head_cols = [
        "date",
        "campaign_name",
        "adset_name",
        "spend",
        "impressions",
        "clicks",
        "purchases",
        "revenue",
        "roas",
    ]
    preview = df[head_cols].head(5).fillna("")

    print("[bold green]Loaded dataset[/bold green]", csv_path)
    print(f"Rows: {len(df):,}  Columns: {len(df.columns)}")
    if load_result.notes:
        print("Notes:")
        for n in load_result.notes:
            print(f" - {n}")

    print("\nPreview:")
    print(tabulate(preview.values.tolist(), headers=preview.columns, tablefmt="github"))

    reports_dir = Path(paths.get("reports_dir", "reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    logs_dir = Path(paths.get("logs_dir", "logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_filename = logs_dir / f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    log_file = open(log_filename, "w", encoding="utf-8")
    
    _log_event(log_file, "session_start", {
        "task": task,
        "csv_path": str(csv_path),
        "rows": len(df),
        "columns": list(df.columns),
    })

    data_summary = generate_data_summary(df, top_n=5)
    plan = planner_agent.plan(task, cfg, data_summary=data_summary)
    print("\nPlan:")
    print(plan)
    
    _log_event(log_file, "planner_complete", {
        "plan": plan,
        "plan_source": plan.get("plan_source", "unknown"),
    })

    overview = data_agent.compare_overview(df, plan["time_window_days"])
    print("\nOverview (current vs baseline):")
    print({k: overview[k] for k in ["current_period", "baseline_period"]})

    segments = data_agent.multi_segment_compare(df, plan["time_window_days"], plan["segment_dims"])
    insights = insight_agent.generate_insights(overview, segments, plan)
    
    _log_event(log_file, "insight_generation_complete", {
        "total_insights": len(insights),
        "overview_metrics": overview.get("current", {}),
    })
    
    confidence_min = float(cfg.get("confidence_min", 0.6))
    eval_result = evaluator_agent.evaluate_insights(
        insights, confidence_min, segments=segments, enable_reflection=True
    )
    
    validated_insights = eval_result.get("validated", [])
    needs_retry = eval_result.get("needs_retry", [])
    eval_summary = eval_result.get("summary", {})
    
    _log_event(log_file, "evaluation_complete", {
        "total_insights": eval_summary.get("total", 0),
        "validated": eval_summary.get("validated", 0),
        "low_confidence": eval_summary.get("low_confidence", 0),
        "avg_confidence": eval_summary.get("avg_confidence", 0),
        "needs_retry": len(needs_retry),
    })
    
    if len(needs_retry) > len(validated_insights) * 0.5:
        print(f"\n[yellow]Warning: {len(needs_retry)} insights below confidence threshold. Consider refining hypotheses.[/yellow]")
        _log_event(log_file, "evaluator_warning", {
            "message": "High number of insights need retry",
            "needs_retry_count": len(needs_retry),
            "validated_count": len(validated_insights),
        })
    
    creatives = creative_generator.generate_creatives(
        segments, overview=overview, validated_insights=validated_insights
    )
    
    _log_event(log_file, "creative_generation_complete", {
        "creatives_generated": len(creatives),
    })
    
    insights_eval = validated_insights
    llm_cfg = cfg.get("llm", {})
    llm_provider = str(llm_cfg.get("provider", "")).lower()
    llm_model = str(llm_cfg.get("model", "gpt-4o-mini"))
    narrative = None
    if llm_provider == "openai":
        narrative = llm_agent.generate_narrative(overview, segments, plan, model=llm_model)
        if narrative:
            print("\n[bold green]LLM narrative generated via OpenAI[/bold green]")
            _log_event(log_file, "llm_narrative_complete", {
                "model": llm_model,
                "provider": llm_provider,
                "success": True,
            })
        else:
            print("\n[yellow]LLM narrative skipped (missing OPENAI_API_KEY or API error)[/yellow]")
            _log_event(log_file, "llm_narrative_failed", {
                "model": llm_model,
                "provider": llm_provider,
                "success": False,
            })
    else:
        print("\n[yellow]LLM disabled (llm.provider not set to 'openai')[/yellow]")
    
    _log_event(log_file, "session_complete", {
        "total_insights": len(insights_eval),
        "total_creatives": len(creatives),
        "report_path": str(reports_dir / "report.md"),
    })
    
    log_file.close()
    print(f"\n[dim]Logged to {log_filename}[/dim]")

    stub = {
        "task": task,
        "rows": len(df),
        "columns": list(df.columns),
        "plan": plan,
        "overview": overview,
        "segments": segments,
        "insights": insights_eval,
        "insights_evaluation": eval_result,
        "creatives": creatives,
        "llm_narrative": narrative,
    }
    (reports_dir / "insights.json").write_text(json.dumps(stub, indent=2), encoding="utf-8")
    (reports_dir / "creatives.json").write_text(json.dumps(creatives, indent=2), encoding="utf-8")
    
    report_lines = []
    report_lines.append("# Report")
    report_lines.append("")
    if narrative:
        report_lines.append("## LLM Narrative")
        report_lines.append("")
        report_lines.append(narrative)
        report_lines.append("")
    report_lines.append(f"Task: {task}")
    report_lines.append("")
    report_lines.append("## Analysis Plan (Analyst Thinking)")
    report_lines.append("")
    plan_source = plan.get("plan_source", "rule_based")
    source_label = "LLM-generated" if plan_source == "llm" else "Rule-based"
    report_lines.append(f"**Plan Source:** {source_label}")
    report_lines.append("")
    report_lines.append(f"**Problem Type:** {plan.get('problem_type', 'performance_issue')}")
    report_lines.append("")
    report_lines.append("**Hypotheses to Test:**")
    for i, hyp in enumerate(plan.get('hypotheses', []), start=1):
        report_lines.append(f"{i}. {hyp}")
    report_lines.append("")
    report_lines.append(f"**Analysis Strategy:** {plan.get('analysis_strategy', '')}")
    report_lines.append("")
    
    if plan.get('reasoning'):
        reasoning = plan['reasoning']
        report_lines.append("**Reasoning:**")
        if isinstance(reasoning, dict):
            if reasoning.get('think'):
                report_lines.append(f"- *Think:* {reasoning['think']}")
            if reasoning.get('analyze'):
                report_lines.append(f"- *Analyze:* {reasoning['analyze']}")
            if reasoning.get('conclude'):
                report_lines.append(f"- *Conclude:* {reasoning['conclude']}")
        report_lines.append("")
    
    if plan.get('subtasks'):
        report_lines.append("**Subtask Decomposition:**")
        for i, subtask in enumerate(plan['subtasks'], start=1):
            task_id = subtask.get('task_id', 'unknown')
            agent = subtask.get('agent', 'unknown')
            action = subtask.get('action', 'unknown')
            desc = subtask.get('description', '')
            report_lines.append(f"{i}. [{agent}] {action}: {desc}")
        report_lines.append("")
    
    report_lines.append("**Configuration:**")
    report_lines.append(f"- Window: {plan['time_window_days']} days")
    report_lines.append(f"- KPIs: {', '.join(plan['primary_kpis'])}")
    report_lines.append(f"- Segments (prioritized): {', '.join(plan['segment_dims'])}")
    report_lines.append("")
    report_lines.append("## Overview")
    report_lines.append(f"Current: {overview['current_period']['start']} → {overview['current_period']['end']}")
    report_lines.append(f"Baseline: {overview['baseline_period']['start']} → {overview['baseline_period']['end']}")
    if overview['current'].get('roas') is not None:
        report_lines.append(f"ROAS: {overview['current'].get('roas'):.2f} vs {overview['baseline'].get('roas'):.2f}")
    report_lines.append("")
    
    winners = [ins for ins in insights_eval if "gained" in ins.get("title", "").lower() or ins.get("impact") == "high"]
    losers = [ins for ins in insights_eval if "lost" in ins.get("title", "").lower() or "declined" in ins.get("title", "").lower() or "drop" in ins.get("title", "").lower()]
    
    report_lines.append("## Executive Summary")
    report_lines.append("")
    if overview['current'].get('roas') and overview['baseline'].get('roas'):
        roas_cur = overview['current'].get('roas')
        roas_base = overview['baseline'].get('roas')
        roas_change = ((roas_cur - roas_base) / roas_base * 100) if roas_base > 0 else 0
        revenue_delta = overview.get('delta', {}).get('revenue', 0)
        
        report_lines.append(f"**Performance Change:** ROAS {'declined' if roas_change < 0 else 'improved'} by {abs(roas_change):.2f}% ({roas_cur:.2f} vs {roas_base:.2f})")
        if revenue_delta:
            report_lines.append(f"**Revenue Impact:** ${revenue_delta:+,.0f} vs baseline period")
        report_lines.append("")
    
    report_lines.append("## Top Insights")
    report_lines.append("")
    if eval_summary:
        report_lines.append(f"*Validation Summary: {eval_summary.get('validated', 0)}/{eval_summary.get('total', 0)} insights validated (avg confidence: {eval_summary.get('avg_confidence', 0):.2f})*")
        report_lines.append("")
    
    top_insights = sorted(insights_eval, key=lambda x: (
        {"high": 3, "medium": 2, "low": 1}.get(x.get("impact", "medium"), 1),
        x.get("evaluation", {}).get("final", 0)
    ), reverse=True)[:5]
    
    for i, ins in enumerate(top_insights, start=1):
        title = ins.get('title', 'Unknown')
        eval_data = ins.get('evaluation', {})
        final_score = eval_data.get('final', 0)
        impact = ins.get('impact', 'medium')
        reasoning = ins.get('reasoning', {})
        
        report_lines.append(f"### {i}. {title}")
        report_lines.append(f"**Impact:** {impact.upper()} | **Score:** {final_score:.2f} | **Confidence:** {ins.get('confidence', 0):.2f}")
        report_lines.append("")
        
        if reasoning:
            report_lines.append("**Reasoning:**")
            if reasoning.get('think'):
                report_lines.append(f"- *Think:* {reasoning['think']}")
            if reasoning.get('analyze'):
                report_lines.append(f"- *Analyze:* {reasoning['analyze']}")
            if reasoning.get('conclude'):
                report_lines.append(f"- *Conclude:* {reasoning['conclude']}")
            report_lines.append("")
        
        feedback = eval_data.get('feedback', {})
        if feedback.get('strengths'):
            report_lines.append(f"**Strengths:** {', '.join(feedback['strengths'])}")
        report_lines.append("")
    
    if losers:
        report_lines.append("## Problem Drivers (Underperforming Segments)")
        report_lines.append("")
        report_lines.append("Segments contributing to performance decline:")
        report_lines.append("")
        
        for i, ins in enumerate(losers[:5], start=1):
            title = ins.get('title', 'Unknown')
            eval_data = ins.get('evaluation', {})
            final_score = eval_data.get('final', 0)
            reasoning = ins.get('reasoning', {})
            metric_delta = ins.get('metric_delta', {})
            
            report_lines.append(f"### {i}. {title}")
            report_lines.append(f"**Score:** {final_score:.2f} | **Confidence:** {ins.get('confidence', 0):.2f}")
            
            if metric_delta.get('revenue_delta'):
                report_lines.append(f"**Revenue Impact:** ${metric_delta['revenue_delta']:+,.0f}")
            if metric_delta.get('roas_cur') and metric_delta.get('roas_base'):
                report_lines.append(f"**ROAS:** {metric_delta['roas_cur']:.2f} vs {metric_delta['roas_base']:.2f}")
            
            report_lines.append("")
            
            if reasoning.get('conclude'):
                report_lines.append(f"**Recommendation:** {reasoning['conclude']}")
            
            report_lines.append("")
    
    report_lines.append("## Hypothesis Validation")
    report_lines.append("")
    hypotheses = plan.get('hypotheses', [])
    if hypotheses:
        report_lines.append("Testing the following hypotheses:")
        report_lines.append("")
        for i, hyp in enumerate(hypotheses, start=1):
            matching_insights = [ins for ins in insights_eval if any(word in ins.get('title', '').lower() for word in hyp.lower().split()[:3])]
            status = "Supported" if matching_insights else "Needs more analysis"
            report_lines.append(f"{i}. {hyp} - {status}")
            if matching_insights:
                for ins in matching_insights[:2]:
                    report_lines.append(f"   - {ins.get('title')}")
        report_lines.append("")
    
    if needs_retry:
        report_lines.append("## Insights Needing Revision")
        report_lines.append(f"*{len(needs_retry)} insights flagged for retry (confidence < {confidence_min})*")
        report_lines.append("")
        for ins in needs_retry[:3]:
            report_lines.append(f"- {ins.get('title')}: {ins.get('retry_reason', 'Low confidence')}")
        report_lines.append("")
    
    report_lines.append("## Creative Recommendations (Low-CTR Campaigns)")
    report_lines.append("")
    for i, c in enumerate(creatives[:5], start=1):
        target = c.get('target_campaign', 'Unknown')
        current_ctr = c.get('current_performance', {}).get('ctr', 0)
        target_ctr = c.get('expected_improvement', {}).get('ctr_target', 0)
        rationale = c.get('rationale', '')
        creative = c.get('creative', {})
        
        report_lines.append(f"### {i}. For: {target}")
        report_lines.append(f"**Current CTR:** {current_ctr:.4f} → **Target CTR:** {target_ctr:.4f}")
        report_lines.append("")
        report_lines.append(f"**Hook:** {creative.get('hook', 'N/A')}")
        report_lines.append(f"**Body:** {creative.get('body', 'N/A')}")
        report_lines.append(f"**CTA:** {creative.get('cta', 'N/A')}")
        report_lines.append("")
        if rationale:
            report_lines.append(f"*Rationale:* {rationale}")
        report_lines.append("")
    
    report_lines.append("## Action Items & Next Steps")
    report_lines.append("")
    
    if winners:
        top_winner = winners[0] if winners else None
        if top_winner:
            report_lines.append("**1. Scale Winners:**")
            report_lines.append(f"   - Focus on: {top_winner.get('title', 'Top performers')}")
            report_lines.append(f"   - Action: {top_winner.get('reasoning', {}).get('conclude', 'Increase budget allocation')}")
            report_lines.append("")
    
    if losers:
        top_loser = losers[0] if losers else None
        if top_loser:
            report_lines.append("**2. Address Underperformers:**")
            report_lines.append(f"   - Problem: {top_loser.get('title', 'Underperforming segments')}")
            report_lines.append(f"   - Action: {top_loser.get('reasoning', {}).get('conclude', 'Reallocate budget')}")
            report_lines.append("")
    
    if creatives:
        report_lines.append("**3. Implement Creative Refresh:**")
        report_lines.append(f"   - {len(creatives)} creative recommendations generated for low-CTR campaigns")
        report_lines.append("   - Priority campaigns: " + ", ".join([c.get('target_campaign', 'Unknown') for c in creatives[:5]]))
        report_lines.append("")
    
    report_lines.append("**4. Monitor & Iterate:**")
    report_lines.append("   - Re-run analysis after implementing changes")
    report_lines.append("   - Track CTR improvements for creative updates")
    report_lines.append("   - Monitor budget reallocation impact")
    report_lines.append("")
    
    (reports_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    (reports_dir / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (reports_dir / "data_summary.json").write_text(json.dumps(data_summary, indent=2), encoding="utf-8")
    (reports_dir / "overview.json").write_text(json.dumps(overview, indent=2), encoding="utf-8")
    (reports_dir / "segments.json").write_text(json.dumps(segments, indent=2), encoding="utf-8")
    (reports_dir / "insights.json").write_text(json.dumps(stub, indent=2), encoding="utf-8")
    if narrative:
        (reports_dir / "narrative.md").write_text(narrative, encoding="utf-8")

    print(f"\n[bold green]Wrote[/bold green] {reports_dir / 'report.md'} and insights.json")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "analyze":
        task = " ".join(sys.argv[1:])
        analyze(task)
    else:
        app()

