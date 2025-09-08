import os
class GetSecrets:
    def __init__(self):
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")  
        self.BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    
    def getFrontendUrl(self):
        return self.FRONTEND_URL
    
    def getBackendUrl(self):
        return self.BACKEND_URL
    
