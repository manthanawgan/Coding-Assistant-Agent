from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from app.config.settings import settings
from app.config.logging import logger


class LLMRouter:
    def __init__(self):
        self.providers = {}

    def get_primary_model(self):
        if settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
                max_tokens=8192
            )
        elif settings.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                model=settings.ANTHROPIC_MODEL,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.2,
                max_tokens=8192
            )
        else:
            raise ValueError("No LLM provider configured")

    async def generate(
        self,
        messages: List[BaseMessage],
        max_tokens: int = 8192,
        temperature: float = 0.2
    ) -> str:
        try:
            model = self.get_primary_model()
            response = await model.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def analyze_code(self, code: str, task: str) -> str:
        system_prompt = """You are an expert software engineer. Analyze the provided code and help with the requested task.
Focus on understanding the codebase structure, identifying patterns, and suggesting improvements.
Be concise but thorough in your analysis."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Task: {task}\n\nCode to analyze:\n{code}")
        ]
        return await self.generate(messages)

    async def generate_code(self, prompt: str, context: str) -> str:
        system_prompt = """You are an expert software engineer generating code. You must:
1. Follow the existing code patterns and conventions
2. Write clean, well-documented code
3. Consider edge cases and error handling
4. Match the style of the existing codebase"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context}\n\nTask:\n{prompt}")
        ]
        return await self.generate(messages)

    async def fix_code(self, code: str, error: str, task: str) -> str:
        system_prompt = """You are an expert software engineer debugging code. Analyze the error and provide a fix.
Explain what was wrong and how you fixed it."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Task: {task}\n\nOriginal code:\n{code}\n\nError:\n{error}")
        ]
        return await self.generate(messages)


llm_router = LLMRouter()
