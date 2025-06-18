"""Incident management endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.rate_limit import enforce_rate_limit
from app.core.rbac import require_role
from app.core.security import get_current_active_user
from app.db.models import Acknowledgement, Incident, Rule, User
from app.db.session import get_session
from app.schemas import AcknowledgementCreate, IncidentRead


router = APIRouter()


@router.get("/", response_model=List[IncidentRead])
def list_incidents(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    rule_id: Optional[int] = Query(None, description="Filter by rule ID"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
) -> List[IncidentRead]:
    """Return a list of incidents with optional filtering and pagination."""

    statement = select(Incident)
    if dataset_id is not None:
        statement = statement.where(Incident.dataset_id == dataset_id)
    if rule_id is not None:
        statement = statement.where(Incident.rule_id == rule_id)
    if acknowledged is not None:
        statement = statement.where(Incident.acknowledged == acknowledged)
    statement = statement.offset(offset).limit(limit)
    incidents = session.exec(statement).all()
    return incidents


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: int, session: Session = Depends(get_session)) -> IncidentRead:
    """Retrieve a single incident by its ID."""

    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post(
    "/{incident_id}/acknowledge",
    dependencies=[Depends(require_role("Owner", "Maintainer", "Reviewer")), Depends(enforce_rate_limit)],
    response_model=IncidentRead,
)
def acknowledge_incident(
    incident_id: int,
    ack: AcknowledgementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> IncidentRead:
    """Mark an incident as acknowledged with an optional comment."""

    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if incident.acknowledged:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incident already acknowledged")
    incident.acknowledged = True
    acknowledgement = Acknowledgement(
        incident_id=incident.id,
        user_id=current_user.id,
        comment=ack.comment,
    )
    session.add(acknowledgement)
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident