# GoalOS Lightweight Evaluation Notes

## Purpose
Provide a fast, repeatable quality check for retrieval-backed coaching when dataset size is limited.

## Dataset
- Start with 20-30 representative prompts.
- Include at least:
  - 8 daily execution prompts
  - 6 habit/health prompts
  - 6 reflection/weekly prompts
  - 4 long-term alignment prompts

## Rubric
- **Retrieval relevance (0-2)**
  - 0 = irrelevant/no useful memory
  - 1 = partially relevant memory
  - 2 = clearly relevant memory used in advice
- **Response usefulness (1-5)**
  - 1 = generic/unactionable
  - 3 = somewhat actionable
  - 5 = specific, prioritized, and realistic
- **Hallucination flag**
  - yes = fabricated personal history or unsupported claims
  - no = grounded in context/memory

## Success Baseline (Initial)
- Average retrieval relevance >= 1.3
- Average response usefulness >= 3.8
- Hallucination rate <= 10%

## How to Run
1. Fill `goalos_eval_template.csv` row-by-row.
2. Execute prompts manually through app chat or coaching endpoints.
3. Score each row immediately after response.
4. Summarize averages and failure modes.

## Reporting Format
- Sample size
- Avg retrieval relevance
- Avg response usefulness
- Hallucination rate
- Top 3 failure patterns
- Fixes applied (prompt/retrieval/data)
