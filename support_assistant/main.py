from fastapi import FastAPI

from rag import SupportRequest, SupportResponse, ZeptoRAG

app = FastAPI(title="Zepto Support Assistant", version="1.0.0")
rag = ZeptoRAG()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=SupportResponse)
def ask(request: SupportRequest) -> SupportResponse:
    return rag.ask(request.query)
