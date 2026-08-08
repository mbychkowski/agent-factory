from typing import Any
from pydantic import BaseModel, Field


class IssueMetadata(BaseModel):
    id: int | None = Field(default=None, description="GitHub Issue ID")
    title: str | None = Field(default=None, description="GitHub Issue title")
    author: str | None = Field(default=None, description="Author handle")
    url: str | None = Field(default=None, description="HTML URL")
    labels: list[str] = Field(default_factory=list, description="Issue labels")


class SpecificationsState(BaseModel):
    user_story_markdown: str = Field(default="", description="Generated user story markdown")
    story_peer_reviewed: bool = Field(default=False, description="True if story passed peer review")
    story_review_rounds: int = Field(default=0, description="Review iteration count")
    critique_history: list[dict[str, Any]] = Field(default_factory=list, description="Critique audit log")


class CommentItem(BaseModel):
    comment_id: int | str | None = Field(default=None, description="Comment ID")
    source: str = Field(default="github", description="Source surface")
    author: str = Field(default="unknown", description="Author handle")
    body: str = Field(default="", description="Comment body")
    timestamp: str | None = Field(default=None, description="ISO timestamp")


class AgentSessionState(BaseModel):
    parent_issue_id: int | None = Field(default=None, description="Target issue ID")
    issue: IssueMetadata = Field(default_factory=IssueMetadata, description="Issue metadata")
    specifications: SpecificationsState = Field(default_factory=SpecificationsState, description="Specifications state domain")
    comments: list[CommentItem] = Field(default_factory=list, description="Comments audit history")
