from google import genai
import json
from app.global_constant import constants
import re

INTENT_KEYWORDS = {
    "get_orders": [
        "my orders", "see orders", "show orders", "order history", "show my orders"
    ],
    "place_order": [
        "place order", "buy order", "buy stock", "place new order", "buy shares",
        "purchase stock", "buy 1 stock", "purchase shares", "buy 1 share",
        "buy tata consultancy", "i want to buy", "get me stock", "order shares"
    ],
    "sell_order": [
        "sell order", "i want to sell", "sell my stock", "sell shares",
        "sell 1 stock"
    ],
    "sell_all": [
        "sell all", "sell all stocks", "sell my entire portfolio",
        "liquidate all stocks", "sell everything", "empty my portfolio"
    ],
    "analyze_portfolio": [
        "analyze portfolio", "portfolio analysis", "how is my portfolio doing",
        "suggest me new stocks", "review my portfolio", "analyze and suggest stocks",
        "portfolio performance", "analyze and recommend"
    ],
    "view_holdings": [
        "view holdings", "my holdings", "stocks i own", "show holdings"
    ],
    "get_total_holdings": [
        "how many stocks i have", "total stocks i hold", "number of stocks i own",
        "how many holdings", "count my stocks", "stock count", "total quantity of holdings"
    ],
    "cancel_order": [
        "cancel order", "cancel my order", "delete my order", "remove order",
        "i want to cancel my order", "cancel placed order", "cancel the order",
        "please cancel my order", "revoke my order", "abort the order",
        "cancel my order with id", "cancel these orders", "cancel order id",
        "cancel order number"
    ],
    "cancel_all": [
        "cancel all", "cancel all orders", "delete all orders", "remove all orders",
        "cancel everything", "cancel all my orders", "abort all orders",
        "revoke all orders", "clear all orders"
    ]
}


class GeminiService:

    def __init__(self):
        self.client = genai.Client(api_key= constants.GEMINI_API_KEY )

    def processUserRequest(self, data , userPrompt: str):
        json_data = json.dumps(data, indent=2)
        prompt = f"""Here is the user's current stock holding data in JSON:
        {json_data}

        {userPrompt}
        give me answer in 500 words
        """
        response = self.client.models.generate_content(
            model="gemini-1.5-flash", contents=prompt
        )
        return response.text


    def generate_full_prompt(self, user_input: str): 
            categories = "\n".join([f"{k}: {v}" for k, v in INTENT_KEYWORDS.items()])
            prompt = f"""
            You are an intelligent assistant that classifies user input and extracts stock trading details.
            ### Categories:
            {categories}
            ### Task:
            1. From the user input below, identify the **intent**. Only use keys: {", ".join(INTENT_KEYWORDS.keys())}. If nothing matches, reply "unknown".
            2. Extract the **stock name** (if mentioned).
            3. Extract the **quantity** (if mentioned, as a number, else null).
            4. Extract all **order IDs** mentioned (as an array of numbers, else empty array).


            ### Format your response as JSON give me clean json no extra quotes:
            {{
            "intent": "one_of_the_keys_or_unknown",
            "stock_name": "stock name or null",
            "quantity": number or null,
            "orderids": [list of numbers or empty array]

            }}
            ### User input:
            "{user_input}"
            """
            return prompt

    def detect_intent(self, user_input: str):
        prompt = self.generate_full_prompt(user_input)
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        try:
            cleaned = re.sub(r"```json|```", "", response.text).strip()
            data = json.loads(cleaned)
            intent = data.get("intent", "unknown").strip().lower()
            if intent not in INTENT_KEYWORDS and intent != "unknown":
                intent = "unknown"
            return {
                "intent": intent,
                "stock_name": data.get("stock_name"),
                "quantity": data.get("quantity"),
                "orderids": data.get("orderids", [])
            }
        except Exception as e:
            print("❌ Failed to parse Gemini response:", response.text)
            return {
                "intent": "unknown",
                "stock_name": None,
                "quantity": None
            }
