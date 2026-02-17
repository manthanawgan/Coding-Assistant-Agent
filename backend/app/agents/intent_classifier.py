# app/agents/intent_classifier.py

class IntentClassifier:
    INTENTS = {
        "generate_code": [
            "write", "create", "make", "build", "generate",
            "implement", "code for", "function to", "class for"
        ],
        "explain_code": [
            "explain", "what does", "how does", "understand",
            "break down", "analyze this code"
        ],
        "debug_code": [
            "fix", "debug", "error", "bug", "not working",
            "wrong", "issue with", "problem with"
        ],
        "execute_code": [
            "run", "execute", "test", "try", "what output",
            "what happens", "result of"
        ],
        "review_code": [
            "review", "improve", "optimize", "better way",
            "refactor", "clean up", "best practices"
        ],
        "general_question": [
            "what is", "how to", "difference between",
            "when to use", "why", "concept"
        ]
    }
    
    def classify(self, user_message: str, has_code: bool) -> str: #for classifying user's intent
        message_lower = user_message.lower()
        
        has_code_block = "```" in user_message or has_code
        
        scores = {}         #score each inetent
        for intent, keywords in self.INTENTS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            scores[intent] = score
        
        max_intent = max(scores.items(), key=lambda x: x[1])        #hihghest scoring intent
        
        #including special case keywords aswell (temp)
        if has_code_block:
            if any(word in message_lower for word in ["fix", "debug", "error", "wrong"]):
                return "debug_code"
            elif any(word in message_lower for word in ["explain", "what", "how"]):
                return "explain_code"
            elif any(word in message_lower for word in ["run", "execute", "test"]):
                return "execute_code"
            else:
                return "review_code"
        
        #If asking to write/create/generate, it's code generation (shoudl chaneg this aswell)
        if max_intent[1] > 0:
            return max_intent[0]
        
        return "general_question"
    
    def extract_code(self, message: str) -> str: #extracting code block im
        import re
        code_block = re.search(r'```(?:\w+)?\n(.*?)```', message, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        return ""