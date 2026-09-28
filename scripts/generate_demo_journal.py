"""Generate data/demo_seed.csv: a FICTIONAL journal for the public demo.

Usage: python scripts/generate_demo_journal.py data/demo_seed.csv

Persona: Alex Chen, backend engineer moving into ML engineering, building a side
project (a recipe-search API) and training for a half marathon. Nothing here is
derived from any real journal. Output mirrors the real notebook CSV format:
Date (D/M/YY), Gratitude, Plan ("H-H activity" lines), Tasks ("N. text (tick)/(X)"),
Review, Takeaway, Awake ("H:MM AM - H:MM PM").
"""
import csv
import random
import sys
from datetime import date, timedelta

rng = random.Random(20260928)
START, END = date(2026, 8, 17), date(2026, 9, 27)

GRATITUDE = [
    "I am grateful for a quiet morning to think.",
    "I am grateful for my sister checking in on me.",
    "I am grateful for a body that can run again.",
    "I am grateful for good coffee and a clear desk.",
    "I am grateful for a mentor who answers my questions.",
    "I am grateful for the rain cooling the city down.",
    "I am grateful for a paycheck that covers rent and savings.",
    "I am grateful for friends who keep me honest.",
    "I am grateful for the open-source maintainers whose code I use.",
    "I am grateful for a long walk after dinner.",
    "I am grateful for finally sleeping eight hours.",
    "I am grateful for small wins that add up.",
    "I am grateful for my team covering for me on a slow day.",
    "I am grateful for the library being open late.",
]

# (task text, base probability of completion)
TASK_POOL = [
    ("Ship recipe-search API endpoint", 0.6),
    ("Write unit tests for the ranking module", 0.65),
    ("Read one chapter of Designing ML Systems", 0.7),
    ("Solve 2 LeetCode mediums", 0.6),
    ("Run 5 km", 0.65),
    ("Stretch 15 min", 0.55),
    ("Apply to 2 ML engineer roles", 0.5),
    ("Review embeddings notebook", 0.6),
    ("Cook dinner instead of ordering", 0.6),
    ("Call parents", 0.8),
    ("Log expenses", 0.55),
    ("Write blog draft on hybrid search", 0.45),
    ("Clean the apartment", 0.6),
    ("Prepare for mock interview", 0.6),
]
STUCK_TASK = ("Update resume with side-project results", 0.15)  # recurring miss -> distraction memory

WORK_BLOCKS = ["Work: payments service tickets", "Work: on-call + code review", "Work: API migration",
               "Work: sprint planning, standup", "Work: data pipeline fix"]
LEARN_BLOCKS = ["Designing ML Systems reading", "LeetCode practice", "Embeddings notebook",
                "Mock interview prep", "Fast.ai lesson"]
PROJECT_BLOCKS = ["Side project: ranking module", "Side project: API endpoints",
                  "Side project: tests + CI", "Side project: deploy to Cloud Run", "Blog draft"]
LOOSE_BLOCKS = ["YouTube rabbit hole", "Phone scrolling, lost track", "Chill, TV", "Nap"]

GOOD_REVIEWS = [
    "Deep work block before lunch went well, shipped the endpoint I planned.",
    "Kept the phone in another room and it made a real difference.",
    "Good energy all day. The run in the morning set the tone.",
    "Finished what I planned and still had time to read.",
    "Mock interview felt smoother, system design answers are getting clearer.",
    "Tests caught a ranking bug before it shipped. Worth the time.",
]
MIXED_REVIEWS = [
    "Work went fine, but not the side project; I kept postponing it.",
    "Got the run in, however the evening disappeared into YouTube.",
    "Productive morning, but not a single job application again.",
    "Learning block was solid, however I skipped dinner prep and ordered in.",
    "Some progress, but the resume slipped again. I keep avoiding it.",
]
BAD_REVIEWS = [
    "Slept late, felt foggy, and scrolled most of the afternoon.",
    "On-call pages broke the day into pieces. Very little focus.",
    "Low energy day. Did the minimum at work and nothing after.",
    "Overplanned again. Too many tasks, finished almost none.",
]
COMMITMENTS = [
    "Start the day with the hardest task before opening Slack.",
    "Keep the phone out of the bedroom tonight.",
    "Plan only three tasks tomorrow.",
    "Book two job applications into the calendar like meetings.",
    "Run before work on Tuesday, Thursday and Saturday.",
    "Finish the resume update before touching new features.",
]
LESSONS = [
    "Energy follows sleep; late nights cost the next afternoon.",
    "Small daily progress on the side project beats weekend marathons.",
    "Avoided tasks grow heavier the longer they sit.",
    "A written plan the night before makes the morning easy.",
    "Movement first thing clears my head better than coffee.",
    "Saying no to extra work keeps room for what matters.",
]


def fmt_clock(h: float) -> str:
    hh, mm = int(h) % 24, int(round((h % 1) * 60))
    suffix = "AM" if hh < 12 else "PM"
    h12 = hh % 12 or 12
    return f"{h12}:{mm:02d} {suffix}"


def h12(h: int) -> int:
    return h % 12 or 12


def day_row(d: date, i: int) -> dict:
    week = (d - START).days // 7
    # Story arc: slow start, strong middle, a dip in week 4 (on-call), recovery after.
    mood = {0: 0.45, 1: 0.6, 2: 0.72, 3: 0.4, 4: 0.68, 5: 0.75}.get(week, 0.6)
    weekend = d.weekday() >= 5
    wake = rng.choice([6.5, 7.0, 7.0, 7.5, 8.0]) if mood > 0.5 else rng.choice([7.5, 8.0, 8.5, 9.0])
    sleep = rng.choice([22.5, 23.0, 23.0, 23.5]) if mood > 0.5 else rng.choice([23.5, 24.0, 24.5])
    awake = f"{fmt_clock(wake)} - {fmt_clock(sleep)}"
    if i % 11 == 5:  # occasionally forgot to write the AWAKE line
        awake = ""

    start = int(wake)
    blocks, h = [], start
    while h + 2 <= 22:
        if h == start:
            act = rng.choice(["Run, shower, breakfast", "Walk, breakfast", "Stretch, coffee, plan day"])
        elif weekend:
            act = rng.choice(PROJECT_BLOCKS + LEARN_BLOCKS + ["Groceries, cook", "Friends, lunch"]
                             + (LOOSE_BLOCKS if rng.random() > mood else []))
        elif h < 18:
            act = rng.choice(WORK_BLOCKS) if rng.random() < 0.8 else "Lunch, walk"
        else:
            act = rng.choice(PROJECT_BLOCKS + LEARN_BLOCKS) if rng.random() < mood else rng.choice(LOOSE_BLOCKS)
        blocks.append(f"{h12(h)}-{h12(h + 2)} {act}")
        h += 2

    n = rng.choice([3, 4, 4, 5])
    picked = rng.sample(TASK_POOL, n)
    if week >= 1 and i % 4 == 1:
        picked[-1] = STUCK_TASK
    task_lines, done_count = [], 0
    for k, (text, p) in enumerate(picked, 1):
        done = rng.random() < min(0.95, p + (mood - 0.55))
        done_count += done
        task_lines.append(f"{k}. {text} ({'tick' if done else 'X'})")

    # The review follows how the day actually went.
    rate = done_count / len(picked)
    if rate >= 0.75:
        review = rng.choice(GOOD_REVIEWS)
    elif rate >= 0.4:
        stuck_missed = STUCK_TASK in picked and "(X)" in task_lines[picked.index(STUCK_TASK)]
        pool = [r for r in MIXED_REVIEWS if ("resume" in r) == stuck_missed] or MIXED_REVIEWS
        review = rng.choice(pool)
    else:
        review = rng.choice(BAD_REVIEWS)
    takeaway = rng.choice(COMMITMENTS) if rng.random() < 0.5 else rng.choice(LESSONS)

    return {
        "Date": f"{d.day}/{d.month}/{d.strftime('%y')}",
        "Gratitude": rng.choice(GRATITUDE),
        "Plan": "\n".join(blocks),
        "Tasks": "\n".join(task_lines),
        "Review": review,
        "Takeaway": takeaway,
        "Awake": awake,
    }


def main(out_path: str) -> None:
    rows, d, i = [], START, 0
    while d <= END:
        rows.append(day_row(d, i))
        d += timedelta(days=1)
        i += 1
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Date", "Gratitude", "Plan", "Tasks", "Review", "Takeaway", "Awake"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} fictional days to {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
