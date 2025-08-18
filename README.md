# 📌 AI-Powered Stock Trading Backend  

This repository contains the **backend service** for an **AI-driven stock trading assistant**.  
The service enables users to **buy, sell, or cancel stock orders using natural language prompts**.  

The backend leverages:  
- **Google Gemini** → for analyzing user prompts and extracting trading intent  
- **Redis** → for caching stock data, user sessions, and quick lookups  
- **Python (FastAPI/Flask)** → REST API server  
- **Broker APIs** → to execute buy/sell/cancel orders  

---

## 🚀 Features  

- 🔹 **Natural Language Trading** – Users can simply type prompts like *“Buy 5 shares of TCS”* or *“Cancel my last order”*.  
- 🔹 **Google Gemini Integration** – Converts unstructured prompts into structured trade requests.  
- 🔹 **Order Management** – Supports placing new orders, cancelling existing ones, and fetching portfolio/holdings.  
- 🔹 **Redis Caching** – Stores frequently accessed stock symbols, tokens, and user sessions for high performance.  
- 🔹 **Secure Auth Flow** – Manages JWT tokens, broker credentials, and refresh tokens.  
- 🔹 **Modular Architecture** – Clear separation of **AI inference**, **order execution**, and **data caching**.  

---

## 🛠️ Tech Stack  

- **Language**: Python 3.10+  
- **Framework**: FastAPI  
- **AI**: Google Gemini API  
- **Cache/DB**: Redis (UpStash)
- **Deployment**: Render / Docker / Railway  
- **Others**: Pydantic, Requests/HTTPX  

---

 

