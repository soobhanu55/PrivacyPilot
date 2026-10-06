"""End-to-end workflow tests. The old test only asserted that a report with >=1 risk came back, which a hardcoded
list of three findings also satisfied. These tests check that the result depends on what the documents say."""
import asyncio

import pytest

from app.agents.workflow import run_compliance_workflow
from app.services.compliance_service import ComplianceService
from app.services.gap_analysis import KeywordScorer
from app.services.persistence_service import PersistenceService

DPO_DOC = (
    "Wir haben einen externen Datenschutzbeauftragten benannt und der Aufsichtsbehörde gemeldet.\n\n"
    "Seine Kontaktdaten stehen in der Datenschutzerklärung und sind im Intranet erreichbar."
)
OTHER_DOC = "Die Kantine bietet täglich zwei Gerichte an.\n\nUrlaub wird im Portal beantragt."
VENDOR_DOC = "Wir nutzen Microsoft 365 und Zoom für die Zusammenarbeit."


def docs(tmp_path, **files):
    out = []
    for i, (name, text) in enumerate(files.items()):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        out.append({"document_id": f"id{i}", "filename": name, "path": str(p)})
    return out


def run(documents):
    return run_compliance_workflow("acme", documents, scorer=KeywordScorer())


def risk_ids(state):
    return {r.id for r in state["report"].risks}


def test_report_depends_on_the_document_content(tmp_path):
    with_dpo = run(docs(tmp_path, **{"a.txt": DPO_DOC}))
    without = run(docs(tmp_path, **{"b.txt": OTHER_DOC}))
    assert "dsgvo-37" not in risk_ids(with_dpo)  # the DPO paragraph is evidence
    assert "dsgvo-37" in risk_ids(without)       # absent from the unrelated document
    assert with_dpo["report"].compliance_score > without["report"].compliance_score
    assert risk_ids(with_dpo) != risk_ids(without)  # the old stub returned the same three findings for any input


def test_report_records_method_documents_and_applicability(tmp_path):
    state = run(docs(tmp_path, **{"plain.txt": OTHER_DOC}))
    report = state["report"]
    assert report.method == "keyword-rules" and report.documents_analyzed == ["plain.txt"]
    assert {"dsgvo-46", "aiact-14"} <= set(report.not_applicable)  # no vendor and no AI mentioned
    assert "keine Rechtsberatung" in report.summary_de


def test_vendors_found_in_documents_drive_third_country_applicability(tmp_path):
    state = run(docs(tmp_path, **{"vendors.txt": VENDOR_DOC}))
    assert {f["vendor"] for f in state["report"].data_flows} == {"Microsoft", "Zoom"}
    assert "dsgvo-46" in risk_ids(state)  # US vendors named, no transfer safeguards documented


def test_unreadable_files_are_skipped_without_aborting(tmp_path):
    documents = docs(tmp_path, **{"ok.txt": DPO_DOC, "weird.xyz": "data"})
    state = run(documents)
    assert len(state["skipped"]) == 1 and "weird.xyz" in state["skipped"][0]
    assert "dsgvo-37" not in risk_ids(state)  # the readable document was still analysed


def test_no_documents_yields_score_zero_and_says_so():
    report = run([])["report"]
    assert report.compliance_score == 0 and report.summary_de.startswith("Keine lesbaren Dokumente")


# ---- tenant isolation -----------------------------------------------------------

def test_reports_and_graphs_are_kept_per_tenant(tmp_path):
    service = ComplianceService()
    documents = docs(tmp_path, **{"v.txt": VENDOR_DOC})
    asyncio.run(service.analyze("tenant-a", "acme", documents, scorer=KeywordScorer()))
    assert asyncio.run(service.latest_report("tenant-a")) is not None
    assert asyncio.run(service.latest_report("tenant-b")) is None  # the old global slot would have returned A's report
    assert asyncio.run(service.graph_payload("tenant-b")) == {"nodes": [], "edges": []}
    graph = asyncio.run(service.graph_payload("tenant-a"))
    assert any(n["id"] == "Zoom" and n["third_country"] for n in graph["nodes"])
    assert any(e["relation"] == "transfers_to_third_country" for e in graph["edges"])


class _Result:
    def scalars(self):
        return self

    def all(self):
        return []


class _CapturingSession:
    async def execute(self, stmt):
        self.stmt = stmt
        return _Result()


def test_document_lookup_is_always_filtered_by_tenant():
    session = _CapturingSession()
    asyncio.run(PersistenceService().get_documents(session, "tenant-a", ["doc-1", "doc-2"]))
    sql = str(session.stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant_key = 'tenant-a'" in sql and "'doc-1'" in sql
