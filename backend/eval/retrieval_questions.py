"""Hand-labelled retrieval questions over the AI Act and NIS2 corpus.

Each question has the article(s) that actually answer it, checked against the corpus text (not the title
alone). Questions are phrased the way an SME would ask, deliberately NOT copying article titles. The pool
searched is all 178 distinct articles of the AI Act, NIS2 and CSRD, so a random ranking hits rank 1 about 0.6% of the time.
Where two articles genuinely both answer the question, both are accepted.
"""

# (question, language, [(regulation, article), ...])
QUESTIONS = [
    ("Which AI practices are banned outright in the EU?", "en", [("AI Act", 5)]),
    ("Can a company use social scoring of people based on their behaviour?", "en", [("AI Act", 5)]),
    ("What makes an AI system count as high-risk?", "en", [("AI Act", 6)]),
    ("What must providers set up to identify and reduce the risks of a high-risk AI system over its lifecycle?", "en", [("AI Act", 9)]),
    ("What rules apply to training, validation and test datasets of high-risk systems, including bias?", "en", [("AI Act", 10)]),
    ("What technical documentation must be drawn up before a high-risk AI system is placed on the market?", "en", [("AI Act", 11)]),
    ("Must high-risk AI systems automatically log events during operation?", "en", [("AI Act", 12), ("AI Act", 19)]),
    ("How must a high-risk AI system be designed so people can effectively supervise it and stop it?", "en", [("AI Act", 14)]),
    ("What accuracy and cybersecurity robustness is required of high-risk AI?", "en", [("AI Act", 15)]),
    ("Do users have to be told when they are interacting with a chatbot?", "en", [("AI Act", 50)]),
    ("What must deployers of high-risk AI systems do, for example monitoring use and informing workers?", "en", [("AI Act", 26)]),
    ("When must an assessment of the impact on fundamental rights be carried out before using high-risk AI?", "en", [("AI Act", 27)]),
    ("What is the maximum fine for violating the ban on prohibited AI practices?", "en", [("AI Act", 99)]),
    ("Do employees who work with AI need training?", "en", [("AI Act", 4)]),
    ("What obligations apply to providers of general-purpose AI models?", "en", [("AI Act", 53)]),
    ("When must serious incidents involving a high-risk AI system be reported to the authorities?", "en", [("AI Act", 73)]),
    ("Can an affected person ask for an explanation of a decision taken with the help of a high-risk AI system?", "en", [("AI Act", 86)]),
    ("What is an AI regulatory sandbox?", "en", [("AI Act", 57)]),
    ("What quality management system must providers of high-risk AI have?", "en", [("AI Act", 17)]),
    ("Who has to register high-risk AI systems in the EU database?", "en", [("AI Act", 49), ("AI Act", 71)]),
    ("What are the responsibilities of the management body for cybersecurity?", "en", [("NIS2", 20)]),
    ("What minimum cybersecurity measures must essential and important entities take, such as encryption and supply chain security?", "en", [("NIS2", 21)]),
    ("Within how many hours must a significant incident be notified to the CSIRT?", "en", [("NIS2", 23)]),
    ("How high can administrative fines for essential and important entities be?", "en", [("NIS2", 34)]),
    ("Which kinds of companies fall under the directive as essential or important entities?", "en", [("NIS2", 2), ("NIS2", 3)]),
    ("What is coordinated vulnerability disclosure?", "en", [("NIS2", 12)]),
    ("What powers do authorities have to supervise important entities?", "en", [("NIS2", 33)]),
    ("What information must entities submit to the registry of entities?", "en", [("NIS2", 27)]),
    ("How must member states organise their computer security incident response teams?", "en", [("NIS2", 10), ("NIS2", 11)]),
    ("Can entities voluntarily exchange cyber threat information with each other?", "en", [("NIS2", 29)]),
    ("Can members of management be held liable for breaches of the cybersecurity obligations?", "en", [("NIS2", 20)]),
    ("Which member state has jurisdiction over an entity that offers services in several countries?", "en", [("NIS2", 26)]),
    ("Welche KI-Praktiken sind verboten?", "de", [("AI Act", 5)]),
    ("Muss ich Kunden darüber informieren, dass sie mit einem Chatbot sprechen?", "de", [("AI Act", 50)]),
    ("Wie schnell muss ich einen erheblichen Sicherheitsvorfall melden?", "de", [("NIS2", 23)]),
    ("Welche Pflichten hat die Geschäftsleitung bei der Cybersicherheit?", "de", [("NIS2", 20)]),
    ("Welche Anforderungen gelten für die technische Dokumentation von Hochrisiko-KI?", "de", [("AI Act", 11)]),
]
