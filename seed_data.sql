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
-- 3. Insert Scenarios
INSERT INTO scenarios (
        topic_id,
        title,
        difficulty_level,
        script_content,
        key_phrases
    )
VALUES (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Job Interview'
        ),
        'Scenario for Job Interview',
        'BEGINNER',
        'A: Tell me about yourself.\nB: I am a software engineer with 5 years of experience.',
        '{"tell me": "Ke cho toi nghe", "experience": "Kinh nghiem"}'
    ),
    (
        (
            SELECT topic_id
            FROM topics
            WHERE name = 'Ordering Coffee'
        ),
        'Scenario for Ordering Coffee',
        'BEGINNER',
        'A: Can I have a latte?\nB: Sure, anything else?',
        '{"latte": "Ca phe latte", "anything else": "Con gi nua khong"}'
    );