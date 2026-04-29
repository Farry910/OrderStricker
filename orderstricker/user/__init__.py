"""User identity and profile hooks (expand when auth is added)."""

from uuid import UUID

from pydantic import BaseModel, Field


class UserRef(BaseModel):
    id: UUID
