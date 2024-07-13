from pydantic import BaseModel
from typing import List

class UserPost(BaseModel):
    post_title : str
    post_text : str

class Post(UserPost):
    user_id : int

class Posts(BaseModel):
    posts : List[Post]

class User(BaseModel):
    username : str
    password : str

class UserHashed(BaseModel):
    username : str
    salt : str
    hash_password : str