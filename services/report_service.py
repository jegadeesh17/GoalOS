"""Weekly retrospective digest: compiles a 7-day report as structured data, Markdown, or printable HTML."""

from __future__ import annotations

import html
import json
from datetime import date, timedelta
from statistics import mean
from typing import Any, Optional

from database.repositories.coach_repository import CoachRepository
from database.repositories.log_repository import LogRepository
from database.repositories.score_repository import ScoreRepository
from models.daily_log import DailyLog
from services.journal_helpers import log_task_stats, week_task_stats


def _avg(values: list[float]) -> Optional[float]:
  return round(mean(values), 2) if values else None


def _collect(logs: list[DailyLog], field: str) -> list[float]:
  out: list[float] = []
  for log in logs:
    value = getattr(log, field, None)
    if value is not None:
      out.append(float(value))
  return out


# Coach output is stored as a JSON blob whose keys vary by session type. Prefer the
# human-readable headline fields; fall back to the first prose value we can find.
_COACH_SUMMARY_KEYS = (
  "urgent_takeaway",
  "mentor_rule",
  "week_summary",
  "summary",
  "takeaway",
  "headline",
  "reflection",
)


def _coach_excerpt(raw: Optional[str], limit: int = 320) -> str:
  """Pull a readable sentence out of a stored coach response."""
  text = (raw or "").strip()
  if not text:
    return ""
  try:
    parsed = json.loads(text)
  except (json.JSONDecodeError, ValueError):
    return text[:limit]

  if isinstance(parsed, dict):
    for key in _COACH_SUMMARY_KEYS:
      value = parsed.get(key)
      if isinstance(value, str) and value.strip():
        return value.strip()[:limit]
    for value in parsed.values():
      if isinstance(value, str) and value.strip():
        return value.strip()[:limit]
  return text[:limit]


class ReportService:
  """Compile a 7-day retrospective from journal logs, scores, and coach output."""

  def __init__(
    self,
    log_repo: Optional[LogRepository] = None,
    score_repo: Optional[ScoreRepository] = None,
    coach_repo: Optional[CoachRepository] = None,
  ) -> None:
    self.log_repo = log_repo or LogRepository()
    self.score_repo = score_repo or ScoreRepository()
    self.coach_repo = coach_repo or CoachRepository()

  def build_report(self, week_start: Optional[date] = None) -> dict[str, Any]:
    """Assemble the structured weekly digest payload for a 7-day window."""
    start = week_start or (date.today() - timedelta(days=6))
    end = start + timedelta(days=6)

    logs = self.log_repo.get_range(start, end)
    scores = self.score_repo.get_range(start, end)
    task_stats = week_task_stats(logs)

    momentum = [s.momentum_score for s in scores if s.momentum_score is not None]
    growth = [s.overall_growth_score for s in scores if s.overall_growth_score is not None]

    takeaways: list[dict[str, Any]] = []
    for log in logs:
      # Journals often carry the same sentence in one_lesson and takeaway; list it once.
      seen: set[str] = set()
      for label, text in (
        ("win", log.one_win),
        ("lesson", log.one_lesson),
        ("takeaway", log.takeaway),
      ):
        cleaned = (text or "").strip()
        if not cleaned or cleaned.casefold() in seen:
          continue
        seen.add(cleaned.casefold())
        takeaways.append({"date": log.date.isoformat(), "kind": label, "text": cleaned})

    coach_notes: list[dict[str, Any]] = []
    try:
      for response in self.coach_repo.get_recent(last_n=20):
        if start <= response.date <= end:
          coach_notes.append(
            {
              "date": response.date.isoformat(),
              "session_type": response.session_type,
              "excerpt": _coach_excerpt(response.ai_response),
            }
          )
    except Exception:
      # Coach history is supplementary; a missing/empty table must not fail the digest.
      coach_notes = []

    daily_rows = [
      {
        "date": log.date.isoformat(),
        "sleep_hours": log.sleep_hours,
        "deep_work_hours": log.deep_work_hours,
        "mood_evening": log.mood_evening,
        "tasks": log_task_stats(log),
      }
      for log in logs
    ]

    return {
      "week_start": start.isoformat(),
      "week_end": end.isoformat(),
      "days_logged": task_stats["days_logged"],
      "tasks": task_stats,
      "averages": {
        "sleep_hours": _avg(_collect(logs, "sleep_hours")),
        "deep_work_hours": _avg(_collect(logs, "deep_work_hours")),
        "mood_morning": _avg(_collect(logs, "mood_morning")),
        "mood_evening": _avg(_collect(logs, "mood_evening")),
        "momentum_score": _avg([float(m) for m in momentum]),
        "overall_growth_score": _avg([float(g) for g in growth]),
      },
      "daily": daily_rows,
      "takeaways": takeaways,
      "coach_notes": coach_notes,
    }

  def render_markdown(self, report: dict[str, Any]) -> str:
    """Render the digest as a portable Markdown document."""
    avg = report["averages"]
    tasks = report["tasks"]

    def fmt(value: Any, suffix: str = "") -> str:
      return f"{value}{suffix}" if value is not None else "—"

    lines = [
      f"# GoalOS Weekly Digest — {report['week_start']} to {report['week_end']}",
      "",
      "## Summary",
      "",
      f"- Days logged: **{report['days_logged']} / 7**",
      f"- Tasks completed: **{tasks['completed_tasks']} / {tasks['total_tasks']}** "
      f"({fmt(tasks['week_completion_rate'], '%')} completion rate)",
      f"- Average sleep: **{fmt(avg['sleep_hours'], ' hrs')}**",
      f"- Average deep work: **{fmt(avg['deep_work_hours'], ' hrs')}**",
      f"- Average momentum score: **{fmt(avg['momentum_score'])}**",
      f"- Average overall growth score: **{fmt(avg['overall_growth_score'])}**",
      "",
      "## Daily Breakdown",
      "",
      "| Date | Sleep | Deep Work | Tasks | Evening Mood |",
      "| --- | --- | --- | --- | --- |",
    ]

    for row in report["daily"]:
      lines.append(
        f"| {row['date']} | {fmt(row['sleep_hours'], ' h')} | {fmt(row['deep_work_hours'], ' h')} "
        f"| {row['tasks']['completed']}/{row['tasks']['total']} | {fmt(row['mood_evening'])} |"
      )
    if not report["daily"]:
      lines.append("| — | — | — | — | — |")

    lines += ["", "## Wins, Lessons & Takeaways", ""]
    if report["takeaways"]:
      for item in report["takeaways"]:
        lines.append(f"- **{item['date']} · {item['kind'].title()}** — {item['text']}")
    else:
      lines.append("_No wins or lessons recorded this week._")

    lines += ["", "## AI Coach Highlights", ""]
    if report["coach_notes"]:
      for note in report["coach_notes"]:
        lines.append(f"- **{note['date']} · {note['session_type']}** — {note['excerpt']}")
    else:
      lines.append("_No coach sessions recorded this week._")

    lines.append("")
    return "\n".join(lines)

  def render_html(self, report: dict[str, Any]) -> str:
    """Render a self-contained, print-to-PDF friendly HTML document."""
    avg = report["averages"]
    tasks = report["tasks"]

    def fmt(value: Any, suffix: str = "") -> str:
      return html.escape(f"{value}{suffix}") if value is not None else "&mdash;"

    stat_cards = "".join(
      f'<div class="stat"><span class="label">{html.escape(label)}</span>'
      f'<span class="value">{value}</span></div>'
      for label, value in (
        ("Days Logged", f"{report['days_logged']} / 7"),
        ("Tasks Completed", f"{tasks['completed_tasks']} / {tasks['total_tasks']}"),
        ("Completion Rate", fmt(tasks["week_completion_rate"], "%")),
        ("Avg Sleep", fmt(avg["sleep_hours"], " hrs")),
        ("Avg Deep Work", fmt(avg["deep_work_hours"], " hrs")),
        ("Avg Momentum", fmt(avg["momentum_score"])),
      )
    )

    daily_rows = "".join(
      f"<tr><td>{html.escape(row['date'])}</td><td>{fmt(row['sleep_hours'], ' h')}</td>"
      f"<td>{fmt(row['deep_work_hours'], ' h')}</td>"
      f"<td>{row['tasks']['completed']}/{row['tasks']['total']}</td>"
      f"<td>{fmt(row['mood_evening'])}</td></tr>"
      for row in report["daily"]
    ) or '<tr><td colspan="5" class="empty">No journal entries logged this week.</td></tr>'

    takeaways = "".join(
      f"<li><strong>{html.escape(item['date'])} &middot; {html.escape(item['kind'].title())}</strong> "
      f"&mdash; {html.escape(item['text'])}</li>"
      for item in report["takeaways"]
    ) or '<li class="empty">No wins or lessons recorded this week.</li>'

    coach_notes = "".join(
      f"<li><strong>{html.escape(note['date'])} &middot; {html.escape(note['session_type'])}</strong> "
      f"&mdash; {html.escape(note['excerpt'])}</li>"
      for note in report["coach_notes"]
    ) or '<li class="empty">No coach sessions recorded this week.</li>'

    title = f"GoalOS Weekly Digest — {report['week_start']} to {report['week_end']}"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 32px; background: #f8faf8; color: #0f172a;
         font: 14px/1.6 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }}
  .sheet {{ max-width: 860px; margin: 0 auto; background: #fff; border: 1px solid #d1e7dd;
            border-radius: 20px; padding: 32px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; letter-spacing: -0.01em; }}
  h2 {{ font-size: 15px; margin: 28px 0 10px; color: #065f46; }}
  .range {{ color: #64748b; font-size: 12px; margin: 0 0 20px; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
  .stat {{ border: 1px solid #d1e7dd; border-radius: 14px; padding: 12px 14px; background: #f6fbf8; }}
  .stat .label {{ display: block; font-size: 11px; text-transform: uppercase;
                  letter-spacing: 0.05em; color: #475569; font-weight: 600; }}
  .stat .value {{ display: block; font-size: 18px; font-weight: 700; margin-top: 4px; color: #065f46; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e2f0e8; }}
  th {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; }}
  ul {{ padding-left: 18px; margin: 0; }}
  li {{ margin-bottom: 8px; }}
  .empty {{ color: #94a3b8; font-style: italic; list-style: none; margin-left: -18px; }}
  td.empty {{ margin-left: 0; text-align: center; }}
  @media print {{ body {{ background: #fff; padding: 0; }}
                  .sheet {{ border: none; border-radius: 0; padding: 0; max-width: none; }} }}
</style>
</head>
<body>
<div class="sheet">
  <h1>GoalOS Weekly Digest</h1>
  <p class="range">{html.escape(report['week_start'])} &rarr; {html.escape(report['week_end'])}</p>

  <h2>Summary</h2>
  <div class="stats">{stat_cards}</div>

  <h2>Daily Breakdown</h2>
  <table>
    <thead><tr><th>Date</th><th>Sleep</th><th>Deep Work</th><th>Tasks</th><th>Evening Mood</th></tr></thead>
    <tbody>{daily_rows}</tbody>
  </table>

  <h2>Wins, Lessons &amp; Takeaways</h2>
  <ul>{takeaways}</ul>

  <h2>AI Coach Highlights</h2>
  <ul>{coach_notes}</ul>
</div>
</body>
</html>
"""
