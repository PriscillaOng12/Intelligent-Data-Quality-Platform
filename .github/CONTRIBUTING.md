# Contributing to Intelligent Data Quality Platform

Thank you for your interest in contributing to the Intelligent Data Quality Platform! This document provides guidelines and instructions for contributing to this project.

## 🎯 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- **Docker & Docker Compose** (20.10+)
- **Node.js** (18+) and npm
- **Python** (3.9+) with pip
- **Git** for version control

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/intelligent-data-quality-platform.git
   cd intelligent-data-quality-platform
   ```

3. **Set up the development environment**:
   ```bash
   make setup
   make dev-up
   ```

4. **Verify the setup**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Grafana: http://localhost:3001

## 📋 How to Contribute

### 🐛 Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Provide detailed information** including:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Screenshots/logs if applicable

### ✨ Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Provide detailed information** including:
   - Clear problem statement
   - Proposed solution
   - Use cases and business value
   - Technical considerations

### 🔧 Code Contributions

#### 1. Choose an Issue
- Look for issues labeled `good first issue` for beginners
- Check issues labeled `help wanted` for general contributions
- Comment on the issue to indicate you're working on it

#### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

#### 3. Make Your Changes
- **Follow coding standards** (see Style Guide below)
- **Write tests** for new functionality
- **Update documentation** as needed
- **Test your changes** thoroughly

#### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add new anomaly detection algorithm

- Implement isolation forest algorithm
- Add unit tests for new algorithm
- Update API documentation
"
```

**Commit Message Format:**
```
type(scope): short description

Longer description if needed
- List of changes
- More details
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

#### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a pull request using the provided template.

## 🏗️ Development Guidelines

### Project Structure
```
├── backend/           # Python FastAPI backend
├── frontend/          # React TypeScript frontend
├── docs/              # Documentation
├── infrastructure/    # Terraform and Kubernetes configs
├── scripts/           # Utility scripts
└── tests/             # Test files
```

### Backend Development (Python/FastAPI)

#### Code Style
- **PEP 8** compliance
- **Type hints** for all functions
- **Docstrings** for all public functions
- **Pydantic models** for data validation

#### Example:
```python
from typing import List, Optional
from pydantic import BaseModel

class DatasetResponse(BaseModel):
    """Response model for dataset information."""
    id: str
    name: str
    quality_score: Optional[float] = None
    
def get_datasets(limit: int = 10) -> List[DatasetResponse]:
    """Retrieve list of datasets with quality scores.
    
    Args:
        limit: Maximum number of datasets to return
        
    Returns:
        List of dataset information
    """
    # Implementation here
    pass
```

#### Testing
- **pytest** for unit tests
- **coverage** reports (aim for >80%)
- **Integration tests** for API endpoints
- **Mock external dependencies**

```bash
# Run backend tests
cd backend
pytest tests/ --cov=app --cov-report=html
```

### Frontend Development (React/TypeScript)

#### Code Style
- **ESLint** and **Prettier** configuration
- **TypeScript strict mode**
- **Functional components** with hooks
- **Material-UI** for consistent styling

#### Example:
```typescript
interface DatasetCardProps {
  dataset: Dataset;
  onSelect: (id: string) => void;
}

export const DatasetCard: React.FC<DatasetCardProps> = ({ 
  dataset, 
  onSelect 
}) => {
  const handleClick = useCallback(() => {
    onSelect(dataset.id);
  }, [dataset.id, onSelect]);

  return (
    <Card onClick={handleClick}>
      <CardContent>
        <Typography variant="h6">{dataset.name}</Typography>
        <Typography variant="body2">
          Quality Score: {dataset.qualityScore?.toFixed(2) ?? 'N/A'}
        </Typography>
      </CardContent>
    </Card>
  );
};
```

#### Testing
- **Jest** for unit tests
- **React Testing Library** for component tests
- **Cypress** for E2E tests

```bash
# Run frontend tests
cd frontend
npm test
npm run test:e2e
```

### Documentation

- **Markdown** for all documentation
- **Clear examples** and code snippets
- **Architecture diagrams** using Mermaid
- **API documentation** auto-generated from code

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only  
make test-frontend

# Integration tests
make test-integration
```

### Test Requirements
- **Unit tests** for all new functions/components
- **Integration tests** for API endpoints
- **E2E tests** for critical user flows
- **Performance tests** for optimization changes

## 📚 Documentation Updates

- Update relevant documentation for any changes
- Include code examples where helpful
- Update API documentation for backend changes
- Add screenshots for UI changes

## 🔍 Code Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Manual review** by maintainers
3. **Discussion** and feedback incorporation
4. **Approval** and merge

### Review Criteria
- Code quality and style compliance
- Test coverage and quality
- Documentation completeness
- Performance impact
- Security considerations

## 🏷️ Labels and Milestones

### Issue Labels
- **Type**: `bug`, `feature`, `documentation`, `question`
- **Priority**: `critical`, `high`, `medium`, `low`
- **Difficulty**: `good first issue`, `intermediate`, `advanced`
- **Status**: `needs-triage`, `in-progress`, `blocked`
- **Component**: `frontend`, `backend`, `infrastructure`, `docs`

### Pull Request Labels
- **Type**: `bug-fix`, `feature`, `enhancement`, `documentation`
- **Size**: `small`, `medium`, `large`
- **Status**: `work-in-progress`, `ready-for-review`, `changes-requested`

## 🚀 Release Process

1. **Feature freeze** for upcoming release
2. **Testing period** with release candidates
3. **Documentation** updates and review
4. **Release notes** preparation
5. **Version tagging** and deployment

## 💬 Communication

- **GitHub Issues** for bug reports and feature requests
- **GitHub Discussions** for questions and general discussion
- **Pull Request comments** for code-specific discussions

## 🙋 Getting Help

- Check the [documentation](docs/)
- Search existing [issues](https://github.com/your-username/intelligent-data-quality-platform/issues)
- Ask questions in [discussions](https://github.com/your-username/intelligent-data-quality-platform/discussions)
- Contact maintainers directly for urgent issues

## 📜 License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to the Intelligent Data Quality Platform! 🎉
