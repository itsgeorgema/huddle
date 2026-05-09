from pydantic import BaseModel


class ClaimRead(BaseModel):
    id: str
    participant_id: str
    text: str
    claim_type: str
    stakeholder: str
    value_label: str
    confidence: float

    model_config = {"from_attributes": True}


class ConflictEdgeRead(BaseModel):
    id: str
    source_claim_id: str
    target_claim_id: str
    conflict_type: str
    risk_score: float
    reason: str

    model_config = {"from_attributes": True}
