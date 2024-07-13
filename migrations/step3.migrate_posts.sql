CREATE TABLE temp_posts (
    post_id INTEGER PRIMARY KEY,
    post_title VARCHAR(50) NOT NULL,
    post_text VARCHAR(500) NOT NULL,
    user_id INTEGER
);
INSERT INTO temp_posts (
    post_id ,
    post_title,
    post_text,
    user_id
) SELECT * FROM posts;
DROP TABLE posts;
CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    post_title VARCHAR(50) NOT NULL,
    post_text VARCHAR(500) NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
DROP TABLE temp_posts;