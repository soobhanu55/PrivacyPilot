"""Hand-labeled evaluation of app.services.ml_service.rerank_candidates.

No paid API required: the cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)
runs locally via sentence-transformers. 20 hand-written GDPR/DSGVO-relevant
queries, each with a set of candidate sentences and one clearly-correct top
answer plus deliberate distractors (some topically close, some unrelated).

Run: python backend/tests/eval_reranker.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ml_service import rerank_candidates

EVAL_SET = [
    {
        "query": "consent retention policy",
        "candidates": [
            "Data retention policy is documented for all consent records.",
            "No consent register exists.",
            "Office kitchen menu update.",
        ],
        "correct": "Data retention policy is documented for all consent records.",
    },
    {
        "query": "right to be forgotten deletion request",
        "candidates": [
            "Users can submit a deletion request that is processed within 30 days.",
            "The company runs quarterly marketing campaigns.",
            "Employee onboarding takes two weeks.",
        ],
        "correct": "Users can submit a deletion request that is processed within 30 days.",
    },
    {
        "query": "third country data transfer safeguards",
        "candidates": [
            "Standard Contractual Clauses are in place for the US-based cloud vendor.",
            "The office has a new coffee machine.",
            "Annual leave requests go through HR.",
        ],
        "correct": "Standard Contractual Clauses are in place for the US-based cloud vendor.",
    },
    {
        "query": "data breach notification timeline",
        "candidates": [
            "Breaches must be reported to the supervisory authority within 72 hours.",
            "The support team responds to emails within 24 hours.",
            "Product releases happen every quarter.",
        ],
        "correct": "Breaches must be reported to the supervisory authority within 72 hours.",
    },
    {
        "query": "data protection officer appointment",
        "candidates": [
            "A DPO was appointed and registered with the local authority.",
            "The company sponsors a football team.",
            "New hires get a laptop on day one.",
        ],
        "correct": "A DPO was appointed and registered with the local authority.",
    },
    {
        "query": "employee personal data processing legal basis",
        "candidates": [
            "Employee payroll data is processed under contractual necessity.",
            "The cafeteria menu changes weekly.",
            "The building has 5 floors.",
        ],
        "correct": "Employee payroll data is processed under contractual necessity.",
    },
    {
        "query": "cookie consent banner requirements",
        "candidates": [
            "The website shows a cookie banner requiring explicit opt-in before tracking.",
            "The mobile app was released last year.",
            "Marketing budget increased by 10%.",
        ],
        "correct": "The website shows a cookie banner requiring explicit opt-in before tracking.",
    },
    {
        "query": "data minimization principle",
        "candidates": [
            "Only fields strictly necessary for the signup form are collected.",
            "The company has offices in three cities.",
            "Customer support is available 24/7.",
        ],
        "correct": "Only fields strictly necessary for the signup form are collected.",
    },
    {
        "query": "vendor data processing agreement",
        "candidates": [
            "A signed DPA is on file with every third-party data processor.",
            "The office relocated last year.",
            "The team uses Slack for communication.",
        ],
        "correct": "A signed DPA is on file with every third-party data processor.",
    },
    {
        "query": "special category health data safeguards",
        "candidates": [
            "Health data is encrypted at rest and access-logged per request.",
            "The company sells software subscriptions.",
            "Sales grew 15% last quarter.",
        ],
        "correct": "Health data is encrypted at rest and access-logged per request.",
    },
    {
        "query": "data subject access request process",
        "candidates": [
            "Access requests are fulfilled within one month via a self-service portal.",
            "The office dress code is business casual.",
            "The company was founded in 2015.",
        ],
        "correct": "Access requests are fulfilled within one month via a self-service portal.",
    },
    {
        "query": "privacy by design implementation",
        "candidates": [
            "New features undergo a privacy impact assessment before launch.",
            "The team runs a weekly standup meeting.",
            "The office has free parking.",
        ],
        "correct": "New features undergo a privacy impact assessment before launch.",
    },
    {
        "query": "cross-border data transfer to non-adequate country",
        "candidates": [
            "A transfer impact assessment was completed before enabling the integration.",
            "Employees get 25 vacation days per year.",
            "The company logo was redesigned.",
        ],
        "correct": "A transfer impact assessment was completed before enabling the integration.",
    },
    {
        "query": "data retention schedule for HR records",
        "candidates": [
            "HR records are deleted automatically after the legally required retention period.",
            "The company hosts an annual holiday party.",
            "The product roadmap is public.",
        ],
        "correct": "HR records are deleted automatically after the legally required retention period.",
    },
    {
        "query": "AI system risk classification under EU AI Act",
        "candidates": [
            "The internal scoring tool was classified as limited-risk under Article 6.",
            "The company uses a ticketing system for support.",
            "Revenue is reported quarterly to investors.",
        ],
        "correct": "The internal scoring tool was classified as limited-risk under Article 6.",
    },
    {
        "query": "encryption of personal data at rest",
        "candidates": [
            "All customer databases use AES-256 encryption at rest.",
            "The team prefers async communication.",
            "The office is on the fifth floor.",
        ],
        "correct": "All customer databases use AES-256 encryption at rest.",
    },
    {
        "query": "processing records under Article 30",
        "candidates": [
            "A record of processing activities is maintained and reviewed annually.",
            "The company sponsors local sports events.",
            "The website was redesigned last month.",
        ],
        "correct": "A record of processing activities is maintained and reviewed annually.",
    },
    {
        "query": "child data protection age verification",
        "candidates": [
            "Age verification is required before account creation for users under 16.",
            "The company has a bring-your-own-device policy.",
            "The support hotline operates in three languages.",
        ],
        "correct": "Age verification is required before account creation for users under 16.",
    },
    {
        "query": "supervisory authority complaint handling",
        "candidates": [
            "Complaints from the data protection authority are logged and answered within statutory deadlines.",
            "The company has a referral bonus program.",
            "The office kitchen was renovated.",
        ],
        "correct": "Complaints from the data protection authority are logged and answered within statutory deadlines.",
    },
    {
        "query": "biometric data processing consent",
        "candidates": [
            "Explicit consent is captured before enabling face-recognition login.",
            "The company issues quarterly newsletters.",
            "The parking lot was resurfaced.",
        ],
        "correct": "Explicit consent is captured before enabling face-recognition login.",
    },
]


def main() -> None:
    hits_at_1 = 0
    for item in EVAL_SET:
        ranked = rerank_candidates(item["query"], item["candidates"], top_k=len(item["candidates"]))
        top_pick = ranked[0]["text"]
        is_hit = top_pick == item["correct"]
        hits_at_1 += int(is_hit)
        print(f"{'OK ' if is_hit else 'MISS'} | {item['query'][:50]:50s} | top={top_pick[:60]}")

    n = len(EVAL_SET)
    print(f"\nHit@1: {hits_at_1}/{n} ({100 * hits_at_1 / n:.1f}%)")


if __name__ == "__main__":
    main()
