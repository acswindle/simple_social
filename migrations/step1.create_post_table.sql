CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    post_title VARCHAR(50) NOT NULL,
    post_text VARCHAR(500) NOT NULL,
    user_id INTEGER
);