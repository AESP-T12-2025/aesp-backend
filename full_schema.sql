-- Clean up existing schema to ensure clean import (Optional, but recommended for full sync)
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
-- ==========================================
-- GROUP 1: AUTHENTICATION & USERS
-- ==========================================
-- ENUMS
CREATE TYPE user_role AS ENUM ('ADMIN', 'MENTOR', 'LEARNER');
CREATE TYPE auth_provider AS ENUM ('LOCAL', 'GOOGLE');
CREATE TYPE verification_status AS ENUM ('PENDING', 'VERIFIED', 'REJECTED');
CREATE TYPE learner_rank_tier AS ENUM ('BRONZE', 'SILVER', 'GOLD', 'PLATINUM');
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR,
    full_name VARCHAR,
    avatar_url VARCHAR,
    role user_role,
    auth_provider auth_provider DEFAULT 'LOCAL',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE learner_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    current_proficiency_level VARCHAR,
    target_level VARCHAR,
    learning_preferences JSONB,
    streak_count INTEGER DEFAULT 0,
    total_xp INTEGER DEFAULT 0,
    current_rank_tier learner_rank_tier
);
CREATE TABLE mentor_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    bio TEXT,
    years_of_experience INTEGER,
    verification_status verification_status DEFAULT 'PENDING'
);
CREATE TABLE mentor_skills (
    skill_id SERIAL PRIMARY KEY,
    mentor_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    skill_name VARCHAR
);
-- ==========================================
-- GROUP 2: SUBSCRIPTION & FINANCE
-- ==========================================
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'EXPIRED', 'CANCELLED', 'UPGRADED');
CREATE TYPE transaction_status AS ENUM ('SUCCESS', 'FAILED', 'PENDING');
CREATE TABLE service_packages (
    package_id SERIAL PRIMARY KEY,
    name VARCHAR,
    price DECIMAL,
    duration_days INTEGER,
    has_mentor_support BOOLEAN,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE TABLE user_subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    package_id INTEGER REFERENCES service_packages(package_id),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    status subscription_status,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    package_id INTEGER REFERENCES service_packages(package_id),
    amount DECIMAL,
    payment_method VARCHAR,
    status transaction_status,
    created_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- GROUP 3: CURRICULUM & ADAPTIVE LEARNING
-- ==========================================
CREATE TYPE difficulty_level AS ENUM ('BEGINNER', 'INTERMEDIATE', 'ADVANCED');
CREATE TYPE vocab_status AS ENUM ('LEARNING', 'MASTERED');
CREATE TYPE path_item_status AS ENUM ('LOCKED', 'OPEN', 'COMPLETED');
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR,
    description TEXT
);
CREATE TABLE topics (
    topic_id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(category_id),
    name VARCHAR,
    description TEXT,
    image_url VARCHAR
);
CREATE TABLE scenarios (
    scenario_id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(topic_id),
    title VARCHAR,
    difficulty_level difficulty_level,
    script_content TEXT,
    key_phrases JSONB
);
CREATE TABLE vocabularies (
    vocab_id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(scenario_id),
    word VARCHAR,
    definition TEXT,
    example_sentence TEXT,
    pronunciation_ipa VARCHAR
);
CREATE TABLE user_saved_vocab (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    vocab_id INTEGER REFERENCES vocabularies(vocab_id),
    status vocab_status,
    saved_at TIMESTAMP
);
CREATE TABLE learning_paths (
    path_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    title VARCHAR,
    created_at TIMESTAMP
);
CREATE TABLE path_items (
    item_id SERIAL PRIMARY KEY,
    path_id INTEGER REFERENCES learning_paths(path_id),
    scenario_id INTEGER REFERENCES scenarios(scenario_id),
    order_sequence INTEGER,
    status path_item_status
);
-- ==========================================
-- GROUP 4: SOLO PRACTICE (WITH AI)
-- ==========================================
CREATE TYPE test_type AS ENUM ('INITIAL_ASSESSMENT', 'PERIODIC_CHECK');
CREATE TYPE session_mode AS ENUM ('SOLO_WITH_AI');
CREATE TABLE proficiency_tests (
    test_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    score FLOAT,
    determined_level VARCHAR,
    test_date TIMESTAMP,
    type test_type
);
CREATE TABLE speaking_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    scenario_id INTEGER REFERENCES scenarios(scenario_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    audio_url VARCHAR,
    mode session_mode
);
CREATE TABLE ai_feedbacks (
    feedback_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES speaking_sessions(session_id),
    pronunciation_score FLOAT,
    grammar_score FLOAT,
    fluency_score FLOAT,
    detailed_analysis JSONB,
    created_at TIMESTAMP
);
-- ==========================================
-- GROUP 5: PEER PRACTICE
-- ==========================================
CREATE TYPE peer_session_status AS ENUM ('MATCHING', 'ONGOING', 'COMPLETED', 'CANCELLED');
CREATE TYPE participant_role AS ENUM ('SPEAKER_A', 'SPEAKER_B');
CREATE TABLE peer_sessions (
    peer_session_id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(scenario_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    status peer_session_status,
    recording_url VARCHAR
);
CREATE TABLE peer_session_participants (
    participant_id SERIAL PRIMARY KEY,
    peer_session_id INTEGER REFERENCES peer_sessions(peer_session_id),
    user_id INTEGER REFERENCES users(user_id),
    role participant_role
);
CREATE TABLE peer_session_feedbacks (
    id SERIAL PRIMARY KEY,
    participant_id INTEGER REFERENCES peer_session_participants(participant_id),
    pronunciation_score FLOAT,
    grammar_score FLOAT,
    ai_suggestion TEXT,
    created_at TIMESTAMP
);
-- ==========================================
-- GROUP 6: MENTOR FEATURES
-- ==========================================
CREATE TYPE slot_status AS ENUM ('AVAILABLE', 'BOOKED', 'CANCELLED');
CREATE TYPE assessment_status AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW');
CREATE TYPE comment_status AS ENUM ('VISIBLE', 'HIDDEN_BY_ADMIN');
CREATE TABLE mentor_availability_slots (
    slot_id SERIAL PRIMARY KEY,
    mentor_id INTEGER REFERENCES users(user_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    is_recurring BOOLEAN DEFAULT FALSE,
    status slot_status,
    created_at TIMESTAMP
);
CREATE TABLE mentor_assessments (
    assessment_id SERIAL PRIMARY KEY,
    learner_id INTEGER REFERENCES users(user_id),
    slot_id INTEGER REFERENCES mentor_availability_slots(slot_id),
    result_level VARCHAR,
    mentor_notes TEXT,
    status assessment_status,
    meeting_link VARCHAR
);
CREATE TABLE mentor_documents (
    document_id SERIAL PRIMARY KEY,
    mentor_id INTEGER REFERENCES users(user_id),
    title VARCHAR,
    file_url VARCHAR,
    related_topic_id INTEGER REFERENCES topics(topic_id)
);
CREATE TABLE mentor_reviews (
    review_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES speaking_sessions(session_id),
    mentor_id INTEGER REFERENCES users(user_id),
    general_comment TEXT,
    grammar_correction TEXT,
    pronunciation_correction TEXT,
    created_at TIMESTAMP
);
CREATE TABLE mentor_posts (
    post_id SERIAL PRIMARY KEY,
    mentor_id INTEGER REFERENCES users(user_id),
    title VARCHAR,
    content TEXT,
    created_at TIMESTAMP
);
CREATE TABLE post_comments (
    comment_id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES mentor_posts(post_id),
    user_id INTEGER REFERENCES users(user_id),
    content TEXT,
    status comment_status,
    created_at TIMESTAMP
);
-- ==========================================
-- GROUP 7: SYSTEM & STATS
-- ==========================================
CREATE TYPE notif_type AS ENUM (
    'SYSTEM',
    'PAYMENT',
    'BOOKING',
    'FEEDBACK',
    'REMINDER'
);
CREATE TYPE challenge_status AS ENUM ('JOINED', 'COMPLETED');
CREATE TYPE ticket_category AS ENUM ('PAYMENT', 'TECHNICAL', 'ACCOUNT');
CREATE TYPE ticket_status AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED');
CREATE TYPE report_target_type AS ENUM ('USER', 'POST', 'COMMENT');
CREATE TYPE report_status AS ENUM ('PENDING', 'RESOLVED', 'DISMISSED');
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    title VARCHAR,
    message TEXT,
    type notif_type,
    is_read BOOLEAN DEFAULT FALSE,
    related_link VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE challenges (
    challenge_id SERIAL PRIMARY KEY,
    title VARCHAR,
    description TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    points_reward INTEGER
);
CREATE TABLE user_challenge_progress (
    participation_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    challenge_id INTEGER REFERENCES challenges(challenge_id),
    status challenge_status,
    completion_date TIMESTAMP
);
CREATE TABLE support_tickets (
    ticket_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    category ticket_category,
    subject VARCHAR,
    description TEXT,
    status ticket_status,
    created_at TIMESTAMP
);
CREATE TABLE system_policies (
    policy_id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES users(user_id),
    title VARCHAR,
    content TEXT,
    effective_date TIMESTAMP
);
CREATE TABLE user_reports (
    report_id SERIAL PRIMARY KEY,
    reporter_id INTEGER REFERENCES users(user_id),
    target_id INTEGER,
    target_type report_target_type,
    reason TEXT,
    status report_status
);
CREATE TABLE user_daily_stats (
    stat_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    date DATE,
    practice_minutes INTEGER,
    words_learned INTEGER,
    avg_score FLOAT,
    note TEXT
);