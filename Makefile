.PHONY: api web test docker-up docker-down seed

api:
	cd apps/api && python -m uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	cd apps/api && pytest

docker-up:
	docker compose up --build

docker-down:
	docker compose down

seed:
	cd apps/api && python scripts/seed_demo.py
