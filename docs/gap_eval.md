# Gap analysis evaluation (synthetic documents)

60 dev and 60 test documents, each with 10 obligations present (50%), mentioned but unmet (25%) or absent (25%) plus filler; German and English. **Synthetic, written by the author:** this measures the matcher on these paraphrases, not on real company policies. Thresholds are tuned on dev only; the table is the unseen test split.

## keyword-rules

Tuned on dev: found >= 0.667, review >= 0.667. Test pairs: 568 (54% truly evidenced). Applicability trigger accuracy (test): 1.00.

| Setting (test split) | Precision of 'found' | Recall of 'found' | F1 | Recall found+review | Unmet items sent to review | Share of all items in review |
|---|---|---|---|---|---|---|
| tuned thresholds | 1.00 | 0.46 | 0.63 | 0.46 | 0.00 | 0.00 |
| always 'gap' | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| always 'found' | 0.54 | 1.00 | 0.70 | 1.00 | 0.00 | 0.00 |

## dense-embeddings

Tuned on dev: found >= 0.866, review >= 0.851. Test pairs: 568 (54% truly evidenced). Applicability trigger accuracy (test): 1.00.

| Setting (test split) | Precision of 'found' | Recall of 'found' | F1 | Recall found+review | Unmet items sent to review | Share of all items in review |
|---|---|---|---|---|---|---|
| tuned thresholds | 0.95 | 0.44 | 0.60 | 0.78 | 0.15 | 0.26 |
| always 'gap' | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| always 'found' | 0.54 | 1.00 | 0.70 | 1.00 | 0.00 | 0.00 |

## What was tried, including what did not work

- **German-only queries (first version):** English passages scored lower than German ones regardless of meaning, so a German distractor ("we have not appointed a DPO") scored about the same as an English genuine passage and no single threshold worked (test recall of found+review was well below target). Fixed by scoring against a German and an English query and keeping the better match.
- **First threshold rule had a bug:** it picked the lowest review threshold instead of the highest, which sent 72 to 75% of all items to review. Corrected, and the objective changed to a precision target (a false 'found' is false assurance).
- **Small-LLM verifier (Qwen2.5-1.5B-Instruct, zero-shot yes/no on the top-3 passages):** worse than plain similarity (test AUC 0.61 vs 0.87), so it was dropped.
- **Limits that remain:** thresholds tuned on one set of wordings recover only 78% of evidenced items on unseen wordings (found+review), so 'gap' means 'no evidence found', not 'proven absent'. A passage that mentions an obligation negatively is the hard case.
