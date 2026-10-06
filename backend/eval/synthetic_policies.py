"""Synthetic company-policy documents with known ground truth, for evaluating the gap analysis.

Everything here is written by hand and SYNTHETIC: it measures how well the matcher handles these particular
paraphrases, not how it would do on real SME policies. Each obligation has paragraphs that satisfy it
(PRESENT) and hard distractors that mention the topic without satisfying it (DISTRACT, e.g. "we have not
appointed one yet"). The wordings are split: variants 0-1 are the DEV split (used to tune thresholds),
variants 2-3 the TEST split (used only to report). Variants alternate German / English.
"""
from __future__ import annotations

import random

PRESENT = {
    "dsgvo-30": [
        "Wir führen ein Verzeichnis von Verarbeitungstätigkeiten nach Art. 30 DSGVO. Es enthält für jede Verarbeitung den Zweck, die Kategorien personenbezogener Daten, die Empfänger und die vorgesehenen Löschfristen und wird jährlich überprüft.",
        "Our records of processing activities list every processing operation with its purpose, the categories of personal data, the recipients and the retention period. The record is reviewed once a year by the data protection coordinator.",
        "Das Verarbeitungsverzeichnis der Firma ist vollständig gepflegt: pro Tätigkeit sind Zweck, betroffene Personengruppen, Datenarten, Empfänger und Fristen für die Löschung eingetragen. Neue Verfahren werden vor dem Start aufgenommen.",
        "A register of all data processing is maintained for the whole company. For each activity it names the purpose, the data categories, who receives the data and when the data is erased, and new systems are added before go-live.",
    ],
    "dsgvo-33": [
        "Bei einer Datenpanne informiert jede Mitarbeiterin sofort den Datenschutzkoordinator. Dieser prüft den Vorfall und meldet eine Verletzung des Schutzes personenbezogener Daten innerhalb von 72 Stunden an die zuständige Aufsichtsbehörde.",
        "Every suspected data breach must be reported internally within one hour. The data protection officer assesses it and notifies the supervisory authority within 72 hours if there is a risk to the individuals concerned.",
        "Unser Notfallplan für Datenschutzverletzungen legt fest: Meldung an die Aufsichtsbehörde spätestens 72 Stunden nach Bekanntwerden, Dokumentation jedes Vorfalls und Information der Betroffenen bei hohem Risiko.",
        "Our incident procedure for personal data breaches sets a deadline of 72 hours to inform the authority, requires every incident to be logged, and describes when affected people must be told.",
    ],
    "dsgvo-28": [
        "Mit allen externen Dienstleistern, die personenbezogene Daten in unserem Auftrag verarbeiten, schließen wir einen Auftragsverarbeitungsvertrag nach Art. 28 DSGVO ab. Die Verträge liegen im Vertragsmanagement und werden jährlich geprüft.",
        "A data processing agreement is signed with every processor that handles personal data on our behalf, for example hosting and payroll providers. The agreements are stored centrally and reviewed once a year.",
        "Für Hosting, Lohnabrechnung und Newsletter-Versand bestehen AV-Verträge mit unseren Dienstleistern. Neue Anbieter werden erst nach Unterzeichnung des Vertrags freigegeben.",
        "No external provider gets access to personal data before a processing contract is in place. Our contract register shows a signed agreement for each current vendor.",
    ],
    "dsgvo-37": [
        "Wir haben einen externen Datenschutzbeauftragten benannt und der Aufsichtsbehörde gemeldet. Seine Kontaktdaten stehen in der Datenschutzerklärung und sind für alle Mitarbeitenden im Intranet erreichbar.",
        "A data protection officer has been appointed and registered with the supervisory authority. Employees and customers can reach the officer through the contact details published on our website.",
        "Die Rolle des Datenschutzbeauftragten ist seit diesem Jahr besetzt: Ein zertifizierter Berater übernimmt die Aufgabe, die Benennung wurde bei der Behörde angezeigt.",
        "Our company has designated a data protection officer, a certified external consultant, and notified the authority of the appointment. Contact details are part of every privacy notice.",
    ],
    "dsgvo-17": [
        "Unser Löschkonzept legt Aufbewahrungsfristen je Datenart fest: Bewerberdaten werden nach sechs Monaten gelöscht, Rechnungen nach zehn Jahren. Die Löschung wird protokolliert.",
        "We follow a retention schedule with fixed periods per type of data. Applicant data is deleted after six months and contracts after the legal retention period, and each deletion is logged.",
        "Personenbezogene Daten werden nur so lange gespeichert wie nötig. Für jede Datenart gibt es eine definierte Frist, nach deren Ablauf die Daten automatisch gelöscht werden.",
        "Data is kept only as long as needed. Each category has a defined deletion date, and a monthly job removes expired records from all systems.",
    ],
    "dsgvo-7": [
        "Einwilligungen für Newsletter und Marketing werden über ein Consent-Tool dokumentiert, mit Zeitpunkt und Zweck gespeichert und können jederzeit widerrufen werden. Der Nachweis ist abrufbar.",
        "Consent for marketing e-mails is recorded with a timestamp and the exact wording shown to the person. People can withdraw consent at any time and the withdrawal is logged.",
        "Wir holen Einwilligungen aktiv ein (Double-Opt-In) und führen ein Register darüber. Ein Widerruf ist mit einem Klick möglich und wird sofort im System umgesetzt.",
        "Opt-ins are collected through a double confirmation and stored in a consent register, so we can prove when and for what purpose someone agreed. Unsubscribing takes effect immediately.",
    ],
    "dsgvo-46": [
        "Für die Nutzung von Microsoft 365 und HubSpot mit Datenübermittlung in die USA haben wir Standardvertragsklauseln abgeschlossen und eine Transfer-Folgenabschätzung dokumentiert.",
        "Where data goes to US providers such as AWS, we rely on standard contractual clauses and a documented transfer impact assessment, which is reviewed whenever the provider changes.",
        "Bei Anbietern mit Sitz in Drittländern (Zoom, Salesforce) liegen Standardvertragsklauseln vor; ergänzend wurden technische Schutzmaßnahmen und die Rechtslage vor Ort geprüft.",
        "Transfers to third countries such as the USA are covered by standard contractual clauses signed with Google and Slack, plus an assessment of the legal risks in the recipient country.",
    ],
    "nis2-21": [
        "Wir setzen technische Schutzmaßnahmen um: Alle Konten sind durch Multi-Faktor-Authentifizierung gesichert, Daten werden verschlüsselt gespeichert, tägliche Backups werden getestet und ein Notfallkonzept regelt den Betrieb bei Ausfällen.",
        "Our security measures include multi-factor authentication for all accounts, encryption of data at rest, regular backups with restore tests, vulnerability scans and an incident response plan.",
        "Die IT-Sicherheit umfasst Zwei-Faktor-Anmeldung, Festplattenverschlüsselung, monatliche Schwachstellenscans und automatische Patches. Für Ausfälle gibt es einen dokumentierten Wiederanlaufplan.",
        "To manage cyber risks we run patch management, back up all critical systems offsite, enforce 2FA and have a business continuity plan that is exercised once a year.",
    ],
    "nis2-23": [
        "Erhebliche Sicherheitsvorfälle melden wir stufenweise: eine Frühwarnung innerhalb von 24 Stunden an das BSI, eine Meldung mit Bewertung innerhalb von 72 Stunden und einen Abschlussbericht nach einem Monat.",
        "For significant security incidents we send an early warning to the competent authority within 24 hours, an incident notification within 72 hours and a final report after one month.",
        "Das Krisenteam ist angewiesen, jeden schwerwiegenden Sicherheitsvorfall binnen eines Tages als Frühwarnung an die zuständige Behörde zu melden und danach die Details nachzureichen.",
        "Our incident plan names the person who files the first report with the national CSIRT within a day of becoming aware of a major incident, followed by a detailed report.",
    ],
    "aiact-14": [
        "Für unseren KI-gestützten Kundenservice ist menschliche Aufsicht vorgesehen: Geschulte Mitarbeitende prüfen die Ergebnisse, können sie übersteuern und das System jederzeit anhalten.",
        "Our AI systems operate under human oversight: trained reviewers check outputs before they affect customers, can override any result and can stop the system at any time.",
        "Entscheidungen des KI-Modells zur Bewerbervorauswahl werden nie automatisch umgesetzt. Eine Person kontrolliert jede Empfehlung und kann eingreifen.",
        "A human-in-the-loop step is mandatory for the machine learning model that scores leads: a staff member reviews the score and may intervene or ignore it.",
    ],
}

DISTRACT = {
    "dsgvo-30": [
        "Ein Verzeichnis aller Datenverarbeitungen existiert bisher nicht. Wir haben uns vorgenommen, es im nächsten Jahr zu erstellen, sobald die Zuständigkeiten geklärt sind.",
        "We know that records of processing activities are required but have not started one yet. At the moment each team keeps its own informal list of tools.",
        "Die Fachabteilungen führen eigene Excel-Listen über genutzte Programme. Eine zentrale Übersicht mit Zwecken und Empfängern gibt es derzeit nicht.",
        "There is no overview of which personal data we process or why. A documentation project for this is planned but not funded.",
    ],
    "dsgvo-33": [
        "Datenpannen sind bisher nicht aufgetreten. Ein formaler Ablauf für den Ernstfall ist nicht festgelegt, die Geschäftsführung würde im Einzelfall entscheiden.",
        "We have never had a data breach, so there is no written procedure for reporting one. Management would decide what to do if it happened.",
        "Sicherheitsvorfälle werden per E-Mail an die IT gemeldet. Ob und wann eine Behörde informiert wird, ist nicht geregelt.",
        "Employees are asked to tell IT when a laptop is lost. What happens next and who informs any authority is not defined.",
    ],
    "dsgvo-28": [
        "Wir arbeiten mit mehreren Dienstleistern zusammen, die Kundendaten sehen können. Verträge über die Datenverarbeitung stehen noch aus und werden nach Möglichkeit nachgeholt.",
        "Our vendors can access customer records. We rely on their standard terms of service and have not signed separate processing agreements.",
        "Die Buchhaltung wird von einem externen Büro erledigt. Zur Verarbeitung der Daten dort wurde nichts Schriftliches vereinbart.",
        "An outside agency manages our customer mailing list. There is only an informal agreement by e-mail about how they use the data.",
    ],
    "dsgvo-37": [
        "Ob wir einen Datenschutzbeauftragten benennen müssen, ist noch nicht geklärt. Die Stelle ist derzeit nicht besetzt.",
        "The position of data protection officer is currently vacant. We are still checking whether the law requires us to appoint one.",
        "Fragen zum Datenschutz richtet man bei uns an die Geschäftsführung. Eine benannte Person für diese Aufgabe gibt es nicht.",
        "Privacy questions go to whoever is available in the office. No one has formally been given responsibility for data protection.",
    ],
    "dsgvo-17": [
        "Daten werden bei uns grundsätzlich aufbewahrt, weil sie später nützlich sein könnten. Feste Fristen für die Löschung haben wir nicht definiert.",
        "Customer data stays in the CRM indefinitely. We have no schedule for deleting old records.",
        "Alte Backups und E-Mail-Postfächer werden nicht aufgeräumt. Ein Konzept dafür ist nicht geplant.",
        "Nobody is responsible for removing outdated files from the shared drive, and there is no rule about how long documents are kept.",
    ],
    "dsgvo-7": [
        "Newsletter-Adressen stammen teils aus alten Visitenkarten und Messekontakten. Wie die Zustimmung dazu eingeholt wurde, ist nicht dokumentiert.",
        "We assume that customers agree to marketing mails when they buy from us. We do not keep a record of that agreement.",
        "Das Kontaktformular hat ein Häkchen für Marketing, über dessen Speicherung wir nichts festhalten. Abmeldungen werden manuell bearbeitet.",
        "Contacts from trade fairs are added to the mailing list. If someone asks to be removed, we delete them when we notice.",
    ],
    "dsgvo-46": [
        "Wir nutzen Microsoft 365, Zoom und Google Workspace für die tägliche Arbeit. Wo die Daten dabei verarbeitet werden, haben wir nicht geprüft.",
        "Our CRM runs on HubSpot and our infrastructure on AWS. We have not reviewed whether personal data leaves the EU.",
        "Für Videokonferenzen verwenden wir Zoom und für Dateiablage Dropbox. Zusätzliche Vereinbarungen zum Datentransfer in die USA bestehen nicht.",
        "The team collaborates in Slack and stores documents in Google Cloud. Data transfers outside Europe have never been looked at.",
    ],
    "nis2-21": [
        "Die IT-Sicherheit wird bei uns von einem Mitarbeiter nebenbei betreut. Passwörter werden gelegentlich geändert, ein weitergehendes Konzept existiert nicht.",
        "We use antivirus software on office computers. Beyond that, security is handled case by case without a written concept.",
        "Backups werden gemacht, wenn jemand daran denkt. Verschlüsselung und Mehr-Faktor-Anmeldung sind derzeit nicht eingeführt.",
        "Patches are installed when employees complain about problems. There is no plan for what to do after a serious outage.",
    ],
    "nis2-23": [
        "Sicherheitsvorfälle werden intern in einem Ticketsystem erfasst. Eine Meldung an Behörden ist nicht vorgesehen, weil wir uns nicht als betroffen ansehen.",
        "Security incidents are tracked internally. We have not checked whether we must report them to any authority and no deadlines are defined.",
        "Nach einem Angriff würde die IT zunächst versuchen, den Betrieb wiederherzustellen. Wer informiert wird und wann, ist offen.",
        "In case of a cyber attack the priority is to get systems running again; informing authorities is handled afterwards if at all.",
    ],
    "aiact-14": [
        "Wir setzen einen Chatbot im Kundenservice ein, der Fragen selbstständig beantwortet. Eine Kontrolle der Antworten durch Mitarbeitende findet nicht statt.",
        "We use an AI model to rank job applications. Its output is used directly and nobody is assigned to check or override it.",
        "Das Sprachmodell erstellt Angebotstexte, die ungeprüft an Kunden gehen. Regeln, wer das System überwacht, gibt es nicht.",
        "Our machine learning model approves small customer refunds automatically. There is no review step and no way for staff to step in.",
    ],
}

FILLER = [  # neutral company text, no obligation topics; 0-6 dev, 7-13 test
    "Die Müller Maschinenbau GmbH wurde 1998 gegründet und beschäftigt heute rund 85 Mitarbeitende an zwei Standorten in Süddeutschland.",
    "Our company develops industrial pumps and sells them to customers in more than twenty countries through a network of regional partners.",
    "Der Urlaubsantrag wird im Personalportal gestellt und von der jeweiligen Führungskraft innerhalb von drei Arbeitstagen bearbeitet.",
    "New employees receive a laptop, a security badge and an introduction to the team on their first day.",
    "Die Kantine bietet täglich zwei Gerichte an. Getränke und Obst stehen den Mitarbeitenden kostenlos zur Verfügung.",
    "The quarterly all-hands meeting is held in the main conference room and streamed to the second office.",
    "Reisekosten werden monatlich abgerechnet. Belege müssen bis zum fünften Werktag des Folgemonats vorliegen.",
    "Das Unternehmen produziert Verpackungslösungen aus recyceltem Material und liefert an den Einzelhandel in ganz Europa.",
    "Office hours are Monday to Friday from eight to five; visitors register at the front desk.",
    "Die Weihnachtsfeier findet jedes Jahr im Dezember statt und wird vom Betriebsrat organisiert.",
    "Meeting rooms can be booked in the calendar tool, and cleaning takes place every evening after six.",
    "Auszubildende durchlaufen in drei Jahren alle Abteilungen und werden von einem festen Mentor begleitet.",
    "Our fleet of delivery vans is serviced every twelve months, and drivers complete a safety training each spring.",
    "Die Geschäftsführung trifft sich einmal im Monat mit den Abteilungsleitern, um die Planung abzustimmen.",
]

SPLITS = {"dev": {"variants": (0, 1), "filler": range(0, 7)}, "test": {"variants": (2, 3), "filler": range(7, 14)}}
OBLIGATION_IDS = list(PRESENT)


def make_documents(split: str, n: int = 60, seed: int = 0) -> list[dict]:
    """n synthetic documents. Each has a paragraph per obligation that is present (50%), a distractor
    (25%) or absent (25%), plus filler. Returns {"text", "present": {id: bool}, "mentioned": {id: bool}}."""
    cfg = SPLITS[split]
    rng = random.Random(f"{split}-{seed}")
    docs = []
    for _ in range(n):
        paras, present, mentioned = [], {}, {}
        for ob in OBLIGATION_IDS:
            r = rng.random()
            present[ob] = r < 0.5
            mentioned[ob] = r < 0.75
            if r < 0.5:
                paras.append(PRESENT[ob][rng.choice(cfg["variants"])])
            elif r < 0.75:
                paras.append(DISTRACT[ob][rng.choice(cfg["variants"])])
        paras += [FILLER[i] for i in rng.sample(list(cfg["filler"]), 4)]
        rng.shuffle(paras)
        docs.append({"text": "\n\n".join(paras), "present": present, "mentioned": mentioned})
    return docs
