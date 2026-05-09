from pydantic import BaseModel


class GroupRead(BaseModel):
    id: str
    label: str
    participant_ids: list[str]
    risk_score: float
    diversity_score: float
    bridge_score: float
    reasoning: str


class MediationBriefRead(BaseModel):
    group_id: str
    shared_ground: list[str]
    likely_tensions: list[str]
    bridge_questions: list[str]
    discussion_order: list[str]


class LiveMessage(BaseModel):
    group_id: str | None = None
    messages: list[str]


class LiveIntervention(BaseModel):
    event: str
    reason: str
    intervention: str
