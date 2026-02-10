from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.config import get_settings
from app.agents.coding_agent import CodingAgent
from schemas import ChatRequest, ChatResponse
from tools.code_parser import CodeParser


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent = CodingAgent()

@app.get("/")
async def root():
    return {"message": "Coding Assistant API", "version": settings.VERSION}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        result = await agent.process_request(
            user_input=request.message,
            chat_history=history
        )
        
        return ChatResponse(
            response=result["answer"],
            thoughts=result.get("thoughts", []),
            metadata={"iterations": result.get("iterations", 0)}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze")
async def analyze_code(code: str):
    """Analyze code structure"""
    try:
        parser = CodeParser()
        analysis = parser.parse_code(code)
        complexity = parser.get_code_complexity(code)
        
        return {
            "analysis": analysis,
            "complexity": complexity
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)