.PHONY: setup backend frontend spark-job demo test check clean

# Create virtual environment and install backend and frontend dependencies
setup:
	python3 -m venv .venv && \
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r backend/requirements.txt && \
	cd frontend && npm install && cd ..

# Run the FastAPI backend with live reload
backend:
	cd backend && \
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run the React frontend in development mode
frontend:
	cd frontend && npm run dev

# Execute the quality job once using the local Spark simulation
spark-job:
	cd backend/jobs && python run_quality_job.py --once

# Start all services using Docker Compose for a full demo
demo:
	docker compose -f infra/docker-compose.yml up --build

# Run backend and frontend tests with coverage
test:
	cd backend && pytest -q --cov=app --cov-report=xml && cd ../frontend && npm run test --if-present

# Run static code checks, tests and type checks for the backend and frontend
check:
	cd backend && \
	ruff check . && \
	black --check . && \
	mypy . && \
	pytest -q --cov=app --cov-report=xml && \
	cd ../frontend && \
	npm run lint --if-present && \
	npm run typecheck --if-present

# Clean up build artefacts and remove Docker volumes
clean:
	rm -rf .venv frontend/node_modules backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache coverage.xml .coverage
	docker compose -f infra/docker-compose.yml down -v || true