from models.schemas import ResponseModel
class ResponseBuilder:
    def __init__(self):
        self._status = None
        self._statusCode = None
        self._data = None
        self._userIntent = None
        self._errorMessage = None

    def status(self, status: str):
        self._status = status
        return self

    def statusCode(self, code: int):
        self._statusCode = code
        return self

    def data(self, data):
        self._data = data
        return self

    def userIntent(self, userIntent: str):
        self._userIntent = userIntent
        return self

    def errorMessage(self, errorMessage: str):
        self._errorMessage = errorMessage
        return self

    def build(self) -> ResponseModel:
        return ResponseModel(
            status=self._status,
            statusCode=self._statusCode,
            data=self._data or [],
            userIntent=self._userIntent,
            errorMessage=self._errorMessage or None
        )
