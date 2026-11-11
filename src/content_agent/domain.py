"""Input and state contracts. Money is measured in integer simulation units."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import hashlib
import json


class TaskStatus(StrEnum):
    NEEDS_INPUT = "needs_input"
    RUNNING = "running"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    INVALIDATED = "invalidated"


@dataclass(frozen=True)
class Request:
    request_id: str
    theme: str
    budget: int
    deadline: datetime

    def fingerprint(self) -> str:
        from datetime import timezone
        payload = {"theme": self.theme, "budget": self.budget,
                   "deadline": self.deadline.astimezone(timezone.utc).isoformat()}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@dataclass
class Validation:
    request: Request | None = None
    missing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_request(raw: dict, *, now: datetime) -> Validation:
    """No tool side effects; callers must stop when request is None."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must include a timezone")
    result = Validation()
    if not isinstance(raw, dict):
        result.errors.append("input must be an object")
        return result
    for key in ("request_id", "theme", "budget", "deadline"):
        if key not in raw or raw[key] is None or raw[key] == "":
            result.missing.append(key)
    for key in ("request_id", "theme"):
        if key not in result.missing and (not isinstance(raw[key], str) or not raw[key].strip()):
            result.errors.append(f"{key} must be a non-empty string")
    budget = raw.get("budget")
    if "budget" not in result.missing and (type(budget) is not int or budget < 0):
        result.errors.append("budget must be a non-negative integer")
    deadline = None
    if "deadline" not in result.missing:
        try:
            deadline = datetime.fromisoformat(raw["deadline"])
            if deadline.tzinfo is None or deadline.utcoffset() is None:
                result.errors.append("deadline must include a timezone")
            elif deadline <= now:
                result.errors.append("deadline must be in the future")
        except (TypeError, ValueError):
            result.errors.append("deadline must be an ISO 8601 string")
    if not result.errors and not result.missing:
        result.request = Request(raw["request_id"].strip(), raw["theme"].strip(), budget, deadline)
    return result


@dataclass
class StepResult:
    name: str
    status: StepStatus = StepStatus.PENDING
    result: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class RunState:
    request_id: str
    status: TaskStatus = TaskStatus.RUNNING
    steps: list[StepResult] = field(default_factory=list)
    actual_tool_cost: int = 0
    remaining_plan_cost: int = 0
    plan_version: int = 0
    saved_plan_id: str | None = None
    reason: str | None = None
