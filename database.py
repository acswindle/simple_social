import sqlite3
from sqlite3 import Connection
from typing import List, Union
from models import Post, Posts, UserHashed, UserHashedIndex, Like

def get_post(connection:Connection,
             user_id:int|None = None,
             limit:int=10,
             page:int=0)->Posts:
    offset = limit*page
    with connection:
        cur = connection.cursor()
        cur = cur.execute(
                '''
                WITH post_page AS (
                SELECT post_id, post_title, post_text, user_id
                FROM posts
                LIMIT :limit
                OFFSET :offset),
                like_count AS (
                SELECT post_id , COUNT(*) num_likes
                FROM likes
                WHERE post_id IN (SELECT post_id FROM post_page)
                GROUP BY post_id
                ),
                user_liked AS (
                SELECT post_id, user_id
                FROM likes
                WHERE user_id = :user_id AND post_id IN (SELECT post_id FROM post_page)
                )
                SELECT post_title, post_text, p.user_id user_id, num_likes, p.post_id post_id, u.user_id user_liked
                FROM post_page p
                LEFT JOIN like_count l
                USING (post_id)
                LEFT JOIN user_liked u
                USING (post_id);
                ''',
                {
                    'limit' : limit,
                    'offset' : offset,
                    'user_id' : user_id,
                }
        )
        return Posts(posts = [Post.model_validate(dict(post)) for post in cur])

def get_single_post(connection:Connection,
             post_id:int,
             user_id:int)->Posts:
    with connection:
        cur = connection.cursor()
        cur = cur.execute(
                '''
                WITH post_page AS (
                SELECT post_id, post_title, post_text, user_id
                FROM posts
                WHERE post_id = :post_id
                ),
                like_count AS (
                SELECT post_id, COUNT(*) num_likes
                FROM likes
                WHERE post_id = :post_id
                ),
                user_liked AS
                (SELECT post_id, user_id user_liked
                FROM likes
                WHERE user_id = :user_id AND post_id = :post_id
                )
                SELECT post_title, post_text, p.user_id user_id, num_likes, user_liked, p.post_id post_id
                FROM post_page p
                LEFT JOIN like_count l
                USING (post_id)
                LEFT JOIN user_liked u
                USING (post_id);
                ''',
                {
                    'post_id' : post_id,
                    'user_id' : user_id,
                }
        )
        return Post.model_validate(dict(cur.fetchone()))

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

def add_like(
        connection:Connection,
        like:Like,
)->None:
    with connection:
        cur = connection.cursor()
        cur.execute(
            '''
            INSERT INTO likes (user_id,post_id)
            VALUES (:user_id, :post_id);
            ''',
            like.model_dump()
        )

def check_like(
        connection:Connection,
        like:Like,
)->bool:
    cur = connection.cursor()
    cur.execute(
        '''
        SELECT * FROM likes WHERE user_id = :user_id AND post_id = :post_id;
        ''',
        like.model_dump()
    )
    return True if cur.fetchone() is not None else False

def delete_like(
        connection:Connection,
        like:Like,
)->None:
    cur = connection.cursor()
    cur.execute('DELETE FROM likes WHERE user_id = :user_id AND post_id = :post_id', 
                like.model_dump())

if __name__ == "__main__":
    connection = sqlite3.connect('social.db')
    connection.row_factory = sqlite3.Row
    print(get_user(connection,'test'))