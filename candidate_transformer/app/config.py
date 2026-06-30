# app/config.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class FieldConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    from_field: Optional[str] = Field(None, alias="from")
    type: str = "string"  # "string", "integer", "float", "list", "object"
    required: bool = False
    normalize: Optional[str] = None

class RuntimeConfig(BaseModel):
    fields: Optional[List[FieldConfig]] = None
    include_confidence: bool = True
    include_provenance: bool = True
    on_missing: str = "null"  # "null", "omit", "error"
