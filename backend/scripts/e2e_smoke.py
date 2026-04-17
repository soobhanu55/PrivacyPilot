from __future__ import annotations

import json
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
ROOT = Path(__file__).resolve().parents[2]
HR_DOC = ROOT / "sample-data" / "company-docs" / "hr_policy.txt"
MKT_DOC = ROOT / "sample-data" / "company-docs" / "marketing_policy.txt"


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        login = client.post("/auth/login", json={"tenant_key": "demo-sme", "password": "demo1234"})
        login.raise_for_status()
        auth = login.json()
        access_token = auth["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        with HR_DOC.open("rb") as hr, MKT_DOC.open("rb") as mkt:
            upload = client.post(
                "/upload-documents",
                headers=headers,
                files=[("files", (HR_DOC.name, hr, "text/plain")), ("files", (MKT_DOC.name, mkt, "text/plain"))],
            )
        upload.raise_for_status()
        upload_payload = upload.json()
        document_ids = [doc["document_id"] for doc in upload_payload["uploaded_documents"]]

        analyze = client.post(
            "/analyze-compliance",
            headers=headers,
            json={"company_id": "demo-company", "document_ids": document_ids, "departments": ["HR", "Marketing"]},
        )
        analyze.raise_for_status()
        report = analyze.json()

        risk_report = client.get("/risk-report", headers=headers)
        risk_report.raise_for_status()

        audit = client.get("/audit-log", headers=headers)
        audit.raise_for_status()

        print("=== E2E Smoke Test Passed ===")
        print(f"Compliance score: {report['compliance_score']}")
        print(f"Risks: {len(report['risks'])}")
        print(f"Audit entries: {len(audit.json().get('entries', []))}")
        print("Top risk titles:", [item["title"] for item in report["risks"]])
        print("Report excerpt:")
        print(json.dumps({"summary_de": report["summary_de"], "next_actions_de": report["next_actions_de"][:2]}, indent=2))


if __name__ == "__main__":
    main()
