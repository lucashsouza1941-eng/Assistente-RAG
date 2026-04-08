from pydantic import BaseModel


class KPIResponse(BaseModel):
    total_conversations: int
    resolution_rate: float
    avg_response_time_ms: float
    patients_served: int
    escalation_rate: float
