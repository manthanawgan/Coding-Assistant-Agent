import google.generativeai as genai
from typing import List, Dict, Optional
from app.config import get_settings

class GeminiLLM:
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.chat_session = None
        
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> str:
        try:
            if history and not self.chat_session:
                #convert history to Gemini format
                formatted_history = self._format_history(history)
                self.chat_session = self.model.start_chat(history=formatted_history)
                response = self.chat_session.send_message(prompt)
            elif self.chat_session:
                response = self.chat_session.send_message(prompt)
            else:
                #single turn generatn
                if system_instruction:
                    model_with_system = genai.GenerativeModel(
                        get_settings().GEMINI_MODEL,
                        system_instruction=system_instruction
                    )
                    response = model_with_system.generate_content(prompt)
                else:
                    response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def _format_history(self, history: List[Dict]) -> List[Dict]: #for converting standard chat history into gemini format
        formatted = []
        for msg in history:
            formatted.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })
        return formatted
    
    def reset_session(self): #for new convo
        self.chat_session = None