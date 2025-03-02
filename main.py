# main.py

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from database import async_session, engine
from models import Base, User, Post

app = FastAPI(title="Async Blog API")

# Create the database tables at startup.
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to get an async session.
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# Pydantic Schemas for User.
class UserCreate(BaseModel):
    username: str
    email: str

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        orm_mode = True

# Pydantic Schemas for Post.
class PostCreate(BaseModel):
    title: str
    content: str
    owner_id: int

class PostRead(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    class Config:
        orm_mode = True

# CRUD operations for Users.
@app.post("/users/", response_model=UserRead)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    new_user = User(username=user.username, email=user.email)
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="User could not be created.")
    return new_user

@app.get("/users/", response_model=List[UserRead])
async def read_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users

@app.get("/users/{user_id}", response_model=UserRead)
async def read_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.username = user_data.username
    user.email = user_data.email
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="User could not be updated.")
    return user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="User could not be deleted.")
    return {"detail": "User deleted successfully"}

# CRUD operations for Posts.
@app.post("/posts/", response_model=PostRead)
async def create_post(post: PostCreate, session: AsyncSession = Depends(get_session)):
    # Ensure the owner exists.
    result = await session.execute(select(User).where(User.id == post.owner_id))
    owner = result.scalars().first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    new_post = Post(title=post.title, content=post.content, owner_id=post.owner_id)
    session.add(new_post)
    try:
        await session.commit()
        await session.refresh(new_post)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Post could not be created.")
    return new_post

@app.get("/posts/", response_model=List[PostRead])
async def read_posts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Post))
    posts = result.scalars().all()
    return posts

@app.get("/posts/{post_id}", response_model=PostRead)
async def read_post(post_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=PostRead)
async def update_post(post_id: int, post_data: PostCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.title = post_data.title
    post.content = post_data.content
    post.owner_id = post_data.owner_id
    try:
        await session.commit()
        await session.refresh(post)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Post could not be updated.")
    return post

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await session.delete(post)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Post could not be deleted.")
    return {"detail": "Post deleted successfully"}
