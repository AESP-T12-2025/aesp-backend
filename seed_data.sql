-- 1. Insert Categories
INSERT INTO categories (name, description)
VALUES (
        'Business English',
        'For workplace and professional settings'
    ),
    (
        'Travel & Tourism',
        'Essential phrases for travelers'
    ),
    (
        'Daily Conversation',
        'Casual chats and everyday scenarios'
    ),
    ('Technology', 'IT, AI, and modern tech terms'),
    (
        'Culture & Arts',
        'Discussing movies, books, and traditions'
    ) ON CONFLICT (category_id) DO NOTHING;
-- 2. Insert Topics (Assuming IDs 1-5 from above categories for simplicity in raw SQL, 
-- or we can use subqueries but raw IDs are often easier for quick seed)
-- We will use subqueries to be safe.
INSERT INTO topics (category_id, name, description)
VALUES (
        (
            SELECT category_id
            FROM categories
            WHERE name = 'Business English'
        ),
        'Job Interview',
        'Common interview questions'
    ),
    (
        (
            SELECT category_id
            FROM categories
            WHERE name = 'Business English'
        ),
        'Meeting Etiquette',
        'How to speak in meetings'
    ),
    (
        (
            SELECT category_id
            FROM categories
            WHERE name = 'Travel & Tourism'
        ),
        'At the Airport',
        'Check-in and customs'
    ),
    (
        (
            SELECT category_id
            FROM categories
            WHERE name = 'Travel & Tourism'
        ),
        'Booking Hotel',
        'Reservations and inquiries'
    ),
    (
        (
            SELECT category_id
            FROM categories
            WHERE name = 'Daily Conversation'
        ),
        'Ordering Coffee',
        'Cafes and restaurants'
    ),
    (
        (
            SELECT category_id
            FROM categories
            WHERE name = 'Daily Conversation'
        ),
        'Making Friends',
        'Introductions and small talk'
    );
-- 3. Insert Scenarios (BEGINNER, INTERMEDIATE, ADVANCED levels)
INSERT INTO scenarios (
        topic_id,
        title,
        difficulty_level,
        script_content,
        key_phrases
    )
VALUES -- BEGINNER Level Scenarios
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Job Interview'
        ),
        'Basic Job Interview',
        'BEGINNER',
        'A: Tell me about yourself.\nB: I am a student. I study English. I like reading books.',
        '{"tell me": "Kể cho tôi nghe", "about yourself": "Về bản thân bạn"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Ordering Coffee'
        ),
        'Ordering at a Cafe',
        'BEGINNER',
        'A: Can I have a latte?\nB: Sure, anything else?\nA: No, thank you.',
        '{"latte": "Cà phê latte", "anything else": "Còn gì nữa không"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Making Friends'
        ),
        'Simple Introductions',
        'BEGINNER',
        'A: Hi! My name is John. What is your name?\nB: Hello! I am Mary. Nice to meet you!',
        '{"nice to meet you": "Rất vui được gặp bạn"}'
    ),
    -- INTERMEDIATE Level Scenarios
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Job Interview'
        ),
        'Professional Job Interview',
        'INTERMEDIATE',
        'A: What are your strengths and weaknesses?\nB: My strength is problem-solving. I sometimes focus too much on details, which can slow me down.',
        '{"strengths": "Điểm mạnh", "weaknesses": "Điểm yếu", "problem-solving": "Giải quyết vấn đề"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Meeting Etiquette'
        ),
        'Business Meeting',
        'INTERMEDIATE',
        'A: Lets move on to the next agenda item.\nB: Before we proceed, I would like to raise a concern about the timeline.',
        '{"agenda item": "Mục chương trình", "raise a concern": "Nêu một lo ngại"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'At the Airport'
        ),
        'Airport Navigation',
        'INTERMEDIATE',
        'A: I need to check in for my flight to New York.\nB: May I see your passport and booking confirmation?\nA: Here you go. Could I get a window seat please?',
        '{"check in": "Làm thủ tục", "booking confirmation": "Xác nhận đặt chỗ"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Booking Hotel'
        ),
        'Hotel Reservation',
        'INTERMEDIATE',
        'A: I would like to make a reservation for next weekend.\nB: What type of room would you prefer?\nA: A double room with a city view, please.',
        '{"reservation": "Đặt phòng", "city view": "View thành phố"}'
    ),
    -- ADVANCED Level Scenarios
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Job Interview'
        ),
        'Executive Interview',
        'ADVANCED',
        'A: How would you handle a situation where your team disagrees with a major strategic decision?\nB: I believe in transparent communication. I would facilitate a discussion to understand concerns, present data-driven arguments, and work toward consensus while maintaining executive authority.',
        '{"strategic decision": "Quyết định chiến lược", "data-driven": "Dựa trên dữ liệu", "consensus": "Đồng thuận"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Meeting Etiquette'
        ),
        'High-Stakes Negotiation',
        'ADVANCED',
        'A: We need to finalize the terms before the board meeting.\nB: I appreciate the urgency, however, there are still outstanding issues regarding the equity split and vesting schedule that require further deliberation.',
        '{"outstanding issues": "Vấn đề tồn đọng", "equity split": "Phân chia cổ phần", "vesting schedule": "Lịch trình vesting"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'At the Airport'
        ),
        'International Transit',
        'ADVANCED',
        'A: I have a connecting flight but my baggage seems to be missing from the carousel.\nB: Let me check the system. It appears your luggage was held for security screening and will be forwarded to your final destination.',
        '{"connecting flight": "Chuyến bay nối chuyến", "security screening": "Kiểm tra an ninh"}'
    ) ON CONFLICT DO NOTHING;
-- 4. Reset Proficiency Test to force new 25-question test creation
-- (Uncomment and run if you want to reset the test)
-- DELETE FROM proficiency_tests WHERE title = 'General Placement Test';