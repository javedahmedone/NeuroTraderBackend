class HeaderBuilder:
    def __init__(self):
        self._headers = {}

    def with_content_type(self, content_type):
        self._headers["Content-Type"] = content_type
        return self

    def with_auth(self, token: str | None):
        self._headers["Authorization"] = token
        return self

    def with_custom(self, key: str, value: str):
        self._headers[key] = value
        return self

    def build(self) -> dict:
        # Fallback: ensure Content-Type is always set
        if "Content-Type" not in self._headers:
            self._headers["Content-Type"] = "application/json"
        return self._headers
