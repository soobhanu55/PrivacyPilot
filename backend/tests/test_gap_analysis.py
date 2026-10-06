import pytest

from app.services import gap_analysis as ga
from app.services.gap_analysis import Chunk, KeywordScorer, Thresholds
from tests.fakes import FixedScorer

BY_ID = {o.id: o for o in ga.OBLIGATIONS}


def chunks(*texts):
    return [Chunk(t, document_id=f"d{i}", filename=f"doc{i}.txt") for i, t in enumerate(texts)]


# ---- chunking ---------------------------------------------------------------

def test_split_into_chunks_one_per_paragraph_and_skips_blank():
    out = ga.split_into_chunks("Erster Absatz.\n\n\n\nZweiter Absatz hier.\n\n   \n", "d1", "a.txt")
    assert [c.text for c in out] == ["Erster Absatz.", "Zweiter Absatz hier."]
    assert all(c.document_id == "d1" and c.filename == "a.txt" for c in out)


def test_split_into_chunks_cuts_long_paragraphs_with_overlap():
    words = [f"w{i}" for i in range(300)]
    out = ga.split_into_chunks(" ".join(words), size=100, overlap=20)
    assert len(out) > 2 and all(len(c.text.split()) <= 100 for c in out)
    assert out[0].text.split()[80:] == out[1].text.split()[:20]


# ---- keyword scorer ---------------------------------------------------------

def test_keyword_scorer_scores_matching_text_high_and_unrelated_zero():
    ob = BY_ID["dsgvo-33"]
    good = chunks("Bei einer Datenpanne melden wir die Verletzung innerhalb von 72 Stunden an die Aufsichtsbehörde.")
    bad = chunks("Die Kantine bietet täglich zwei Gerichte an.")
    assert KeywordScorer().best_match(ob, good)[0] >= 0.75
    assert KeywordScorer().best_match(ob, bad) == (0.0, -1)


# ---- thresholds / status ------------------------------------------------------

def test_analyze_maps_scores_to_found_review_gap_with_evidence_only_when_not_gap():
    scorer = FixedScorer({"dsgvo-30": 0.9, "dsgvo-37": 0.5, "dsgvo-17": 0.1}, Thresholds(found=0.8, review=0.4))
    by = {f.obligation.id: f for f in ga.analyze(chunks("irgendein Text"), scorer)}
    assert (by["dsgvo-30"].status, by["dsgvo-37"].status, by["dsgvo-17"].status) == ("found", "review", "gap")
    assert by["dsgvo-30"].evidence is not None and by["dsgvo-37"].evidence is not None
    assert by["dsgvo-17"].evidence is None


# ---- applicability ------------------------------------------------------------

def applicable(ob_id, *texts):
    return ga.applies(BY_ID[ob_id], chunks(*texts))


def test_third_country_obligation_applies_only_with_a_matching_vendor_or_phrase():
    assert applicable("dsgvo-46", "Wir nutzen Zoom für Meetings.")
    assert applicable("dsgvo-46", "Daten gehen in ein Drittland.")
    assert not applicable("dsgvo-46", "Wir nutzen DATEV und Hetzner, alles in Deutschland.")


def test_ai_obligation_applies_only_when_ai_is_mentioned_as_a_word():
    assert applicable("aiact-14", "Unser Chatbot beantwortet Fragen.")
    assert applicable("aiact-14", "We use machine learning for scoring.")
    assert not applicable("aiact-14", "Wir verschicken E-Mails und führen Mails-Archive.")  # 'ai' inside other words


def test_obligations_without_a_trigger_always_apply():
    assert applicable("dsgvo-30", "Beliebiger Text")


# ---- score -------------------------------------------------------------------

def finding(ob_id, status, applicable=True):
    return ga.Finding(BY_ID[ob_id], applicable, status, score=0.0)


def test_compliance_score_hand_calculated():
    # dsgvo-33 is High (weight 3), dsgvo-30 is Medium (weight 2): 3 found + 2 gap -> 3/5 = 60
    assert ga.compliance_score([finding("dsgvo-33", "found"), finding("dsgvo-30", "gap")]) == 60
    # a 'review' counts half: 3*0.5 / 3 = 50
    assert ga.compliance_score([finding("dsgvo-33", "review")]) == 50
    assert ga.compliance_score([finding("dsgvo-33", "found"), finding("dsgvo-30", "found")]) == 100
    assert ga.compliance_score([finding("dsgvo-33", "gap")]) == 0


def test_compliance_score_ignores_not_applicable_obligations():
    findings = [finding("dsgvo-33", "found"), finding("dsgvo-46", "not_applicable", applicable=False)]
    assert ga.compliance_score(findings) == 100
    assert ga.compliance_score([finding("dsgvo-46", "not_applicable", applicable=False)]) == 100


# ---- risk items ---------------------------------------------------------------

def test_risk_items_skip_found_and_cite_the_real_article_title():
    gap_nis2 = finding("nis2-21", "gap")
    items = ga.to_risk_items([finding("dsgvo-30", "found"), gap_nis2, finding("dsgvo-46", "not_applicable", False)])
    assert [i.id for i in items] == ["nis2-21"]
    assert items[0].severity == "High"
    assert items[0].source_refs == ["NIS2 Art. 21: Cybersecurity risk-management measures"]


def test_review_items_are_downgraded_and_quote_the_passage():
    f = ga.Finding(BY_ID["dsgvo-33"], True, "review", 0.86, Chunk("Wir melden Pannen schnell.", "d1", "policy.txt"))
    item = ga.to_risk_items([f])[0]
    assert item.severity == "Medium"  # High obligation, unclear evidence
    assert "Wir melden Pannen schnell." in item.explanation_de and "policy.txt" in item.explanation_de


# ---- vendors ------------------------------------------------------------------

def test_detect_vendors_reports_each_once_with_third_country_flag():
    flows = ga.detect_vendors(chunks("Wir nutzen Microsoft 365 und SAP.", "Auch Microsoft Teams und HubSpot."))
    by = {f["vendor"]: f for f in flows}
    assert set(by) == {"Microsoft", "SAP", "HubSpot"}
    assert by["Microsoft"]["third_country"] is True and by["SAP"]["third_country"] is False
    assert len(flows) == 3


def test_default_scorer_falls_back_to_keywords_without_a_model(monkeypatch):
    import app.rag.hybrid_retriever as hr

    def boom(self, text):
        raise ImportError("sentence-transformers not installed")

    monkeypatch.setattr(hr.E5Embedder, "encode_query", boom)
    assert isinstance(ga.default_scorer(), KeywordScorer)


@pytest.mark.parametrize("ob", ga.OBLIGATIONS, ids=lambda o: o.id)
def test_every_obligation_is_well_formed(ob):
    assert ob.id in ga.QUERIES_EN and len(ob.keywords) >= 3
    assert ob.severity in ga.WEIGHT and ob.query and ob.recommendation_de
