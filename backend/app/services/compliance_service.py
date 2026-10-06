from __future__ import annotations

from app.agents.workflow import run_compliance_workflow
from app.graph.knowledge_graph import ComplianceKnowledgeGraph
from app.models.schemas import ComplianceReport, PolicyRequest
from app.services.gap_analysis import Finding, Scorer


class ComplianceService:
    """Holds the latest report and knowledge graph PER TENANT (a single shared slot would hand one tenant's
    results to another)."""

    def __init__(self) -> None:
        self._latest_report: dict[str, ComplianceReport] = {}
        self._kg: dict[str, ComplianceKnowledgeGraph] = {}

    async def analyze(self, tenant_key: str, company_id: str, documents: list[dict[str, str]],
                      scorer: Scorer | None = None) -> ComplianceReport:
        """documents: [{"document_id", "filename", "path"}] already resolved for this tenant."""
        state = run_compliance_workflow(company_id=company_id, documents=documents, scorer=scorer)
        report = state["report"]
        self._latest_report[tenant_key] = report
        self._kg[tenant_key] = self._build_knowledge_graph(company_id, state.get("data_flows", []), state.get("findings", []))
        return report

    async def latest_report(self, tenant_key: str) -> ComplianceReport | None:
        return self._latest_report.get(tenant_key)

    async def generate_policy(self, payload: PolicyRequest) -> dict[str, str]:
        # Template only: fills a fixed outline with the caller's context. No generation or legal review happens here.
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
        return {"policy_type": payload.policy_type, "content_de": content,
                "note_de": "Vorlage zum Ausfüllen, keine rechtliche Prüfung und keine generierte Fassung."}

    async def simulate_dsar(self, subject_id: str) -> dict[str, str]:
        # Stub: returns a fixed message. It does not search any data store.
        return {
            "subject_id": subject_id,
            "status": "completed",
            "result_de": "DSAR-Simulation (Platzhalter): es wurde kein Datenbestand durchsucht.",
        }

    async def graph_payload(self, tenant_key: str) -> dict:
        kg = self._kg.get(tenant_key)
        return kg.to_visual_payload() if kg else {"nodes": [], "edges": []}

    @staticmethod
    def _build_knowledge_graph(company_id: str, flows: list[dict], findings: list[Finding]) -> ComplianceKnowledgeGraph:
        """Company -> vendors found in its documents, and obligations -> the document that evidences them."""
        kg = ComplianceKnowledgeGraph()
        kg.add_entity(company_id, "company")
        for flow in flows:
            kg.add_entity(flow["vendor"], "vendor", third_country=flow["third_country"])
            kg.add_relation(company_id, flow["vendor"],
                            "transfers_to_third_country" if flow["third_country"] else "uses_vendor",
                            document=flow["document"])
        for f in findings:
            if not f.applicable:
                continue
            kg.add_entity(f.obligation.id, "obligation", status=f.status, title=f.obligation.title_de)
            kg.add_relation(company_id, f.obligation.id, "must_comply_with")
            if f.evidence is not None:
                doc = f.evidence.filename or f.evidence.document_id
                kg.add_entity(doc, "document")
                kg.add_relation(f.obligation.id, doc, "evidenced_by", score=round(f.score, 3))
        return kg


compliance_service = ComplianceService()
