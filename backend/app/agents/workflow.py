"""LangGraph workflow: read the uploaded documents, find vendors/data flows, match each obligation to evidence in
the text, and assemble a scored report. Every step reads real input; nothing is hardcoded per run.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from app.models.schemas import AuditLogEntry, ComplianceReport, RiskItem
from app.services import gap_analysis
from app.services.audit_service import audit_service
from app.services.document_reader import read_document
from app.services.gap_analysis import Chunk, Finding, Scorer


class AgentState(TypedDict, total=False):
    workflow_id: str
    company_id: str
    documents: list[dict[str, str]]  # document_id, filename, path
    scorer: Scorer | None
    chunks: list[Chunk]
    skipped: list[str]
    data_flows: list[dict[str, Any]]
    findings: list[Finding]
    method: str
    risks: list[RiskItem]
    recommendations: list[str]
    report: ComplianceReport


def _log(agent: str, workflow_id: str, input_summary: str, output_summary: str, model: str = "rules") -> None:
    audit_service.log(AuditLogEntry(
        workflow_id=workflow_id, agent=agent, input_summary=input_summary, output_summary=output_summary,
        model=model, trace={"timestamp": datetime.now(UTC).isoformat()},
    ))


def document_ingestion_agent(state: AgentState) -> AgentState:
    chunks: list[Chunk] = []
    skipped: list[str] = []
    for doc in state.get("documents", []):
        try:
            text = read_document(Path(doc["path"]))
        except Exception as exc:  # unreadable or unsupported file: record it, keep analysing the rest
            skipped.append(f"{doc['filename']}: {exc}")
            continue
        chunks += gap_analysis.split_into_chunks(text, doc["document_id"], doc["filename"])
    _log("DocumentIngestionAgent", state["workflow_id"], f"{len(state.get('documents', []))} documents",
         f"{len(chunks)} passages, {len(skipped)} skipped")
    return {**state, "chunks": chunks, "skipped": skipped}


def data_flow_mapping_agent(state: AgentState) -> AgentState:
    flows = gap_analysis.detect_vendors(state.get("chunks", []))
    _log("DataFlowMappingAgent", state["workflow_id"], f"{len(state.get('chunks', []))} passages",
         f"{len(flows)} vendors ({sum(f['third_country'] for f in flows)} outside the EU/EEA)")
    return {**state, "data_flows": flows}


def risk_classification_agent(state: AgentState) -> AgentState:
    scorer = state.get("scorer") or gap_analysis.default_scorer()
    findings = gap_analysis.analyze(state.get("chunks", []), scorer)
    risks = gap_analysis.to_risk_items(findings)
    _log("RiskClassificationAgent", state["workflow_id"], f"{len(state.get('chunks', []))} passages",
         f"{len(risks)} open items of {sum(f.applicable for f in findings)} applicable obligations", model=scorer.name)
    return {**state, "findings": findings, "risks": risks, "method": scorer.name}


def recommendation_agent(state: AgentState) -> AgentState:
    findings, risks = state.get("findings", []), state.get("risks", [])
    score = gap_analysis.compliance_score(findings) if state.get("chunks") else 0
    applicable = [f for f in findings if f.applicable]
    found = sum(f.status == "found" for f in applicable)
    review = sum(f.status == "review" for f in applicable)
    summary = (f"{found} von {len(applicable)} anwendbaren Pflichten sind in den Dokumenten belegt, {review} sind unklar und "
               f"{len(applicable) - found - review} ohne gefundenen Nachweis (Methode: {state.get('method')}). "
               "Heuristische Auswertung als Entscheidungshilfe, keine Rechtsberatung.")
    if not state.get("chunks"):
        summary = "Keine lesbaren Dokumente zum Analysieren. " + summary
    recommendations = [r.recommendation_de for r in risks]
    report = ComplianceReport(
        company_id=state["company_id"], compliance_score=score, summary_de=summary, risks=risks,
        next_actions_de=recommendations, method=state.get("method", ""),
        documents_analyzed=[d["filename"] for d in state.get("documents", [])],
        not_applicable=[f.obligation.id for f in findings if not f.applicable],
        data_flows=state.get("data_flows", []),
    )
    _log("ComplianceRecommendationAgent", state["workflow_id"], f"{len(risks)} open items", f"score={score}")
    return {**state, "recommendations": recommendations, "report": report}


def audit_trail_agent(state: AgentState) -> AgentState:
    _log("AuditTrailAgent", state["workflow_id"], "Assemble trace", "Audit trace finalized")
    return state


workflow = StateGraph(AgentState)
workflow.add_node("ingestion", document_ingestion_agent)
workflow.add_node("dataflow", data_flow_mapping_agent)
workflow.add_node("risk", risk_classification_agent)
workflow.add_node("recommendation", recommendation_agent)
workflow.add_node("audit", audit_trail_agent)
workflow.set_entry_point("ingestion")
workflow.add_edge("ingestion", "dataflow")
workflow.add_edge("dataflow", "risk")
workflow.add_edge("risk", "recommendation")
workflow.add_edge("recommendation", "audit")
workflow.add_edge("audit", END)
compiled_workflow = workflow.compile()


def run_compliance_workflow(company_id: str, documents: list[dict[str, str]], scorer: Scorer | None = None) -> AgentState:
    """documents: [{"document_id", "filename", "path"}]. Returns the final state (report, findings, data_flows)."""
    state = AgentState(workflow_id=str(uuid4()), company_id=company_id, documents=documents, scorer=scorer)
    return compiled_workflow.invoke(state)
