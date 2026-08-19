"""The shapes crossing the HTTP boundary.

Separate from the graph's own state: the API is a contract with a browser and
should not change every time a node gains an internal field.
"""

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal['chat', 'knowledge', 'code']


class Citation(BaseModel):
    """A corpus passage an answer was drawn from."""

    source: str
    heading: str
    text: str
    score: float


class TraceEvent(BaseModel):
    """One node's turn, recorded so the client can show how an answer arrived."""

    node: str
    detail: str = ''
    elapsed_ms: int = 0


class FileEdit(BaseModel):
    path: str = Field(description='Path relative to the workspace root.')
    new_content: str = Field(description='The complete new contents of the file.')


class CodeProposal(BaseModel):
    """A change the coding agent wants to make, pending human approval.

    Mirrors what contributing.md requires of a pull request, because a proposal
    that cannot be turned into a compliant PR is not finished.
    """

    summary: str = Field(description='What changes, in one or two sentences.')
    rationale: str = Field(description='Why now: the ADR, incident or contract that motivates it.')
    verification: str = Field(description='The test that fails without this change.')
    adrs_consulted: list[str] = Field(
        default_factory=list, description='Knowledge-base documents this change was grounded in.'
    )
    branch: str = Field(description='Branch name, type/short-description.')
    commit_message: str = Field(description='Conventional commit subject line.')
    edits: list[FileEdit] = Field(default_factory=list)


class PullRequest(BaseModel):
    """The review artifact produced once a proposal is approved and applied."""

    branch: str
    title: str
    body: str
    diff: str
    checks: list['CheckResult'] = Field(default_factory=list)


class CheckResult(BaseModel):
    """One CI job's outcome, run locally against the workspace."""

    name: str
    passed: bool
    output: str = ''


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ApprovalRequest(BaseModel):
    thread_id: str
    decision: str = Field(description="'approve', 'deny', or revised instructions.")


class ChatResponse(BaseModel):
    thread_id: str
    status: Literal['complete', 'awaiting_approval']
    intent: Intent | None = None
    reply: str = ''
    citations: list[Citation] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    proposal: CodeProposal | None = None
    diff: str = ''
    # Review rules the proposal still breaks. Shown rather than hidden: a change
    # CI would reject is something the approver should know before approving.
    violations: list[str] = Field(default_factory=list)
    pull_request: PullRequest | None = None
