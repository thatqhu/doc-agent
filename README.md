### Local Documents agent
    LangGraph + Adaptive RAG Agent + FastAPI + SSE + VUE3
    We should use local LLM in real env

##### How to use
    docker-compose up -d
    docker exec -it travel_frontend sh
    cd /app && npm install && npm run dev
    docker exec -it travel_frontend sh
    cd /app && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
##### How to development
    open vscode -> `attach to running container`
