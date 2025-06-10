"""Database seeding utilities.

This module populates the database with deterministic data for local
development, demos and tests. The `seed_data` function can be invoked
explicitly from scripts or test fixtures.
"""

from sqlmodel import Session, select

from app.core.security import hash_password
from app.db.models import Dataset, Rule, User


def seed_data(session: Session) -> None:
    """Create initial users, datasets and rules if they do not already exist."""

    # Seed users
    users = {
        "owner@example.com": ("Owner", "Owner"),
        "reviewer@example.com": ("Reviewer", "Reviewer"),
        "viewer@example.com": ("Viewer", "Viewer"),
    }
    for email, (full_name, role) in users.items():
        existing_user = session.exec(select(User).where(User.email == email)).first()
        if not existing_user:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password("Passw0rd!"),
                role=role,
            )
            session.add(user)
    session.commit()

    # Seed dataset
    dataset_name = "sample_dataset"
    existing_dataset = session.exec(select(Dataset).where(Dataset.name == dataset_name)).first()
    if not existing_dataset:
        owner = session.exec(select(User).where(User.email == "owner@example.com")).first()
        dataset = Dataset(
            name=dataset_name,
            description="Synthetic sample dataset for demos and tests",
            owner_id=owner.id,
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)
        # Seed a completeness rule on the synthetic dataset
        rule = Rule(
            dataset_id=dataset.id,
            rule_type="completeness",
            params={"column": "value"},
            threshold=0.1,
            severity="warning",
            enabled=True,
        )
        session.add(rule)
    session.commit()