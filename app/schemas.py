from typing import Any
from pydantic import BaseModel, Field, field_validator

class PredictionInput(BaseModel):
    rainfall_mm: float = Field(ge=0, le=2000)
    temperature_c: float = Field(ge=-50, le=60)
    humidity_pct: float = Field(ge=0, le=100)
    river_discharge_m3_s: float = Field(ge=0, le=100000)
    water_level_m: float = Field(ge=0, le=100)
    elevation_m: float = Field(default=1800, ge=-500, le=9000)
    land_cover: str = "Forest"
    soil_type: str = "Loamy"
    population_density: float = Field(default=120, ge=0)
    infrastructure: int = Field(default=1, ge=0, le=1)
    historical_floods: int = Field(default=0, ge=0, le=1)
    soil_moisture: float = Field(default=45, ge=0, le=100)

    @field_validator("land_cover", "soil_type")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

class NodeToggle(BaseModel):
    online: bool

class PredictionResponse(BaseModel):
    risk_probability: float
    risk_level: str
    system_confidence: float
    confidence_label: str
    contributors: list[dict[str, Any]]
    nodes: list[dict[str, Any]]
    network_status: str
    fusion_message: str
    monitoring_mode: str
    model_decision: str = ""
    prediction_latency_ms: float = 0
    feature_contributions: list[dict[str, Any]] = []
