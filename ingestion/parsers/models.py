"""Pydantic models for validating raw emission factor CSV data."""

import math
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AdemeRawRow(BaseModel):
    """Validation model for a single row of ADEME Base Carbone CSV data.

    Uses aliases matching the French column names from the raw API output.
    """

    row_id: int | str = Field(alias="__id")
    Produit_a_l_unite: str = Field(alias="Produit à l'unité")
    Facteur_d_emission: float = Field(alias="Facteur d'émission", ge=0.0)
    Incertitude_en_pct: Optional[float] = Field(
        alias="Incertitude en %", ge=0.0, le=1.0)
    CodeFede: str
    Federation: str
    Remarques: Optional[str]
    model_config = {"populate_by_name": True, "extra": "ignore"}

    @field_validator("Facteur_d_emission")
    @classmethod
    def _positive_emission(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(
                f"Facteur d'émission must be positive, got {v}")
        return v

    @field_validator("CodeFede", "Federation")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must be a non-empty string")
        return v

    @field_validator("row_id")
    @classmethod
    def _id_non_empty(cls, v: int | str) -> int | str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("row_id must not be empty")
        return v

    @field_validator("Incertitude_en_pct", "Remarques", mode="before")
    @classmethod
    def _blank_incertitude_to_none(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v


class DefraRawRow(BaseModel):
    """Validation model for a single row of DEFRA GHG conversion factors CSV.

    Columns from the flat-format Excel sheet after header row 5.
    """
    id: int | str = Field(alias="ID")
    level_1: str = Field(alias="Level 1")
    level_2: str = Field(alias="Level 2")
    level_3: str = Field(alias="Level 3")
    level_4: Optional[str] = Field(alias="Level 4", default=None)
    column_text: Optional[str] = Field(alias="Column Text", default=None)
    ghg_conversion_factor: float = Field(
        alias="GHG Conversion Factor")
    uom: str = Field(alias="UOM")
    scope: str = Field(alias="Scope")
    ghg_unit: str = Field(alias="GHG/Unit")
    year: int = Field(ge=2000, le=2100)
    model_config = {"populate_by_name": True, "extra": "ignore"}

    @field_validator("level_1", "level_2", "level_3", "uom", "scope", "ghg_unit")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must be a non-empty string")
        return v

    @field_validator("ghg_conversion_factor")
    @classmethod
    def _positive_factor(cls, v: float) -> float:
        if v < 0:
            raise ValueError(
                f"GHG Conversion Factor must be positive, got {v}")
        return v

    @field_validator("level_4", "column_text", mode="before")
    @classmethod
    def nan_or_blank_to_none(cls, v: object) -> object:
        if v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @field_validator("id")
    @classmethod
    def _id_non_empty(cls, v: int | str) -> int | str:
        if isinstance(v, str) and not v.strip():
            raise ValueError("id must not be empty")
        return v


class NveRawRow(BaseModel):
    """Validation model for a single row of NVE electricity grid emission factors CSV."""

    year: int = Field(ge=2000, le=2100)
    co2_per_kWh: float = Field(ge=0.0)
    factor_type: str

    @field_validator("factor_type")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("factor_type must be a non-empty string")
        return v
