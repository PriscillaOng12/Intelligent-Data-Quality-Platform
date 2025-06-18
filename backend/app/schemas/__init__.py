"""Pydantic schemas used for request and response bodies.

These schemas decouple the API layer from the database models. They can
include additional validation and transformation logic where appropriate.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")


class TokenPayload(BaseModel):
    sub: str
    exp: int


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str
    role: str = Field(default="Viewer")


class UserRead(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetRead(DatasetBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class RuleBase(BaseModel):
    dataset_id: int
    rule_type: str
    params: Dict[str, Any]
    threshold: float
    severity: str


class RuleCreate(RuleBase):
    enabled: bool = True


class RuleRead(RuleBase):
    id: int
    enabled: bool
    created_at: datetime

    class Config:
        orm_mode = True


class IncidentRead(BaseModel):
    id: int
    dataset_id: int
    rule_id: int
    created_at: datetime
    metric_value: float
    passed: bool
    severity: str
    description: str
    acknowledged: bool

    class Config:
        orm_mode = True


class AcknowledgementCreate(BaseModel):
    comment: Optional[str] = None
