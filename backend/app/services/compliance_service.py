from __future__ import annotations

from app.agents.workflow import run_compliance_workflow
from app.graph.knowledge_graph import ComplianceKnowledgeGraph
from app.models.schemas import ComplianceReport, PolicyRequest


class ComplianceService:
    def __init__(self) -> None:
        self._latest_report: ComplianceReport | None = None
        self._kg = ComplianceKnowledgeGraph()

    async def analyze(self, company_id: str, document_ids: list[str]) -> ComplianceReport:
        report = run_compliance_workflow(company_id=company_id, document_ids=document_ids)
        self._latest_report = report
        self._bootstrap_knowledge_graph()
        return report

    async def latest_report(self) -> ComplianceReport | None:
        return self._latest_report

    async def generate_policy(self, payload: PolicyRequest) -> dict[str, str]:
        header = "Datenschutzerklarung" if payload.policy_type == "privacy_policy" else "Auftragsverarbeitungsvertrag (AVV)"
        content = (
            f"{header}\n\n"
            f"Unternehmen: {payload.company_id}\n"
            "Geltungsbereich: DSGVO, BDSG, EU AI Act\n\n"
            "1. Zweck und Rechtsgrundlagen der Verarbeitung\n"
            "2. Kategorien personenbezogener Daten\n"
            "3. Aufbewahrung und Loschfristen\n"
            "4. Technische und organisatorische Massnahmen\n"
            "5. Rechte betroffener Personen (DSAR)\n\n"
            f"Kontext:\n{payload.context}\n"
        )
        return {"policy_type": payload.policy_type, "content_de": content}

    async def simulate_dsar(self, subject_id: str) -> dict[str, str]:
        return {
            "subject_id": subject_id,
            "status": "completed",
            "result_de": "DSAR-Simulation abgeschlossen: Datenkategorien identifiziert, Losch- und Exportpfade dokumentiert.",
        }

    async def graph_payload(self) -> dict:
        return self._kg.to_visual_payload()

    def _bootstrap_knowledge_graph(self) -> None:
        self._kg.add_entity("HR", "department")
        self._kg.add_entity("Marketing", "department")
        self._kg.add_entity("CRM", "system")
        self._kg.add_entity("Consent", "obligation")
        self._kg.add_relation("HR", "CRM", "processes")
        self._kg.add_relation("Marketing", "CRM", "transfers_to_third_country")
        self._kg.add_relation("CRM", "Consent", "requires_consent")


compliance_service = ComplianceService()
