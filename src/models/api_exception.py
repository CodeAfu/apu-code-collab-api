class APIException(Exception):
    def __init__(self, status_code: int = 500, error: str = "INTERNAL_SERVER_ERROR", message: str = None):
        self.status_code = status_code
        self.error = error
        self.message = message