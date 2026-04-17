# Demo Scenario: HR + Marketing

## Objective

Show continuous compliance from upload to remediation:

1. Upload HR + Marketing policies
2. Run compliance analysis
3. Review detected risks
4. Generate policy templates
5. Simulate DSAR
6. Re-run and track improved score

## API Walkthrough

1. Upload:
   - `POST /upload-documents`
2. Analyze:
   - `POST /analyze-compliance` with uploaded `document_ids`
3. Read report:
   - `GET /risk-report`
4. Generate policy:
   - `POST /generate-policy` for `privacy_policy` and `dpa`
5. Simulate DSAR:
   - `POST /simulate-dsar/employee-123`
6. Inspect explainability:
   - `GET /audit-log`

## Expected Example Risks

- Missing consent tracking
- No retention policy
- Improper data transfer controls

## Before/After Improvement

- Before score: 40
- After applying recommendations: target 75+
