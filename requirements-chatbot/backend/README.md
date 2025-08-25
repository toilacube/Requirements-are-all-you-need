
# Backend Service

This is a FastAPI backend service managed with [Poetry](https://python-poetry.org/).

---

## 🚀 Getting Started

### 1. Prerequisites
- Python **3.12**
- [Poetry](https://python-poetry.org/docs/#installation)

### 2. Install dependencies
```bash
poetry install
```

### 3. Activate the environment

```bash
poetry env activate
```

### 4. Run the server

```bash
make run
```

By default, the server runs on:
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🛠 Development

### Format code

```bash
make format
```

### Lint code

```bash
make lint
```

### Run tests

```bash
make test
```

---

## 📂 Project Structure

```bash
backend/
  __init__.py
  main.py        # FastAPI entrypoint

pyproject.toml   # Poetry project configuration
README.md
Makefile
```
