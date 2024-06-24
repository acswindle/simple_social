import sqlite3
from sqlite3 import Connection
from typing import List
from models import Post, Posts

def get_post(connection:Connection)->Posts:
    with connection:
        cur = connection.cursor()
        cur = cur.execute(
                '''
                SELECT post_title, post_text, user_id
                FROM posts;
                '''
        )
        return Posts(posts = [Post.model_validate(dict(post)) for post in cur])

def insert_post(connection:Connection,
                post : Post):
    with connection:
        cur = connection.cursor()
        cur.execute(
            '''
            INSERT INTO posts (post_title,post_text,user_id)
            VALUES 
            ( :post_title , :post_text , :user_id )
            ''',
            post.model_dump()
        )


if __name__ == "__main__":
    connection = sqlite3.connect('social.db')
    connection.row_factory = sqlite3.Row
    print(get_post(connection))