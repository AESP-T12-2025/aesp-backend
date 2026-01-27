"""
Custom Exceptions and Error Handling for AESP Backend
======================================================
Provides standardized error responses across the API with:
- Custom exception classes for common HTTP error scenarios
- Centralized exception handlers for consistent response format
- Error code mapping for client-side error handling
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict, List, Optional, Union
import logging
import traceback

from app.core.constants import ErrorCode

logger = logging.getLogger(__name__)


# =============================================================================
# BASE EXCEPTION
# =============================================================================

class APIException(HTTPException):
    """
    Base exception for API errors with standardized format.
    
    All custom exceptions should inherit from this class.
    
    Attributes:
        status_code: HTTP status code
        error_code: Application-specific error code for client handling
        message: Human-readable error message
        details: Additional error details (optional)
    
    Example:
        >>> raise APIException(
        ...     status_code=400,
        ...     error_code="INVALID_EMAIL",
        ...     message="Email format is invalid",
        ...     details={"field": "email", "value": "not-an-email"}
        ... )
    """
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


# =============================================================================
# CLIENT ERROR EXCEPTIONS (4xx)
# =============================================================================

class ValidationException(APIException):
    """
    Validation error (400 Bad Request).
    
    Use when request data fails validation checks.
    """
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, str]]] = None
    ):
        if errors:
            details = details or {}
            details["errors"] = errors
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )


class AuthenticationException(APIException):
    """
    Authentication failed (401 Unauthorized).
    
    Use when authentication credentials are missing or invalid.
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            message=message,
            details=details
        )


class AuthorizationException(APIException):
    """
    Authorization failed (403 Forbidden).
    
    Use when user is authenticated but lacks permission for the action.
    """
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.AUTHORIZATION_FAILED,
            message=message,
            details=details
        )


class NotFoundException(APIException):
    """
    Resource not found (404 Not Found).
    
    Use when a requested resource does not exist.
    """
    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[Union[int, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} not found"
        if resource_id is not None:
            message = f"{resource} with ID {resource_id} not found"
            details = details or {}
            details["resource_id"] = resource_id
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=details
        )


class DuplicateResourceException(APIException):
    """
    Resource already exists (409 Conflict).
    
    Use when attempting to create a resource that already exists.
    """
    def __init__(
        self,
        resource: str = "Resource",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} already exists"
        if field:
            message = f"{resource} with this {field} already exists"
            details = details or {}
            details["field"] = field
        
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.DUPLICATE_RESOURCE,
            message=message,
            details=details
        )


class RateLimitException(APIException):
    """
    Rate limit exceeded (429 Too Many Requests).
    
    Use when user has exceeded the rate limit.
    """
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if retry_after:
            details = details or {}
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=details
        )


# =============================================================================
# SERVER ERROR EXCEPTIONS (5xx)
# =============================================================================

class InternalServerException(APIException):
    """
    Internal server error (500).
    
    Use for unexpected server-side errors.
    """
    def __init__(
        self,
        message: str = "An internal error occurred",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details
        )


class ServiceUnavailableException(APIException):
    """
    Service unavailable (503).
    
    Use when an external service is unavailable.
    """
    def __init__(
        self,
        service: str = "Service",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message=f"{service} is temporarily unavailable",
            details=details
        )


# =============================================================================
# ERROR RESPONSE HELPERS
# =============================================================================

def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response format.
    
    Args:
        error_code: Application-specific error code
        message: Human-readable error message
        details: Additional error details
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {}
        }
    }


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handler for APIException to return standardized format.
    
    This handler catches all APIException subclasses and formats
    them into a consistent JSON response.
    """
    logger.warning(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for standard HTTPException - convert to standard format.
    
    Maps HTTP status codes to application error codes.
    """
    status_to_error_code = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_FAILED,
        403: ErrorCode.AUTHORIZATION_FAILED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        409: ErrorCode.DUPLICATE_RESOURCE,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE
    }
    
    error_code = status_to_error_code.get(
        exc.status_code,
        ErrorCode.INTERNAL_ERROR
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=error_code,
            message=str(exc.detail)
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for Pydantic validation errors.
    
    Formats validation errors into a user-friendly format.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.info(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            details={"errors": errors}
        )
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions.
    
    Logs the full stack trace and returns a generic error message
    to avoid exposing internal details.
    """
    # Log full exception details
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred"
        )
    )


# =============================================================================
# CONVENIENCE FUNCTION TO REGISTER HANDLERS
# =============================================================================

def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> from app.core.exceptions import register_exception_handlers
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("✅ Exception handlers registered")
