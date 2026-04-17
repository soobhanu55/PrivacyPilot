from app.agents.workflow import run_compliance_workflow


def test_workflow_generates_report() -> None:
    report = run_compliance_workflow(company_id="demo-company", document_ids=["doc1", "doc2"])
    assert report.company_id == "demo-company"
    assert 0 <= report.compliance_score <= 100
    assert len(report.risks) >= 1
