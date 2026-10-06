"""Route-level checks for /analyze-compliance and /risk-report, calling the handlers with a fake DB session
(the real stack needs Postgres). They verify what the handler does with what the DB returns; that the DB query
itself is tenant-filtered is covered in test_workflow.py."""
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import routes
from app.models.schemas import AnalyzeRequest
from app.services import gap_analysis
from app.services.compliance_service import compliance_service


class FakeSession:
    def __init__(self, rows):
        self.rows, self.added = rows, []

    async def execute(self, stmt):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self.rows),
                               scalar_one_or_none=lambda: None)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass


def doc_row(tmp_path, doc_id, text):
    p = tmp_path / f"{doc_id}.txt"
    p.write_text(text, encoding="utf-8")
    return SimpleNamespace(document_id=doc_id, filename=p.name, storage_path=str(p))


@pytest.fixture(autouse=True)
def keyword_scorer(monkeypatch):
    monkeypatch.setattr(gap_analysis, "default_scorer", lambda: gap_analysis.KeywordScorer())
    compliance_service._latest_report.clear()
    compliance_service._kg.clear()


def analyze(payload, session, tenant="tenant-a"):
    return asyncio.run(routes.analyze_compliance(payload, tenant_key=tenant, _=None, session=session))


def test_analyze_reads_the_uploaded_documents(tmp_path):
    rows = [doc_row(tmp_path, "d1", "Wir haben einen Datenschutzbeauftragten benannt und seine Kontaktdaten veröffentlicht.")]
    report = analyze(AnalyzeRequest(company_id="acme", document_ids=["d1"]), FakeSession(rows))
    assert report["documents_analyzed"] == ["d1.txt"] and report["method"] == "keyword-rules"
    assert "dsgvo-37" not in {r["id"] for r in report["risks"]}


def test_ids_the_db_does_not_return_for_this_tenant_are_404(tmp_path):
    rows = [doc_row(tmp_path, "d1", "irgendein Text")]  # the tenant owns d1 only
    with pytest.raises(HTTPException) as exc:
        analyze(AnalyzeRequest(company_id="acme", document_ids=["d1", "someone-elses-doc"]), FakeSession(rows))
    assert exc.value.status_code == 404 and "someone-elses-doc" in exc.value.detail


def test_risk_report_never_falls_back_to_another_tenants_report(tmp_path):
    analyze(AnalyzeRequest(company_id="acme", document_ids=["d1"]), FakeSession([doc_row(tmp_path, "d1", "Text")]), tenant="tenant-a")
    other = asyncio.run(routes.risk_report(tenant_key="tenant-b", _=None, session=FakeSession([])))
    assert other == {"report": None}


def test_stub_endpoints_say_what_they_are():
    from app.models.schemas import PolicyRequest

    policy = asyncio.run(compliance_service.generate_policy(PolicyRequest(company_id="acme", policy_type="dpa", context="x")))
    assert "Vorlage" in policy["note_de"]
    dsar = asyncio.run(compliance_service.simulate_dsar("subject-1"))
    assert "Platzhalter" in dsar["result_de"]
