from app.agents.base import Agent


VALUE_KEYWORDS = {
    "housing access": ["housing", "homes", "rent", "affordable"],
    "business access": ["business", "customers", "parking", "shops"],
    "transportation": ["transit", "bike", "bus", "traffic", "car"],
    "accessibility": ["elderly", "disabled", "accessible", "accessibility"],
    "public trust": ["listen", "trust", "transparent", "ignored"],
    "student wellbeing": ["students", "learning", "phone", "campus"],
    "climate": ["climate", "emissions", "dependency"],
    "safety": ["safe", "safety", "crime", "public safety"],
}

STAKEHOLDER_KEYWORDS = {
    "renters": ["housing", "renters", "homes"],
    "business owners": ["business", "shops", "customers"],
    "transit riders": ["transit", "bus", "bike"],
    "elderly residents": ["elderly", "accessible", "disabled"],
    "students": ["students", "campus", "school"],
    "residents": ["neighborhood", "residents", "community", "city"],
}


class ClaimExtractionAgent(Agent):
    name = "claim_extraction"

    async def run(self, payload: dict) -> dict:
        claims = []
        for idx, statement in enumerate(payload["statements"], start=1):
            text = statement["cleaned_statement"]
            parts = self._split_claims(text)
            for part_idx, part in enumerate(parts, start=1):
                claim_id = f"c{idx}_{part_idx}"
                claims.append(
                    {
                        "claim_id": claim_id,
                        "participant_id": statement["participant_id"],
                        "statement_id": statement["statement_id"],
                        "text": part,
                        "claim_type": self._claim_type(part),
                        "stakeholder": self._classify(part, STAKEHOLDER_KEYWORDS, "residents"),
                        "value": self._classify(part, VALUE_KEYWORDS, "community benefit"),
                        "confidence": 0.78,
                    }
                )
        return {"claims": claims}

    def _split_claims(self, text: str) -> list[str]:
        normalized = text.replace(" but ", ". But ").replace(" because ", ". Because ")
        parts = [part.strip(" .") for part in normalized.split(".") if part.strip(" .")]
        return parts[:3] or [text]

    def _claim_type(self, text: str) -> str:
        lower = text.lower()
        if any(word in lower for word in ["should", "need", "must", "support", "oppose"]):
            return "proposal"
        if any(word in lower for word in ["will", "would", "hurt", "help", "reduce"]):
            return "impact"
        if any(word in lower for word in ["more important", "priority", "matters"]):
            return "priority"
        return "concern"

    def _classify(self, text: str, labels: dict[str, list[str]], fallback: str) -> str:
        lower = text.lower()
        scores = {
            label: sum(1 for keyword in keywords if keyword in lower)
            for label, keywords in labels.items()
        }
        label, score = max(scores.items(), key=lambda item: item[1])
        return label if score else fallback
