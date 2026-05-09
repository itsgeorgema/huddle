from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    data: dict = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    risk: float | None = None
    label: str | None = None
    data: dict = {}


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    adjacency: dict[str, list[str]]
