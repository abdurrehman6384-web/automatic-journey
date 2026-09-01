.PHONY: help frontend backend test typecheck build doctor

help:
	@echo "Jinwoo AI commands"
	@echo "  make frontend   Start Vite dashboard"
	@echo "  make backend    Start FastAPI local API"
	@echo "  make test       Run backend unit tests"
	@echo "  make typecheck  Type-check the frontend"
	@echo "  make build      Build the frontend"
	@echo "  make doctor     Check local development prerequisites"

frontend:
	npm run dev

backend:
	python3 -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8787 --reload

test:
	python3 -m unittest discover -s backend/tests -v

typecheck:
	npm run typecheck

build:
	npm run build

doctor:
	@node --version
	@python3 --version
	@echo "Tip: run Ollama separately only if you want a real local model."
