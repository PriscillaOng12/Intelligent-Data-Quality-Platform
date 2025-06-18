"""Load rule definitions from YAML into the database.

Usage:

```bash
python load_rules.py --file rules.yml
```

The YAML file should contain a top‑level list of rule definitions with keys:
`dataset`, `rule_type`, `params`, `threshold`, `severity`, `enabled`.
Datasets are created implicitly if they do not exist.
"""

import argparse
import yaml
from sqlmodel import Session, select

from app.core.security import hash_password
from app.db.models import Dataset, Rule, User
from app.db.session import get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Load rule definitions from YAML")
    parser.add_argument("--file", type=str, required=True, help="Path to YAML file")
    args = parser.parse_args()
    with open(args.file, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)
    with get_session() as session:
        for rule_def in rules:
            dataset_name = rule_def["dataset"]
            dataset = session.exec(select(Dataset).where(Dataset.name == dataset_name)).first()
            if not dataset:
                # Create a dataset owned by the first user
                user = session.exec(select(User)).first()
                dataset = Dataset(name=dataset_name, description="", owner_id=user.id)
                session.add(dataset)
                session.commit()
                session.refresh(dataset)
            rule = Rule(
                dataset_id=dataset.id,
                rule_type=rule_def["rule_type"],
                params=rule_def.get("params", {}),
                threshold=rule_def.get("threshold", 0.0),
                severity=rule_def.get("severity", "warning"),
                enabled=rule_def.get("enabled", True),
            )
            session.add(rule)
        session.commit()
    print(f"Loaded {len(rules)} rules from {args.file}")


if __name__ == "__main__":
    main()