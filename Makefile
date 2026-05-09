.PHONY: api agents web test docker-up docker-down seed

api:
	cd apps/api && npm run dev

agents:
	cd apps/agents && python -m uvicorn app.main:app --reload --port 8001

web:
	cd apps/web && npm run dev

test:
	cd apps/agents && pytest

docker-up:
	docker compose up --build

docker-down:
	docker compose down

seed:
	cd apps/agents && python scripts/seed_demo.py
