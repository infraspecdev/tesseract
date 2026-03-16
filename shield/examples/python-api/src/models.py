"""Pydantic models — intentionally incomplete."""
from pydantic import BaseModel


class Task(BaseModel):
    title: str
    description: str = ""
    status: str = "open"
    # Missing: validation for status enum, max lengths, etc.
