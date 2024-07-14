from fastapi import FastAPI , Form, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.security import OAuth2
from fastapi.responses import HTMLResponse, RedirectResponse
from database import get_post, insert_post, create_user , get_user
from models import Posts, Post, UserPost, User, UserHashed
from sqlite3 import Connection, Row
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
from typing import Annotated
import jwt


app = FastAPI()
connection = Connection('social.db')
connection.row_factory = Row

templates = Jinja2Templates('./templates')
JWT_KEY = "12943c22f40279b21f28b3c907df64b633d1819db59bdd5d9741a28e4cb1e246"
EXPIRATION_TIME = 3600
ALGORITHM = 'HS256'

class OAuthCookie(OAuth2):
    def __call__(self,request:Request)->int:
        _,token = request.cookies.get('access_token').split()
        data = jwt.decode(token,JWT_KEY,[ALGORITHM])
        return data['user_id']

oauth_cookie = OAuthCookie()

@app.get('/')
async def home(request : Request)-> HTMLResponse:
    posts = get_post(connection)
    return templates.TemplateResponse(request, './index.html', context=posts.model_dump())

@app.get("/posts")
async def posts(request: Request)->HTMLResponse:
    posts =  get_post(connection)
    return templates.TemplateResponse(request, './posts.html', context=posts.model_dump())

@app.post('/post')
async def add_post(post : UserPost, request : Request, user_id:int = Depends(oauth_cookie))->HTMLResponse:
    post = Post(user_id=user_id,**post.model_dump())
    insert_post(connection,post)
    posts =  get_post(connection)
    return templates.TemplateResponse(request, './posts.html', context=posts.model_dump())

@app.get('/signup')
async def signup(request :Request)->HTMLResponse:
    return templates.TemplateResponse(request,'./signup.html',context={})

@app.get('/login')
async def signup(request :Request)->HTMLResponse:
    return templates.TemplateResponse(request,'./login.html',context={})

@app.post('/login')
async def add_user(username : Annotated[str,Form()], password : Annotated[str,Form()], request : Request)->HTMLResponse:
    user =  get_user(connection,username) 
    correct_password = pbkdf2_sha256.verify(password + user.salt, user.hash_password)
    if user is None or not correct_password:
        return templates.TemplateResponse(request,'./login',context={'incorrect' : True})
    token = jwt.encode({
        'username' : username,
        'user_id' : user.user_id
    },
    JWT_KEY,
    ALGORITHM,
    )
    response =  RedirectResponse('./',status.HTTP_303_SEE_OTHER)
    response.set_cookie('access_token',
                        f'Bearer {token}',
                        samesite='lax',
                        expires=EXPIRATION_TIME,
                        httponly=True,
                        # set this True in production
                        # secure=True,
                        )
    return response

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
    return RedirectResponse('./login',status.HTTP_303_SEE_OTHER)