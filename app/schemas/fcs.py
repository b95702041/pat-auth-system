"""FCS schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any


class FCSParameter(BaseModel):
    """Schema for FCS parameter."""
    index: int
    pnn: str
    pns: str
    range: int
    display: str


class FCSParameterResponse(BaseModel):
    """Schema for FCS parameters response."""
    total_events: int
    total_parameters: int
    parameters: List[FCSParameter]


class FCSEventResponse(BaseModel):
    """Schema for FCS events response."""
    total_events: int
    limit: int
    offset: int
    events: List[Dict[str, Any]]


class FCSUploadResponse(BaseModel):
    """Schema for FCS upload response."""
    file_id: str
    filename: str
    total_events: int
    total_parameters: int


class FCSStatistic(BaseModel):
    """Schema for FCS parameter statistics."""
    parameter: str
    pns: str
    display: str
    min: float
    max: float
    mean: float
    median: float
    std: float


class FCSStatisticsResponse(BaseModel):
    """Schema for FCS statistics response."""
    total_events: int
    statistics: List[FCSStatistic]
