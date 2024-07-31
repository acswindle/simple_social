CREATE TABLE IF NOT EXISTS comments (
    post_id,
    post_for_id,
    PRIMARY KEY (post_id,post_for_id),
    FOREIGN KEY (post_id) REFERENCES posts (post_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
    FOREIGN KEY (post_for_id) REFERENCES posts (post_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);
