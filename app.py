from fastapi import FastAPI , Form
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from database import get_post, insert_post, create_user , get_user
from models import Posts, Post, UserPost, User, UserHashed
from sqlite3 import Connection, Row
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
from typing import Annotated


app = FastAPI()
connection = Connection('social.db')
connection.row_factory = Row

templates = Jinja2Templates('./templates')
user_id = 1

@app.get('/')
async def home(request : Request)-> HTMLResponse:
    posts = get_post(connection)
    return templates.TemplateResponse(request, './index.html', context=posts.model_dump())

@app.get("/posts")
async def posts(request: Request)->HTMLResponse:
    posts =  get_post(connection)
    return templates.TemplateResponse(request, './posts.html', context=posts.model_dump())

@app.post('/post')
async def add_post(post : UserPost, request : Request)->HTMLResponse:
    post = Post(user_id=user_id,**post.model_dump())
    insert_post(connection,post)
    posts =  get_post(connection)
    return templates.TemplateResponse(request, './posts.html', context=posts.model_dump())

@app.get('/signup')
async def signup(request :Request)->HTMLResponse:
    return templates.TemplateResponse(request,'./signup.html',context={})

@app.post('/signup')
async def add_user(username : Annotated[str,Form()], password : Annotated[str,Form()], request : Request)->HTMLResponse:
    if get_user(connection,username) is not None:
        return templates.TemplateResponse(request,'./signup.html',context={'taken' : True, 'username' : username})
    hex_int = 15
    salt = token_hex(hex_int)
    # hash users password
    hash_password = pbkdf2_sha256.hash(password + salt)
    # update database
    hashed_user = UserHashed(
        username=username,
        salt = salt,
        hash_password=hash_password
    )
    create_user(connection,hashed_user)
    return templates.TemplateResponse(request,'./login.html',context={})