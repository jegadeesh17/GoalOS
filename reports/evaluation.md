# GoalOS — Memory Retrieval Evaluation

Manual 5-query retrieval check using composite ranking (40% semantic, 30% importance, 20% recency, 10% frequency).

| Query ID | Query | Expected Focus | Top Memory | Result | Score |
|----------|-------|----------------|------------|--------|-------|
| Q01 | I delayed deep work because of meetings. What shou... | execution discipline | 1. try to have atleast 1 good work block... | miss | 0.0 |
| Q02 | I keep skipping workouts after office. Give me a r... | health consistency | 1. make sure to get enough sleep and workout. others will follow.... | miss | 0.0 |
| Q03 | I promised to finish SQL practice but missed it. W... | commitment recovery | 1. Remember the goal of start earning money soon.... | miss | 0.0 |
| Q04 | I feel productive but long-term goals are not movi... | goal alignment | i should focus on myself and keep working on myself and prioritize myself first ... | partial | 1.0 |
| Q05 | Weekly review: what pattern is hurting me most?... | pattern detection | 1. very poor focus & efficiency
2. I am not focused or sticking to anything.
3. ... | partial | 1.0 |

**Average retrieval relevance (0–2):** 0.40

## Notes
- Seeded demo memories used when corpus is sparse; replace with your journal import for production eval.
- Regenerate: `python scripts/generate_retrieval_eval.py`