import sqlite3
from sqlite3 import Connection
from typing import List, Union
from models import Post, Posts, UserHashed, UserHashedIndex

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

def get_user(
        connection:Connection,
        username : str
)->Union[UserHashedIndex,None]:
    cur = connection.cursor()
    cur.execute(
        '''
            SELECT 
                user_id,
                username,
                salt,
                hash_password
            FROM users
            WHERE username = ?
        ''', (username,)
    )
    user = cur.fetchone()
    if user is None:
        return None
    return UserHashedIndex(**dict(user))
    

def create_user(connection:Connection,
                user : UserHashed)->bool:
    cur = connection.cursor()
    cur.execute(
        '''
        INSERT INTO users (username,salt,hash_password)
        VALUES 
        ( :username , :salt , :hash_password);
        ''',
    user.model_dump()
    )
    connection.commit()
    return True

if __name__ == "__main__":
    connection = sqlite3.connect('social.db')
    connection.row_factory = sqlite3.Row
    print(get_user(connection,'test'))