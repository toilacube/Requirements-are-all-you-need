
### 🔥 How to use

1. **Init setup (first time) make sure you have `make` in your system**

   ```bash
   make init
   ```

   * Creates Python venv → installs FastAPI dependencies
   * Installs frontend deps (`npm install`)

2. **Run locally (both backend + frontend)**

   ```bash
   make run
   ```

   * Starts FastAPI (`uvicorn`) on `http://localhost:8000`
   * Starts Vite (`npm run dev`) on `http://localhost:5173`

3. **Clean everything**

   ```bash
   make clean
   ```

   * Removes `venv`, `node_modules`, and `__pycache__`


