from fastapi import HTTPException, status


class FileNotFoundError(HTTPException):
    def __init__(self, detail: str = "File not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class FileTooLargeError(HTTPException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {max_mb}MB",
        )


class UnsupportedFormatError(HTTPException):
    def __init__(self, fmt: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported video format: {fmt}",
        )


class CompressionError(HTTPException):
    def __init__(self, detail: str = "Video compression failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class AIServiceError(HTTPException):
    def __init__(self, detail: str = "AI service unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
