import requests

class HttpClient:
    def __init__(self):
        pass

    def get(self, url: str, headers: any, payload: any = None):
        return requests.request("GET", url, headers=headers, data=payload)
    
    def post(self, url: str, headers: any, payload: any = None):
        return requests.post(url, headers=headers, json=payload)
