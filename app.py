from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from database import get_post, insert_post
from models import Posts, Post, UserPost
from sqlite3 import Connection, Row


app = FastAPI()
connection = Connection('social.db')
connection.row_factory = Row

templates = Jinja2Templates('./templates')
user_id = 1

@app.get('/')
async def home(request : Request)-> HTMLResponse:
    posts = get_post(connection)
    return templates.TemplateResponse(request,'./index.html', context=posts.model_dump())

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
