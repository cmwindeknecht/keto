-- Steam Analytics Database Schema

-- Games table
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    steam_app_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    release_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Price history
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Reviews
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    positive INTEGER DEFAULT 0,
    negative INTEGER DEFAULT 0,
    score DECIMAL(5, 2), -- Calculated review score
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_games_steam_app_id ON games(steam_app_id);
CREATE INDEX idx_price_history_game_id ON price_history(game_id);
CREATE INDEX idx_reviews_game_id ON reviews(game_id);