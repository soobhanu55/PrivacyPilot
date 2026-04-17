from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from app.models.schemas import AuditLogEntry, ComplianceReport, RiskItem
from app.services.audit_service import audit_service


class AgentState(TypedDict, total=False):
    workflow_id: str
    company_id: str
    document_ids: list[str]
    extracted_facts: list[str]
    data_flows: list[str]
    risks: list[RiskItem]
    recommendations: list[str]
    report: ComplianceReport


def _log(agent: str, workflow_id: str, input_summary: str, output_summary: str) -> None:
    audit_service.log(
        AuditLogEntry(
            workflow_id=workflow_id,
            agent=agent,
            input_summary=input_summary,
            output_summary=output_summary,
            model="hybrid-rules+llm",
            trace={"timestamp": datetime.now(UTC).isoformat()},
        )
    )


def document_ingestion_agent(state: AgentState) -> AgentState:
    facts = [f"Extrahierter Kontext aus {doc_id}" for doc_id in state.get("document_ids", [])]
    _log("DocumentIngestionAgent", state["workflow_id"], str(state.get("document_ids")), f"{len(facts)} facts")
    return {**state, "extracted_facts": facts}


def data_flow_mapping_agent(state: AgentState) -> AgentState:
    flows = [f"{fact} -> CRM-System" for fact in state.get("extracted_facts", [])]
    _log("DataFlowMappingAgent", state["workflow_id"], f"{len(state.get('extracted_facts', []))} facts", f"{len(flows)} flows")
    return {**state, "data_flows": flows}


def risk_classification_agent(state: AgentState) -> AgentState:
    risks: list[RiskItem] = [
        RiskItem(
            id=f"RISK-{i+1}",
            title=title,
            regulation=reg,
            severity=severity,
            explanation_de=exp,
            recommendation_de=rec,
            source_refs=["DSGVO Art. 5", "EU AI Act Art. 9"],
        )
        for i, (title, reg, severity, exp, rec) in enumerate(
            [
                ("Fehlendes Consent-Tracking", "DSGVO", "High", "Einwilligungen sind nicht systematisch dokumentiert.", "Fuhren Sie ein zentrales Consent-Register ein."),
                ("Keine Aufbewahrungsrichtlinie", "BDSG", "Medium", "Loschfristen sind nicht fur HR- und Marketingdaten definiert.", "Definieren Sie Datenaufbewahrung je Datentyp."),
                ("Unsichere Drittlandubertragung", "DSGVO/NIS2", "High", "Datenubertragung ohne klaren Transfer-Mechanismus erkannt.", "Prufen Sie SCCs und Transfer Impact Assessments."),
            ]
        )
    ]
    _log("RiskClassificationAgent", state["workflow_id"], str(state.get("data_flows")), f"{len(risks)} risks")
    return {**state, "risks": risks}


def recommendation_agent(state: AgentState) -> AgentState:
    recommendations = [r.recommendation_de for r in state.get("risks", [])]
    score = max(0, 100 - (len([r for r in state.get("risks", []) if r.severity == "High"]) * 25) - 10)
    report = ComplianceReport(
        company_id=state["company_id"],
        compliance_score=score,
        summary_de="Automatisierte Bewertung mit Fokus auf DSGVO, BDSG, EU AI Act und NIS2.",
        risks=state.get("risks", []),
        next_actions_de=recommendations,
    )
    _log("ComplianceRecommendationAgent", state["workflow_id"], f"{len(state.get('risks', []))} risks", f"score={score}")
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


def run_compliance_workflow(company_id: str, document_ids: list[str]) -> ComplianceReport:
    state = AgentState(workflow_id=str(uuid4()), company_id=company_id, document_ids=document_ids)
    result = compiled_workflow.invoke(state)
    return result["report"]
