DROP TABLE IF EXISTS recipe_ingredients;
DROP TABLE IF EXISTS recipes;
DROP TYPE IF EXISTS cuisine;

CREATE TYPE cuisine AS ENUM ('MEXICAN', 'AMERICAN', 'ITALIAN', 'ASIAN', 'INDIAN', 'MEDITERRANEAN', 'THAI', 'JAPANESE', 'FRENCH', 'GREEK', 'MIDDLE_EASTERN', 'CARIBBEAN', 'AFRICAN', 'OTHER');

CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cuisine cuisine NOT NULL DEFAULT 'OTHER',
    description TEXT,
    servings INTEGER NOT NULL DEFAULT 1,
    rating INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    usda_fdc_id INTEGER NOT NULL,
    quantity_grams INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_recipe_ingredient UNIQUE(recipe_id, usda_fdc_id)
);

CREATE INDEX idx_recipes_name ON recipes(name);
CREATE INDEX idx_recipes_cuisine ON recipes(cuisine);
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_ingredients_usda_fdc_id ON recipe_ingredients(usda_fdc_id);
