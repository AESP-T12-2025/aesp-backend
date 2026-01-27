"""
Application Constants for AESP Backend
======================================
Centralized location for all magic numbers and configuration values.
Avoid hardcoding values throughout the codebase.
"""
from enum import Enum
from typing import Final


# =============================================================================
# PAGINATION
# =============================================================================

DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100
MIN_PAGE_SIZE: Final[int] = 1


# =============================================================================
# GAMIFICATION
# =============================================================================

LEADERBOARD_SIZE: Final[int] = 10
LEARNING_PATH_LIMIT: Final[int] = 5
DAILY_XP_GOAL: Final[int] = 50
STREAK_BONUS_XP: Final[int] = 25
MAX_XP_PER_SESSION: Final[int] = 100
STREAK_BREAK_DAYS: Final[int] = 1


# =============================================================================
# TIME PERIODS
# =============================================================================

DAYS_IN_WEEK: Final[int] = 7
DAYS_IN_MONTH: Final[int] = 30
HOURS_IN_DAY: Final[int] = 24
MINUTES_IN_HOUR: Final[int] = 60


# =============================================================================
# RATE LIMITING
# =============================================================================

RATE_LIMIT_AUTH: Final[str] = "10/minute"
RATE_LIMIT_API: Final[str] = "60/minute"
RATE_LIMIT_AI: Final[str] = "20/minute"
RATE_LIMIT_UPLOAD: Final[str] = "5/minute"


# =============================================================================
# ENUMS - Using Python Enum for type safety
# =============================================================================

class ProficiencyLevel(str, Enum):
    """CEFR Language Proficiency Levels"""
    A1 = "A1"  # Beginner
    A2 = "A2"  # Elementary
    B1 = "B1"  # Intermediate
    B2 = "B2"  # Upper Intermediate
    C1 = "C1"  # Advanced
    C2 = "C2"  # Proficient


class ChallengeType(str, Enum):
    """Types of learning challenges"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    SPECIAL = "SPECIAL"


class SessionStatus(str, Enum):
    """Status of a speaking session"""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class BookingStatus(str, Enum):
    """Status of a mentor booking"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class VerificationStatus(str, Enum):
    """Status of mentor verification"""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Industry(str, Enum):
    """Industry categories for specialized topics"""
    BUSINESS = "BUSINESS"
    TOURISM = "TOURISM"
    HEALTHCARE = "HEALTHCARE"
    TECHNOLOGY = "TECHNOLOGY"
    EDUCATION = "EDUCATION"
    DAILY_LIFE = "DAILY_LIFE"
    TRAVEL = "TRAVEL"


class TransactionStatus(str, Enum):
    """Status of a payment transaction"""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class SupportTicketStatus(str, Enum):
    """Status of a support ticket"""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


# =============================================================================
# ERROR CODES
# =============================================================================

class ErrorCode:
    """
    Standard error codes for API responses.
    Use these codes for consistent error handling across the API.
    """
    # Client errors (4xx)
    RESOURCE_NOT_FOUND: Final[str] = "RESOURCE_NOT_FOUND"
    VALIDATION_ERROR: Final[str] = "VALIDATION_ERROR"
    AUTHENTICATION_FAILED: Final[str] = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED: Final[str] = "AUTHORIZATION_FAILED"
    DUPLICATE_RESOURCE: Final[str] = "DUPLICATE_RESOURCE"
    RATE_LIMIT_EXCEEDED: Final[str] = "RATE_LIMIT_EXCEEDED"
    INVALID_INPUT: Final[str] = "INVALID_INPUT"
    
    # Server errors (5xx)
    INTERNAL_ERROR: Final[str] = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE: Final[str] = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR: Final[str] = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR: Final[str] = "EXTERNAL_SERVICE_ERROR"


# =============================================================================
# LEGACY CONSTANTS (For backward compatibility)
# =============================================================================

# Use ProficiencyLevel enum instead
PROFICIENCY_LEVELS = [level.value for level in ProficiencyLevel]

# Use ChallengeType enum instead
CHALLENGE_TYPES = {ct.name: ct.value for ct in ChallengeType}

# Use SessionStatus enum instead
SESSION_STATUS = {ss.name: ss.value for ss in SessionStatus}

# Use BookingStatus enum instead
BOOKING_STATUS = {bs.name: bs.value for bs in BookingStatus}

# Use VerificationStatus enum instead
VERIFICATION_STATUS = {vs.name: vs.value for vs in VerificationStatus}

# Use Industry enum instead
INDUSTRIES = [ind.value for ind in Industry]


# =============================================================================
# CONTENT LIMITS
# =============================================================================

MAX_TOPIC_TITLE_LENGTH: Final[int] = 200
MAX_SCENARIO_TITLE_LENGTH: Final[int] = 200
MAX_DESCRIPTION_LENGTH: Final[int] = 2000
MAX_COMMENT_LENGTH: Final[int] = 1000
MAX_BIO_LENGTH: Final[int] = 500


# =============================================================================
# FILE UPLOAD LIMITS
# =============================================================================

MAX_FILE_SIZE_MB: Final[int] = 10
MAX_IMAGE_SIZE_MB: Final[int] = 5
ALLOWED_IMAGE_EXTENSIONS: Final[tuple] = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
ALLOWED_AUDIO_EXTENSIONS: Final[tuple] = ('.mp3', '.wav', '.ogg', '.m4a')
