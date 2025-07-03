"""Models for tracking GitHub interactions."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class InteractionType(enum.Enum):
    """Types of GitHub interactions we track."""

    API_CALL = "api_call"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    COMMENT = "comment"
    REVIEW = "review"
    FORK = "fork"
    STAR = "star"
    WATCH = "watch"
    RELEASE = "release"
    WORKFLOW_RUN = "workflow_run"


class Organization(Base):
    """GitHub organization model."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    github_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="organization"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="organization"
    )


class Repository(Base):
    """GitHub repository model."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    github_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(default=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="repositories"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="repository"
    )


class Interaction(Base):
    """Record of a GitHub interaction."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[InteractionType] = mapped_column(Enum(InteractionType))
    repository_id: Mapped[int | None] = mapped_column(
        ForeignKey("repositories.id"), nullable=True
    )
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    repository: Mapped[Optional["Repository"]] = relationship(
        "Repository", back_populates="interactions"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="interactions"
    )
