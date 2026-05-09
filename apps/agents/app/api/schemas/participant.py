from pydantic import BaseModel, Field


class ParticipantInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    statement: str = Field(min_length=3)


class ParticipantBatchCreate(BaseModel):
    participants: list[ParticipantInput]


class ParticipantRead(BaseModel):
    id: str
    display_name: str
    statement: str | None = None

    model_config = {"from_attributes": True}
