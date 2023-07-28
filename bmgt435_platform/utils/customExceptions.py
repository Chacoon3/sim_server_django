
class DataFormatError(Exception):

    def __init__(self, message: str | None = None):
        self.message = message or "The provided data format does not meet requirements."


    def __str__(self) -> str:
        return self.message