# ==========
# Variables
# ==========
PYTHON       = poetry run python
UVICORN      = poetry run uvicorn
BACKEND_DIR  = backend
FRONTEND_DIR = frontend
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# ==========
# Backend
# ==========
init-backend:
	cd $(BACKEND_DIR) && poetry config virtualenvs.in-project true
	cd $(BACKEND_DIR) && poetry install

run-backend:
	cd $(BACKEND_DIR) && $(UVICORN) main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

# ==========
# Frontend
# ==========
init-frontend:
	cd $(FRONTEND_DIR) && pnpm install

run-frontend:
	cd $(FRONTEND_DIR) && pnpm run dev -- --port $(FRONTEND_PORT)

# ==========
# Combined
# ==========
init: init-backend init-frontend

run:
	@echo "🚀 Starting backend and frontend..."
	@$(MAKE) -j2 run-backend run-frontend

# ==========
# Utilities
# ==========
format:
	cd $(BACKEND_DIR) && poetry run black .

lint:
	cd $(BACKEND_DIR) && poetry run flake8 .

test:
	cd $(BACKEND_DIR) && poetry run pytest -v

clean:
	cd $(BACKEND_DIR) && poetry env remove --all || true
	rm -rf $(BACKEND_DIR)/.venv
