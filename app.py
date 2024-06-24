from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from database import get_post, insert_post
from models import Posts, Post
from sqlite3 import Connection, Row


app = FastAPI()
connection = Connection('social.db')
connection.row_factory = Row

templates = Jinja2Templates('./templates')

@app.get('/')
async def home(request : Request)-> HTMLResponse:
    return templates.TemplateResponse(request,'./index.html', context={})

@app.get("/posts")
async def posts()->Posts:
    return get_post(connection)

@app.post('/post')
async def add_post(post : Post)->Post:
    insert_post(connection,post)
    return post