"""
Application constants - avoid magic numbers and strings
"""

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Gamification
LEADERBOARD_SIZE = 10
LEARNING_PATH_LIMIT = 5
DAILY_XP_GOAL = 50
STREAK_BONUS_XP = 25

# Proficiency levels
PROFICIENCY_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Challenge types
CHALLENGE_TYPES = {
    "DAILY": "daily",
    "WEEKLY": "weekly",
    "SPECIAL": "special"
}

# Session status
SESSION_STATUS = {
    "IN_PROGRESS": "IN_PROGRESS",
    "COMPLETED": "COMPLETED",
    "CANCELLED": "CANCELLED"
}

# Booking status
BOOKING_STATUS = {
    "PENDING": "PENDING",
    "CONFIRMED": "CONFIRMED",
    "COMPLETED": "COMPLETED",
    "CANCELLED": "CANCELLED"
}

# Mentor verification status
VERIFICATION_STATUS = {
    "PENDING": "PENDING",
    "VERIFIED": "VERIFIED",
    "REJECTED": "REJECTED"
}

# Industries for specialized topics
INDUSTRIES = [
    "BUSINESS",
    "TOURISM",
    "HEALTHCARE",
    "TECHNOLOGY",
    "EDUCATION",
    "DAILY_LIFE",
    "TRAVEL"
]

# Rate limiting (requests per minute)
RATE_LIMIT_AUTH = "10/minute"
RATE_LIMIT_API = "60/minute"
RATE_LIMIT_AI = "20/minute"
