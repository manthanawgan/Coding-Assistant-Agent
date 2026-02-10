import re
from typing import Dict, List, Optional
from app.llm.gemini import GeminiLLM
from app.tools.code_parser import CodeParser
from app.tools.executor import CodeExecutor
from app.utils.prompts import SYSTEM_PROMPT, REACT_TEMPLATE

class CodingAgent:
    def __init__(self):
        self.llm = GeminiLLM()
        self.parser = CodeParser()
        self.executor = CodeExecutor()
        self.tools = {
            "parse_code": self._parse_code,
            "execute_code": self._execute_code,
            "analyze_complexity": self._analyze_complexity
        }
        
    async def process_request(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:           #process user request using ReAct pattern (not working properly :p)

        chat_history = chat_history or []
        max_iterations = 5 #might change later
        iteration = 0
        
        thoughts = []
        
        while iteration < max_iterations:
            prompt = REACT_TEMPLATE.format(
                system_prompt=SYSTEM_PROMPT,
                chat_history=self._format_history(chat_history),
                user_input=user_input
            )
            
            response = await self.llm.generate(prompt)
            thoughts.append(response)
            

            action = self._parse_action(response) #parsing response for actn.
            
            if action is None or action["type"] == "final_answer":
                final_answer = self._extract_final_answer(response)
                return {
                    "answer": final_answer,
                    "thoughts": thoughts,
                    "iterations": iteration + 1
                }
            
            tool_result = await self._execute_tool(action)
            
            user_input += f"\nObservation: {tool_result}"
            
            iteration += 1
        
        return {
            "answer": "I've reached the maximum number of reasoning steps. Please try breaking down your request.",
            "thoughts": thoughts,
            "iterations": iteration
        }
    
    def _parse_action(self, response: str) -> Optional[Dict]: #parsing llm reponse for actn
        #Lookin for Action: pattern
        action_match = re.search(r'Action:\s*(\w+)', response)
        input_match = re.search(r'Action Input:\s*(.+?)(?=\n|$)', response, re.DOTALL)
        
        if action_match:
            return {
                "type": "tool",
                "tool": action_match.group(1),
                "input": input_match.group(1).strip() if input_match else ""
            }
        
        if "Final Answer:" in response:
            return {"type": "final_answer"}
        
        return None
    
    def _extract_final_answer(self, response: str) -> str:
        match = re.search(r'Final Answer:\s*(.+)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response
    
    async def _execute_tool(self, action: Dict) -> str:
        tool_name = action["tool"]
        tool_input = action["input"]
        
        if tool_name in self.tools:
            try:
                result = await self.tools[tool_name](tool_input)
                return str(result)
            except Exception as e:
                return f"Tool execution failed: {str(e)}"
        
        return f"Unknown tool: {tool_name}"
    
    async def _parse_code(self, code: str) -> Dict:
        return self.parser.parse_code(code)
    
    async def _execute_code(self, code: str) -> Dict:
        return await self.executor.execute_python(code)
    
    async def _analyze_complexity(self, code: str) -> Dict:
        return self.parser.get_code_complexity(code)
    
    def _format_history(self, history: List[Dict]) -> str:
        formatted = []
        for msg in history[-5:]:  #last 5 msgs
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)