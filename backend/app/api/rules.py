"""Rule management endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.rbac import require_role
from app.core.security import get_current_active_user
from app.db.models import Dataset, Rule, User
from app.db.session import get_session
from app.schemas import RuleCreate, RuleRead


router = APIRouter()


@router.get("/", response_model=List[RuleRead])
def list_rules(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    session: Session = Depends(get_session),
) -> List[RuleRead]:
    """Return all rules, optionally filtering by dataset."""

    statement = select(Rule)
    if dataset_id is not None:
        statement = statement.where(Rule.dataset_id == dataset_id)
    rules = session.exec(statement).all()
    return rules


@router.post(
    "/",
    response_model=RuleRead,
    dependencies=[Depends(require_role("Owner", "Maintainer"))],
)
def create_rule(
    rule_in: RuleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> RuleRead:
    """Create a new quality rule for a dataset."""

    dataset = session.get(Dataset, rule_in.dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    # Basic validation: severity
    if rule_in.severity not in {"info", "warning", "critical"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity")
    rule = Rule(
        dataset_id=rule_in.dataset_id,
        rule_type=rule_in.rule_type,
        params=rule_in.params,
        threshold=rule_in.threshold,
        severity=rule_in.severity,
        enabled=rule_in.enabled,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(rule_id: int, session: Session = Depends(get_session)) -> RuleRead:
    """Return a single rule by its ID."""

    rule = session.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=RuleRead, dependencies=[Depends(require_role("Owner", "Maintainer"))])
def update_rule(
    rule_id: int,
    rule_in: RuleCreate,
    session: Session = Depends(get_session),
) -> RuleRead:
    """Update an existing rule. All fields are replaced."""

    rule = session.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    rule.rule_type = rule_in.rule_type
    rule.params = rule_in.params
    rule.threshold = rule_in.threshold
    rule.severity = rule_in.severity
    rule.enabled = rule_in.enabled
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule