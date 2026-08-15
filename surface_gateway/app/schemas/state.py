from typing import Any

from pydantic import BaseModel, Field


class IssueMetadata(BaseModel):
    id: int | None = Field(default=None, description="GitHub Issue ID")
    repo: str | None = Field(
        default=None, description="GitHub repository full name (owner/repo)"
    )
    title: str | None = Field(default=None, description="GitHub Issue title")
    author: str | None = Field(default=None, description="Author handle")
    url: str | None = Field(default=None, description="HTML URL")
    labels: list[str] = Field(default_factory=list, description="Issue labels")


class SpecificationsState(BaseModel):
    full_spec_markdown: str = Field(
        default="", description="Generated full specification markdown"
    )
    revision_summary: str = Field(
        default="", description="Summary of changes in latest revision"
    )
    council_scores: dict[str, int] = Field(
        default_factory=lambda: {"product": 0, "tech": 0, "security": 0},
        description="Council scores across Product, Tech, and Security",
    )
    council_notes_summarized: str = Field(
        default="", description="Summarized council review feedback"
    )
    council_review_rounds: int = Field(
        default=0, description="Council review round count"
    )
    council_approved: bool = Field(
        default=False, description="True if council approved the spec"
    )


class AgentSessionState(BaseModel):
    parent_issue_id: int | None = Field(default=None, description="Target issue ID")
    issue: IssueMetadata = Field(
        default_factory=IssueMetadata, description="Issue metadata"
    )
    specifications: SpecificationsState = Field(
        default_factory=SpecificationsState, description="Specifications state domain"
    )
    council_review: list[dict[str, Any]] = Field(
        default_factory=list, description="Historical council reviews"
    )
