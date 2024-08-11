from fastapi import FastAPI, Form, status, Depends, Cookie, UploadFile, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.security import OAuth2, OAuth2PasswordBearer
from fastapi.responses import HTMLResponse, RedirectResponse
from database import (
    get_post,
    insert_post,
    create_user,
    get_user,
    add_like,
    get_single_post,
    check_like,
    delete_like,
    add_comment,
    get_comments,
)
from models import Posts, Post, UserPost, UserPostId, UserHashed, Like, PostId
from sqlite3 import Connection, Row
from secrets import token_hex
from passlib.hash import pbkdf2_sha256
from typing import Annotated, Union
import jwt
from uuid import uuid4
from pathlib import Path

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), "static")
connection = Connection("social.db")
connection.row_factory = Row

templates = Jinja2Templates("./templates")
JWT_KEY = "12943c22f40279b21f28b3c907df64b633d1819db59bdd5d9741a28e4cb1e246"
EXPIRATION_TIME = 3600
ALGORITHM = "HS256"

ContextType = dict[str, str | int | None | dict | bool]


def decrypt_access_token(access_token: str | None) -> dict[str, str | int] | None:
    if access_token is None:
        return None
    _, token = access_token.split()
    data = jwt.decode(token, JWT_KEY, [ALGORITHM])
    return data


class OAuthCookie(OAuth2):
    def __call__(self, request: Request) -> int | str | None:
        data = decrypt_access_token(request.cookies.get("access_token"))
        if data is None:
            return None
        return data["user_id"]


oauth_cookie = OAuthCookie()


@app.get("/")
async def home(
    request: Request, access_token: Annotated[str | None, Cookie()] = None
) -> HTMLResponse:
    context = get_post(connection).model_dump()
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./index.html", context=context)


@app.get("/logout")
async def logout(response: RedirectResponse) -> RedirectResponse:
    response = RedirectResponse("/login")
    response.delete_cookie("access_token")
    return response


@app.get("/posts", response_model=None)
async def posts(
    request: Request,
    page: Annotated[int, Query()] = 0,
    access_token: Annotated[str | None, Cookie()] = None,
) -> HTMLResponse | None:
    user_id = None
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
    assert isinstance(user_id, int) or user_id is None, "Error processing access_token"
    context = get_post(connection, user_id, page=page).model_dump()
    if len(context["posts"]) == 0:
        return None
    context["page"] = page
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./posts.html", context=context)


@app.post("/post")
async def add_post(
    post_title: Annotated[str, Form()],
    post_text: Annotated[str, Form()],
    request: Request,
    post_image: UploadFile | None = None,
    user_id: int = Depends(oauth_cookie),
) -> HTMLResponse:
    image_path = None
    if post_image is not None:
        image_path = Path("./static/images") / uuid4().hex
        image_data = await post_image.read()
        image_path.write_bytes(image_data)
        image_path = image_path.name
    post = UserPostId(
        user_id=user_id,
        post_title=post_title,
        post_text=post_text,
        post_image=image_path,
    )
    insert_post(connection, post)
    context = {"post_added": True}
    return templates.TemplateResponse(request, "./add_post.html", context=context)


@app.get("/signup")
async def signup(
    request: Request, access_token: Annotated[str | None, Cookie()] = None
) -> HTMLResponse:
    context = {"signup": True}
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./signup.html", context=context)


@app.get("/login")
async def login(
    request: Request, access_token: Annotated[str | None, Cookie()] = None
) -> HTMLResponse:
    context = {"signup": False}
    if access_token:
        context["login"] = True
    return templates.TemplateResponse(request, "./login.html", context=context)


@app.post("/login", response_model=None)
async def user_login(
    username: Annotated[str, Form()], password: Annotated[str, Form()], request: Request
) -> HTMLResponse | RedirectResponse:
    user = get_user(connection, username)
    if user is None:
        return templates.TemplateResponse(
            request, "./login.html", context={"incorrect": True}
        )
    correct_password = pbkdf2_sha256.verify(password + user.salt, user.hash_password)
    if not correct_password:
        return templates.TemplateResponse(
            request, "./login.html", context={"incorrect": True}
        )
    token = jwt.encode(
        {"username": username, "user_id": user.user_id},
        JWT_KEY,
        ALGORITHM,
    )
    response = RedirectResponse("./", status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        "access_token",
        f"Bearer {token}",
        samesite="lax",
        expires=EXPIRATION_TIME,
        httponly=True,
        # set this True in production
        # secure=True,
    )
    return response


@app.post("/like")
async def upload_like(
    post_id: PostId, request: Request, user_id: int = Depends(oauth_cookie)
) -> HTMLResponse:
    like = Like(user_id=user_id, post_id=post_id.post_id)
    # check if already liked
    if check_like(connection, like):
        delete_like(connection, like)
    else:
        add_like(connection, like)
    context: dict[str, bool | None | dict]
    context = get_single_post(connection, post_id.post_id, user_id).model_dump()
    context = {"post": context}
    context["login"] = True
    return templates.TemplateResponse(request, "./post.html", context=context)


@app.get("/add_comment_form_{post_id}")
async def get_comment_form(
    post_id: int, request: Request, user_id: int = Depends(oauth_cookie)
) -> HTMLResponse:
    context = get_single_post(connection, post_id, user_id).model_dump()
    context: ContextType
    context = {"post": context}
    context["comment_form"] = True
    context["login"] = True
    return templates.TemplateResponse(request, "./post.html", context=context)


@app.post("/add_comment_{post_id}")
async def post_comment_form(
    post_id: int,
    post_text: Annotated[str, Form()],
    post_title: Annotated[str, Form()],
    request: Request,
    user_id: int = Depends(oauth_cookie),
) -> HTMLResponse:
    post = UserPostId(
        user_id=user_id, post_image=None, post_text=post_text, post_title=post_title
    )
    comment_id = insert_post(connection, post)
    add_comment(connection, comment_id, post_id)
    context: ContextType = get_single_post(connection, post_id, user_id).model_dump()
    context = {"post": context}
    context["comment_form"] = False
    context["login"] = True
    return templates.TemplateResponse(request, "./post.html", context=context)


def get_comment_thread_helper(
    access_token: str | None, post_id: int, hide: bool = False
) -> dict:
    user_id = None
    context: ContextType = {}
    if access_token:
        user_id = decrypt_access_token(access_token)
        if user_id:
            user_id = user_id["user_id"]
            context["login"] = True
    assert user_id is None or isinstance(user_id, int), "Error processing access_token"
    context["main_post"] = {
        "posts": [get_single_post(connection, post_id, user_id).model_dump()]
    }
    context["main_post"]["posts"][0]["hide_see_comments"] = not hide
    if hide:
        return context
    comments = get_comments(connection, post_id, user_id).model_dump()
    context["comments"] = comments
    return context


@app.get("/get_thread{post_id}")
async def get_thread(
    post_id: int, request: Request, access_token: Annotated[str | None, Cookie()] = None
) -> HTMLResponse:
    context = get_comment_thread_helper(access_token, post_id)
    return templates.TemplateResponse(request, "./comment_thread.html", context=context)


@app.get("/hide_thread{post_id}")
async def hide_thread(
    post_id: int, request: Request, access_token: Annotated[str | None, Cookie()] = None
) -> HTMLResponse:
    context = get_comment_thread_helper(access_token, post_id, hide=True)
    return templates.TemplateResponse(request, "./comment_thread.html", context=context)


@app.post("/signup", response_model=None)
async def add_user(
    username: Annotated[str, Form()], password: Annotated[str, Form()], request: Request
) -> HTMLResponse | RedirectResponse:
    if get_user(connection, username) is not None:
        return templates.TemplateResponse(
            request, "./signup.html", context={"taken": True, "username": username}
        )
    hex_int = 15
    salt = token_hex(hex_int)
    # hash users password
    hash_password = pbkdf2_sha256.hash(password + salt)
    # update database
    hashed_user = UserHashed(username=username, salt=salt, hash_password=hash_password)
    create_user(connection, hashed_user)
    return RedirectResponse("./login", status.HTTP_303_SEE_OTHER)
