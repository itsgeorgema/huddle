from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str = ""


class SessionRead(BaseModel):
    id: str
    title: str
    description: str
    status: str

    model_config = {"from_attributes": True}


class AnalyzeRequest(BaseModel):
    group_size: int = Field(default=4, ge=2, le=8)
    constraints: dict = Field(default_factory=dict)


class PipelineStep(BaseModel):
    name: str
    status: str
    latency_ms: float | None = None
    error: str | None = None


class PipelineStatus(BaseModel):
    status: str
    steps: list[PipelineStep]
