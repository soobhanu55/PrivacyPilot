"""Evidence-based compliance gap analysis over a company's own documents.

For each obligation (GDPR / NIS2 / AI Act) we look for a passage in the uploaded documents that evidences
it. A passage is scored by a Scorer (keyword rules, or dense embeddings when a model is available); the
best score decides found / review / gap. Obligations whose topic never appears (no third-country vendor,
no AI system) are marked not applicable instead of reported as gaps.

This replaces the earlier agent that returned three hardcoded findings for any input. It is heuristic:
thresholds were tuned on synthetic documents (see docs/gap_eval.md) and are not validated on real SME
policies. Findings are decision support for a human reviewer, not legal advice.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from app.models.schemas import RiskItem
from app.rag.corpus import article_title


@dataclass(frozen=True)
class Obligation:
    id: str
    regulation: str
    article: int
    title_de: str
    query: str  # what a policy sentence meeting the obligation would say (used by the dense scorer)
    keywords: tuple[str, ...]  # regex patterns; the keyword scorer = share of patterns found in one passage
    severity: str  # Low / Medium / High if missing
    explanation_de: str
    recommendation_de: str
    applies_if: str | None = None  # regex; the obligation only applies if the documents match it


OBLIGATIONS: tuple[Obligation, ...] = (
    Obligation(
        "dsgvo-30", "DSGVO", 30, "Verzeichnis von Verarbeitungstätigkeiten",
        "Wir führen ein Verzeichnis von Verarbeitungstätigkeiten mit Zweck, Datenkategorien, Empfängern und Löschfristen.",
        (r"verzeichnis\w* von verarbeitungst\w+|verarbeitungsverzeichnis|records? of processing",
         r"kategorien\s+(?:personenbezogener\s+)?daten|categories of (?:personal )?data",
         r"empf[aä]nger|recipients?", r"zweck\w*|purposes?"),
        "Medium", "Es wurde kein Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) gefunden.",
        "Führen Sie ein Verarbeitungsverzeichnis mit Zweck, Datenkategorien, Empfängern und Löschfristen.",
    ),
    Obligation(
        "dsgvo-33", "DSGVO", 33, "Meldung von Datenschutzverletzungen",
        "Datenschutzverletzungen werden binnen 72 Stunden der Aufsichtsbehörde gemeldet.",
        (r"72\s*stunden|72[- ]hours?", r"aufsichtsbeh[oö]rde|supervisory authority",
         r"datenpanne\w*|datenschutzverletzung\w*|data breach\w*|personal data breach",
         r"melde\w*|notif\w*"),
        "High", "Es gibt keinen dokumentierten Prozess zur Meldung von Datenschutzverletzungen binnen 72 Stunden (Art. 33 DSGVO).",
        "Definieren Sie einen Meldeprozess mit Zuständigkeiten und der 72-Stunden-Frist an die Aufsichtsbehörde.",
    ),
    Obligation(
        "dsgvo-28", "DSGVO", 28, "Auftragsverarbeitungsverträge",
        "Mit allen Dienstleistern, die personenbezogene Daten in unserem Auftrag verarbeiten, bestehen Auftragsverarbeitungsverträge.",
        (r"auftragsverarbeit\w*|\bavv\b|data processing agreement|\bdpa\b", r"vertr[aä]g\w*|agreements?|contracts?",
         r"dienstleister\w*|auftragsverarbeiter|processors?|vendors?"),
        "High", "Es wurden keine Auftragsverarbeitungsverträge mit Dienstleistern nachgewiesen (Art. 28 DSGVO).",
        "Schließen Sie mit jedem Dienstleister, der Daten in Ihrem Auftrag verarbeitet, einen AV-Vertrag.",
    ),
    Obligation(
        "dsgvo-37", "DSGVO", 37, "Datenschutzbeauftragter",
        "Wir haben einen Datenschutzbeauftragten benannt und der Aufsichtsbehörde gemeldet.",
        (r"datenschutzbeauftragt\w*|data protection officer|\bdpo\b", r"benannt|bestellt|appointed|designated",
         r"kontakt\w*|erreichbar|contact"),
        "Medium", "Es wurde keine Benennung eines Datenschutzbeauftragten gefunden (Art. 37 DSGVO).",
        "Prüfen Sie die Benennungspflicht und benennen Sie ggf. einen (internen oder externen) Datenschutzbeauftragten.",
    ),
    Obligation(
        "dsgvo-17", "DSGVO", 17, "Löschkonzept und Aufbewahrungsfristen",
        "Es gibt ein Löschkonzept mit festen Aufbewahrungsfristen je Datenart; Daten werden nach Fristablauf gelöscht.",
        (r"l[oö]schkonzept|l[oö]schfrist\w*|aufbewahrungsfrist\w*|retention (?:period|policy|schedule)",
         r"gel[oö]scht|l[oö]sch\w*|deleted|erasure", r"nach (?:ablauf|fristende)|\d+\s*(?:jahre\w*|monate\w*|years|months)"),
        "Medium", "Es wurde kein Löschkonzept mit Aufbewahrungsfristen gefunden (Art. 17 DSGVO).",
        "Legen Sie Aufbewahrungs- und Löschfristen je Datenart fest und dokumentieren Sie die Löschung.",
    ),
    Obligation(
        "dsgvo-7", "DSGVO", 7, "Nachweisbare Einwilligungen",
        "Einwilligungen werden dokumentiert, sind jederzeit widerrufbar und können nachgewiesen werden.",
        (r"einwilligung\w*|consent", r"dokumentier\w*|nachweis\w*|protokolli\w*|record\w*|logged",
         r"widerr\w+|withdraw\w*"),
        "High", "Es gibt keinen Nachweis, dass Einwilligungen dokumentiert und widerrufbar sind (Art. 7 DSGVO).",
        "Führen Sie ein Einwilligungsregister mit Zeitpunkt, Zweck und Widerrufsmöglichkeit.",
    ),
    Obligation(
        "dsgvo-46", "DSGVO", 46, "Drittlandübermittlung mit Garantien",
        "Für Übermittlungen in Drittländer bestehen Standardvertragsklauseln und eine Transfer-Folgenabschätzung.",
        (r"standardvertragsklausel\w*|standard contractual clauses|\bscc\b", r"drittland\w*|third countr\w+|usa",
         r"transfer[- ]?(?:impact|folgen)\w*|\btia\b|angemessenheitsbeschluss|adequacy"),
        "High", "Mögliche Übermittlung in ein Drittland ohne nachgewiesene Garantien (Art. 44-46 DSGVO).",
        "Prüfen Sie Standardvertragsklauseln und ein Transfer Impact Assessment für US-/Drittland-Anbieter.",
        applies_if=r"\b(?:usa|u\.s\.|vereinigte staaten|united states|drittl[aä]nd\w*|third countr\w+|aws|amazon web services|"
                   r"google (?:workspace|cloud|analytics)|microsoft (?:azure|365)|office 365|salesforce|hubspot|mailchimp|"
                   r"zoom|slack|openai|dropbox)\b",
    ),
    Obligation(
        "nis2-21", "NIS2", 21, "Risikomanagementmaßnahmen für Cybersicherheit",
        "Wir setzen technische Maßnahmen zur Cybersicherheit um, zum Beispiel Multi-Faktor-Authentifizierung, Backups, Verschlüsselung und ein Notfallkonzept.",
        (r"multi-?faktor|\bmfa\b|2fa|zwei-?faktor|multi-?factor", r"backup\w*|datensicherung\w*",
         r"verschl[uü]ssel\w*|encrypt\w*", r"notfall\w*|incident response|business continuity|disaster",
         r"schwachstell\w*|vulnerabilit\w*|patch\w*"),
        "High", "Es wurden keine konkreten Cybersicherheitsmaßnahmen nachgewiesen (Art. 21 NIS2).",
        "Dokumentieren Sie Maßnahmen wie MFA, Backups, Verschlüsselung, Schwachstellenmanagement und Notfallplanung.",
    ),
    Obligation(
        "nis2-23", "NIS2", 23, "Meldepflichten bei Sicherheitsvorfällen",
        "Erhebliche Sicherheitsvorfälle werden innerhalb von 24 Stunden als Frühwarnung und binnen 72 Stunden ausführlich an das BSI gemeldet.",
        (r"24\s*stunden|24[- ]hours?", r"fr[uü]hwarnung|early warning", r"\bbsi\b|csirt|zust[aä]ndige beh[oö]rde|competent authority",
         r"sicherheitsvorf\w+|security incident|significant incident"),
        "High", "Es gibt keinen Prozess für die gestufte Meldung erheblicher Sicherheitsvorfälle (Art. 23 NIS2).",
        "Richten Sie die Meldekette ein: Frühwarnung binnen 24 h, Meldung binnen 72 h, Abschlussbericht.",
    ),
    Obligation(
        "aiact-14", "AI Act", 14, "Menschliche Aufsicht bei KI-Systemen",
        "Für unsere KI-Systeme ist menschliche Aufsicht vorgesehen: Ergebnisse werden von geschulten Personen geprüft und können übersteuert werden.",
        (r"menschliche\w* aufsicht|human oversight|human[- ]in[- ]the[- ]loop|\bhitl\b", r"pr[uü]f\w*|review\w*|kontroll\w*",
         r"[uü]bersteuer\w*|eingreif\w*|override|intervene|stopp\w*", r"ki[- ]?(?:system|modell)\w*|ai systems?"),
        "High", "Es wurde keine menschliche Aufsicht für eingesetzte KI-Systeme nachgewiesen (Art. 14 AI Act).",
        "Legen Sie fest, wer KI-Ergebnisse prüft, übersteuern und das System anhalten kann.",
        applies_if=r"\b(?:ki|k[uü]nstliche intelligenz|ai|artificial intelligence|machine learning|maschinelles lernen|chatbot|llm|"
                   r"sprachmodell\w*|copilot)\b",
    ),
)

# Vendors seen in company documents. (pattern, display name, headquartered outside the EU/EEA)
VENDORS = (
    (r"microsoft (?:365|azure|teams)|office 365|\bazure\b", "Microsoft", True),
    (r"\baws\b|amazon web services", "Amazon Web Services", True),
    (r"google (?:workspace|cloud|analytics)|\bgmail\b", "Google", True),
    (r"salesforce", "Salesforce", True), (r"hubspot", "HubSpot", True), (r"mailchimp", "Mailchimp", True),
    (r"\bzoom\b", "Zoom", True), (r"\bslack\b", "Slack", True), (r"openai|chatgpt", "OpenAI", True),
    (r"dropbox", "Dropbox", True),
    (r"\bsap\b", "SAP", False), (r"datev", "DATEV", False), (r"personio", "Personio", False),
    (r"hetzner", "Hetzner", False), (r"ionos", "IONOS", False),
)

# English versions of Obligation.query. Embedding similarity is higher for same-language text, so with a German-only
# query English passages score lower than German ones regardless of meaning; the dense scorer uses the better of both.
QUERIES_EN = {
    "dsgvo-30": "We keep a record of processing activities listing purpose, categories of personal data, recipients and retention periods.",
    "dsgvo-33": "Personal data breaches are reported to the supervisory authority within 72 hours.",
    "dsgvo-28": "Data processing agreements are in place with all service providers that process personal data on our behalf.",
    "dsgvo-37": "We have appointed a data protection officer and notified the supervisory authority.",
    "dsgvo-17": "We have a deletion concept with fixed retention periods per type of data; data is deleted after the period expires.",
    "dsgvo-7": "Consent is documented, can be withdrawn at any time and can be proven.",
    "dsgvo-46": "Transfers to third countries are covered by standard contractual clauses and a transfer impact assessment.",
    "nis2-21": "We implement technical cybersecurity measures such as multi-factor authentication, backups, encryption and an emergency plan.",
    "nis2-23": "Significant security incidents are reported within 24 hours as an early warning and in detail within 72 hours to the authority.",
    "aiact-14": "Our AI systems are subject to human oversight: trained people review the results and can override them.",
}

WEIGHT = {"High": 3, "Medium": 2, "Low": 1}
STATUS_POINTS = {"found": 1.0, "review": 0.5, "gap": 0.0}


@dataclass
class Chunk:
    text: str
    document_id: str = ""
    filename: str = ""


@dataclass
class Finding:
    obligation: Obligation
    applicable: bool
    status: str  # found / review / gap / not_applicable
    score: float = 0.0
    evidence: Chunk | None = None


@dataclass(frozen=True)
class Thresholds:
    found: float
    review: float


class Scorer(Protocol):
    name: str
    thresholds: Thresholds

    def prepare(self, chunks: list[Chunk]) -> None: ...
    def best_match(self, ob: Obligation, chunks: list[Chunk]) -> tuple[float, int]: ...


class KeywordScorer:
    """Share of the obligation's keyword patterns that appear in a single passage (0..1). No model needed."""

    name = "keyword-rules"
    thresholds = Thresholds(found=2 / 3, review=2 / 3)  # exactly 2/3 (tuned on dev, docs/gap_eval.md); scores are discrete, so no review band

    def prepare(self, chunks: list[Chunk]) -> None:
        pass

    def best_match(self, ob: Obligation, chunks: list[Chunk]) -> tuple[float, int]:
        best, idx = 0.0, -1
        for i, c in enumerate(chunks):
            t = c.text.lower()
            score = sum(bool(re.search(p, t)) for p in ob.keywords) / len(ob.keywords)
            if score > best:
                best, idx = score, i
        return best, idx


class DenseScorer:
    """Cosine similarity between the obligation's query (German and English, best of both) and each passage."""

    name = "dense-embeddings"
    thresholds = Thresholds(found=0.866, review=0.851)  # tuned on the dev split, see docs/gap_eval.md

    def __init__(self, embedder) -> None:
        self.embedder = embedder
        self._emb: np.ndarray | None = None
        self._queries: dict[str, np.ndarray] = {}  # obligation queries never change, embed each once (rows: de, en)

    def prepare(self, chunks: list[Chunk]) -> None:
        self._emb = self.embedder.encode_passages([c.text for c in chunks]) if chunks else None

    def best_match(self, ob: Obligation, chunks: list[Chunk]) -> tuple[float, int]:
        if self._emb is None or not len(chunks):
            return 0.0, -1
        if ob.id not in self._queries:
            self._queries[ob.id] = np.vstack([self.embedder.encode_query(ob.query),
                                              self.embedder.encode_query(QUERIES_EN[ob.id])])
        sims = (self._emb @ self._queries[ob.id].T).max(axis=1)
        i = int(np.argmax(sims))
        return float(sims[i]), i


def default_scorer() -> Scorer:
    """Dense embeddings when sentence-transformers and the model are available, else keyword rules."""
    try:
        from app.rag.hybrid_retriever import E5Embedder

        embedder = E5Embedder()
        embedder.encode_query("test")  # fails fast if the library or model is missing
        return DenseScorer(embedder)
    except Exception:
        return KeywordScorer()


def split_into_chunks(text: str, document_id: str = "", filename: str = "", size: int = 120, overlap: int = 20) -> list[Chunk]:
    """Paragraph-first chunking: a paragraph becomes one chunk, long paragraphs are cut into overlapping windows."""
    out: list[Chunk] = []
    for para in re.split(r"\n\s*\n", text):
        words = para.split()
        if not words:
            continue
        step = size - overlap
        starts = [0] if len(words) <= size else list(range(0, len(words) - overlap, step))
        out += [Chunk(" ".join(words[s:s + size]), document_id, filename) for s in starts]
    return out


def detect_vendors(chunks: list[Chunk]) -> list[dict]:
    """Vendors named in the documents (lexicon-based: only the vendors listed in VENDORS are recognised)."""
    found: dict[str, dict] = {}
    for c in chunks:
        low = c.text.lower()
        for pattern, name, third_country in VENDORS:
            if name not in found and re.search(pattern, low):
                found[name] = {"vendor": name, "third_country": third_country, "document": c.filename or c.document_id,
                               "excerpt": c.text[:160]}
    return list(found.values())


def applies(ob: Obligation, chunks: list[Chunk]) -> bool:
    return ob.applies_if is None or any(re.search(ob.applies_if, c.text.lower()) for c in chunks)


def analyze(chunks: list[Chunk], scorer: Scorer | None = None, thresholds: Thresholds | None = None) -> list[Finding]:
    scorer = scorer or default_scorer()
    th = thresholds or scorer.thresholds
    scorer.prepare(chunks)
    findings: list[Finding] = []
    for ob in OBLIGATIONS:
        if not applies(ob, chunks):
            findings.append(Finding(ob, False, "not_applicable"))
            continue
        score, idx = scorer.best_match(ob, chunks)
        status = "found" if score >= th.found else "review" if score >= th.review else "gap"
        findings.append(Finding(ob, True, status, score, chunks[idx] if idx >= 0 and status != "gap" else None))
    return findings


def compliance_score(findings: list[Finding]) -> int:
    """Severity-weighted share of applicable obligations that are evidenced (review counts half)."""
    applicable = [f for f in findings if f.applicable]
    if not applicable:
        return 100
    total = sum(WEIGHT[f.obligation.severity] for f in applicable)
    got = sum(WEIGHT[f.obligation.severity] * STATUS_POINTS[f.status] for f in applicable)
    return round(100 * got / total)


def to_risk_items(findings: list[Finding]) -> list[RiskItem]:
    """One RiskItem per obligation that is not clearly evidenced, citing the article (and its text title where
    the regulation text is in the corpus)."""
    items = []
    for f in findings:
        if not f.applicable or f.status == "found":
            continue
        ob = f.obligation
        title = article_title(ob.regulation, ob.article) if ob.regulation in ("AI Act", "NIS2") else None
        ref = f"{ob.regulation} Art. {ob.article}" + (f": {title}" if title else "")
        if f.status == "review":
            excerpt = f.evidence.text[:200] if f.evidence else ""
            severity = "Medium" if ob.severity == "High" else "Low"
            explanation = (f"Unklarer Nachweis für {ob.title_de}. Mögliche Textstelle in "
                           f"{f.evidence.filename or 'Dokument'} (Score {f.score:.2f}): „{excerpt}“. Bitte prüfen.")
            heading = f"Prüfen: {ob.title_de}"
        else:
            severity, explanation, heading = ob.severity, ob.explanation_de, f"Kein Nachweis: {ob.title_de}"
        items.append(RiskItem(id=ob.id, title=heading, regulation=ob.regulation, severity=severity,
                              explanation_de=explanation, recommendation_de=ob.recommendation_de, source_refs=[ref]))
    return items
