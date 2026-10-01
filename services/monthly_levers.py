"""Lever analysis: which habits are associated with a higher share of tasks done that day.

Spearman rank correlation with a seeded permutation test, so results are deterministic and
testable. These are associations on small samples: every finding carries its n and a caveat, and a
lever is only reported when there are enough days and the p-value clears a threshold. Nothing here
claims causation.
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable, Optional

METHOD_VERSION = 1
MIN_DAYS = 30  # fewer matched days than this: report nothing for the lever
MIN_GROUP = 5  # fewer days than this in a contrast group: no contrast sentence
STRONG_P = 0.05  # applied to the p-value corrected for the number of levers tested (Bonferroni)
SUGGESTIVE_P = 0.05  # applied to the raw p-value
N_PERMUTATIONS = 1000
WAKE_EARLY, WAKE_LATE = 7.5, 8.5
CAVEAT = "Association on a small sample, not proof of cause."
SLEEP_CAVEAT = (
  CAVEAT + " Sleep length and wake time move together, so this may just be the wake time effect."
)


def clock_label(hour: float) -> str:
  total = round(hour * 60)
  return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def _ranks(values: list[float]) -> list[float]:
  order = sorted(range(len(values)), key=lambda i: values[i])
  ranks = [0.0] * len(values)
  i = 0
  while i < len(order):
    j = i
    while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
      j += 1
    average = (i + j) / 2 + 1
    for k in range(i, j + 1):
      ranks[order[k]] = average
    i = j + 1
  return ranks


def _centered_ranks(values: list[float]) -> list[float]:
  ranks = _ranks(values)
  mean = (len(ranks) + 1) / 2
  return [r - mean for r in ranks]


def _rank_correlation(cx: list[float], cy: list[float]) -> Optional[float]:
  denominator = math.sqrt(sum(a * a for a in cx)) * math.sqrt(sum(b * b for b in cy))
  if denominator == 0:
    return None
  return max(-1.0, min(1.0, sum(a * b for a, b in zip(cx, cy, strict=True)) / denominator))


def spearman(xs: list[float], ys: list[float]) -> Optional[float]:
  if len(xs) != len(ys) or len(xs) < 3:
    return None
  rho = _rank_correlation(_centered_ranks(list(xs)), _centered_ranks(list(ys)))
  return None if rho is None else round(rho, 12)


def permutation_p(xs: list[float], ys: list[float], rng: random.Random) -> Optional[tuple[float, float]]:
  """(rho, two-sided permutation p) or None when a variable is constant."""
  cx, cy = _centered_ranks(list(xs)), _centered_ranks(list(ys))
  rho = _rank_correlation(cx, cy)
  if rho is None:
    return None
  extreme = 0
  shuffled = list(cy)
  for _ in range(N_PERMUTATIONS):
    rng.shuffle(shuffled)
    permuted = _rank_correlation(cx, shuffled)
    if permuted is not None and abs(permuted) >= abs(rho) - 1e-12:
      extreme += 1
  return rho, (extreme + 1) / (N_PERMUTATIONS + 1)


def tier_for(p: float, tests: int) -> Optional[str]:
  """"strong" only if p survives correction for the levers tested together; "suggestive" if it clears 0.05 alone."""
  if min(1.0, p * tests) < STRONG_P:
    return "strong"
  if p < SUGGESTIVE_P:
    return "suggestive"
  return None


Group = tuple[str, Callable[[float], bool]]


def _plan_groups(values: list[float]) -> Optional[tuple[Group, Group]]:
  ordered = sorted(values)
  low, high = ordered[len(ordered) // 3], ordered[(2 * len(ordered)) // 3]
  if low >= high:
    return None
  return (
    (f"{high:g}+ plan hours filled", lambda v: v >= high),
    (f"{low:g} or fewer plan hours filled", lambda v: v <= low),
  )


def _lever_specs(rows: list[dict[str, Any]]) -> list[tuple[str, str, Callable[[dict], Optional[float]], Optional[tuple[Group, Group]], str]]:
  plan_values = [r["plan_filled"] for r in rows if r["plan_filled"] is not None and r["rate"] is not None]
  return [
    (
      "wake", "Wake-up time", lambda r: r["wake"],
      (
        (f"wake by {clock_label(WAKE_EARLY)}", lambda v: v <= WAKE_EARLY),
        (f"wake {clock_label(WAKE_LATE)} or later", lambda v: v >= WAKE_LATE),
      ),
      CAVEAT,
    ),
    (
      "sleep", "Sleep before the day", lambda r: r["sleep"],
      (("slept under 6h30", lambda v: v < 6.5), ("slept 7h30 or more", lambda v: v >= 7.5)),
      SLEEP_CAVEAT,
    ),
    (
      "bedtime_prev", "Last night's bedtime", lambda r: r["bed_prev"],
      (("in bed by midnight", lambda v: v <= 24.0), ("in bed after 01:00", lambda v: v >= 25.0)),
      CAVEAT,
    ),
    (
      "plan_filled", "Hours of the plan grid filled", lambda r: r["plan_filled"],
      _plan_groups(plan_values) if len(plan_values) >= MIN_DAYS else None,
      CAVEAT,
    ),
    (
      "tasks_planned", "Tasks planned", lambda r: float(r["n_tasks"]) if r["n_tasks"] else None,
      (("planned 5 or more", lambda v: v >= 5), ("planned 3 or fewer", lambda v: v <= 3)),
      CAVEAT,
    ),
    (
      "prev_rate", "Yesterday's completion", lambda r: r["prev_rate"],
      (("after a solid day", lambda v: v >= 50), ("after a weaker day", lambda v: v < 50)),
      CAVEAT,
    ),
    (
      "weekend", "Weekend or weekday", lambda r: 1.0 if r["weekend"] else 0.0,
      (("on weekends", lambda v: v == 1.0), ("on weekdays", lambda v: v == 0.0)),
      CAVEAT,
    ),
  ]


def _test_lever(
  key: str,
  label: str,
  pairs: list[tuple[float, float]],
  groups: Optional[tuple[Group, Group]],
  caveat: str,
  rng: random.Random,
) -> Optional[dict[str, Any]]:
  """Run one lever's test (None if it cannot be tested). Tiering happens once every lever has been tested."""
  if len(pairs) < MIN_DAYS:
    return None
  result = permutation_p([x for x, _ in pairs], [y for _, y in pairs], rng)
  if result is None:
    return None
  rho, p = result
  summaries: list[dict[str, Any]] = []
  if groups:
    for group_label, belongs in groups:
      rates = [y for x, y in pairs if belongs(x)]
      summaries.append({"label": group_label, "mean": round(sum(rates) / len(rates), 1) if rates else None, "n": len(rates)})
  contrast = None
  if len(summaries) == 2 and all(g["n"] >= MIN_GROUP for g in summaries):
    first, second = summaries
    contrast = (
      f"{first['label'][0].upper()}{first['label'][1:]}: {first['mean']:.0f}% of tasks done (n={first['n']})"
      f" vs {second['label']}: {second['mean']:.0f}% (n={second['n']})"
    )
  return {
    "lever": key,
    "label": label,
    "rho": round(rho, 2),
    "n": len(pairs),
    "p": round(p, 4),
    "groups": summaries,
    "contrast": contrast,
    "caveat": caveat,
  }


def _plan_size_observation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  buckets: list[tuple[str, Callable[[int], bool]]] = [
    ("2 or fewer", lambda n: n <= 2), ("3", lambda n: n == 3), ("4", lambda n: n == 4), ("5+", lambda n: n >= 5),
  ]
  usable = [r for r in rows if r["n_tasks"] and r["done"] is not None]
  out = []
  for name, belongs in buckets:
    days = [r for r in usable if belongs(r["n_tasks"])]
    if days:
      out.append({
        "bucket": name,
        "days": len(days),
        "avg_planned": round(sum(r["n_tasks"] for r in days) / len(days), 2),
        "avg_done": round(sum(r["done"] for r in days) / len(days), 2),
      })
  return out


def _task_position_observation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  tally: dict[str, list[int]] = {}
  for row in rows:
    for index, done in enumerate(row["tasks"], start=1):
      entry = tally.setdefault(str(index) if index < 5 else "5+", [0, 0])
      entry[1] += 1
      entry[0] += 1 if done else 0
  return [
    {"position": pos, "done": d, "total": t, "rate": round(d / t * 100, 1)}
    for pos, (d, t) in sorted(tally.items(), key=lambda kv: (kv[0] == "5+", kv[0]))
  ]


def compute_levers(rows: list[dict[str, Any]], seed: int) -> dict[str, Any]:
  """Findings (tiered by p-value) and plain observations over a window of day rows."""
  rng = random.Random(seed)
  tested = []
  for key, label, extract, groups, caveat in _lever_specs(rows):
    pairs: list[tuple[float, float]] = []
    for r in rows:
      x = extract(r)
      if r["rate"] is not None and x is not None:
        pairs.append((x, r["rate"]))
    result = _test_lever(key, label, pairs, groups, caveat, rng)
    if result:
      tested.append(result)
  findings = []
  for result in tested:
    tier = tier_for(result["p"], len(tested))
    if tier:
      findings.append({
        **result,
        "tier": tier,
        "tests": len(tested),
        "p_adjusted": round(min(1.0, result["p"] * len(tested)), 4),
      })
  findings.sort(key=lambda f: (f["p"], -abs(f["rho"])))
  return {
    "method_version": METHOD_VERSION,
    "window_days": len(rows),
    "findings": findings,
    "observations": {
      "plan_size": _plan_size_observation(rows),
      "task_position": _task_position_observation(rows),
    },
  }


def build_focus(findings: list[dict[str, Any]], stuck_tasks: list[dict[str, Any]]) -> list[str]:
  """Up to two "try next month" lines from the strongest actionable findings, plus the top stuck task."""
  lines: list[str] = []
  for f in findings:
    if len(lines) >= 2:
      break
    if len(f["groups"]) != 2 or not f["contrast"]:
      continue
    better, worse = f["groups"]
    if better["mean"] is None or worse["mean"] is None or better["mean"] <= worse["mean"]:
      continue
    numbers = f"{better['mean']:.0f}% of tasks done vs {worse['mean']:.0f}%"
    if f["lever"] == "wake":
      lines.append(f"Aim to wake by {clock_label(WAKE_EARLY)} more often: those days had {numbers} on later mornings.")
    elif f["lever"] == "plan_filled":
      lines.append(f"Fill more of the hourly plan grid before the day starts: {better['label']} days had {numbers}.")
    elif f["lever"] == "bedtime_prev":
      lines.append(f"Get to bed by midnight more often: the next day had {numbers} after a late night.")
  if stuck_tasks:
    top = stuck_tasks[0]
    lines.append(
      f"Break \"{top['task']}\" into a first 15-minute step: planned {top['planned']} times, done {top['done']}."
    )
  return lines
