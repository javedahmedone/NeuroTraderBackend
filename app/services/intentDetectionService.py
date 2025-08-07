from transformers import pipeline
from rapidfuzz import fuzz

class IntentDetectionService:
    FUZZY_MATCH_THRESHOLD = 65
    pipe = pipeline("text2text-generation", model="google/flan-t5-base")

    INTENT_KEYWORDS = {
       "get_orders": ["my orders", "see orders", "show orders", "order history", "show my orders"],
        "place_order": ["place order", "buy order", "buy stock", "place new order", "buy shares", "purchase stock", "buy 1 stock", "purchase shares", "buy 1 share", "buy tata consultancy","i want to buy", "get me stock", "order shares"],
        "sell_order": ["sell order", "i want to sell", "sell my stock", "sell shares", "sell 1 stock", "sell tata consultancy"],
        "analyze_portfolio": ["analyze portfolio", "portfolio analysis", "how is my portfolio doing","suggest me new stocks", "review my portfolio", "analyze and suggest stocks", "portfolio performance", "analyze and recommend"],
        "view_holdings": ["view holdings", "my holdings", "stocks i own", "show holdings"],
        "get_total_holdings": ["how many stocks i have", "total stocks i hold", "number of stocks i own", "how many holdings", "count my stocks", "stock count",  "total quantity of holdings"]
    }


    def get_intent(self, prompt: str) -> str:
        # intent, score = self.best_fuzzy_intent(prompt)
        # # Prefer fuzzy if score is moderately good
        # if score >= 45:
        #     print(f"✅ Using fuzzy match: {intent} (score: {score})")
        #     return intent

        # Otherwise, use LLM
        query = (
            f"Classify the user's intent from this prompt: '{prompt}'\n"
            f"Choose from: {', '.join(self.INTENT_KEYWORDS.keys())}.\n"
            f"Reply with only the matching option."
        )
        result = self.pipe(query, max_length=10, do_sample=False)[0]
        response = result.get('generated_text', '').strip().lower()
        print("🧠 LLM Raw Output:", response)

        if response in self.INTENT_KEYWORDS:
            print(f"✅ LLM matched: {response}")
            return response

        return "unknown"


    def best_fuzzy_intent(self, prompt: str):
        prompt_lower = prompt.lower().strip()
        if "sell" in prompt_lower:
            return "sell_order", 100
        elif "buy" in prompt_lower:
            return "place_order", 100
        best_intent = None
        best_score = 0
        best_phrase = ""
        for intent, phrases in self.INTENT_KEYWORDS.items():
            for phrase in phrases:
                score = fuzz.ratio(prompt_lower, phrase)
                if score > best_score:
                    best_score = score
                    best_intent = intent
                    best_phrase = phrase

        print(f"🧠 Fuzzy best match: '{best_phrase}' → '{best_intent}' with score {best_score}")
        return best_intent, best_score   

   