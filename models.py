from pydantic import BaseModel
from typing import List

class Post(BaseModel):
    post_title : str
    post_text : str
    user_id : int

class Posts(BaseModel):
    posts : List[Post]