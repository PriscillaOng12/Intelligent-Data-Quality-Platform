"""Dataset management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.rbac import require_role
from app.core.security import get_current_active_user
from app.db.models import Dataset, User
from app.db.session import get_session
from app.schemas import DatasetCreate, DatasetRead


router = APIRouter()


@router.get("/", response_model=list[DatasetRead])
def list_datasets(session: Session = Depends(get_session)) -> list[DatasetRead]:
    """Return all datasets accessible to the current user.

    For now, returns all datasets without scoping by tenant. Multi-tenancy could
    be added by filtering on the current user's tenant id.
    """

    statement = select(Dataset)
    datasets = session.exec(statement).all()
    return datasets


@router.post("/", response_model=DatasetRead, dependencies=[Depends(require_role("Owner", "Maintainer"))])
def create_dataset(
    dataset_in: DatasetCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> DatasetRead:
    """Create a new dataset. Only Owners and Maintainers can create datasets."""

    existing = session.exec(select(Dataset).where(Dataset.name == dataset_in.name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dataset already exists")
    dataset = Dataset(
        name=dataset_in.name,
        description=dataset_in.description,
        owner_id=current_user.id,
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, session: Session = Depends(get_session)) -> DatasetRead:
    """Retrieve a dataset by its ID."""

    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset