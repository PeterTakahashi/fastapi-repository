# FastAPI Repository Documentation

`fastapi-repository` provides a `BaseRepository` class that simplifies data access in FastAPI applications using SQLAlchemy. It offers a standardized, asynchronous interface for CRUD operations, filtering, sorting, and more, inspired by Ruby on Rails' Active Record.

This guide will walk you through setting up and using the repository with a complete example.

## Features

- **Async Support:** Built for modern asynchronous Python applications.
- **Generic Interface:** A base class that can be extended for any SQLAlchemy model.
- **Simple CRUD:** `create`, `find`, `update`, and `destroy` methods out of the box.
- **Powerful Filtering:** Ransack-style filtering with operators like `__icontains`, `__gt`, `__in`, etc.
- **Sorting & Pagination:** Easily order and paginate query results.
- **Eager & Lazy Loading:** Control how related models are loaded to prevent N+1 query problems.
- **Default Scoping:** Apply default filters to all queries on a repository.

## Installation

```bash
pip install fastapi-repository
```

## Getting Started: A Complete Example

Let's build a simple user management API to see `fastapi-repository` in action.

### 1. Define your SQLAlchemy Model

First, define your data model using SQLAlchemy's declarative base.

```python
# models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str]
    email: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
```

### 2. Set up your Database Session

You'll need an `AsyncSession` to interact with your database. Here’s a typical setup.

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
```

### 3. Create a Repository

Create a repository for your `User` model by inheriting from `BaseRepository`.

```python
# repositories.py
from fastapi_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, model=User)
```

### 4. Use it in your FastAPI App

Now, you can inject the repository into your FastAPI routes to handle database operations cleanly.

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, repositories
from .database import get_session, engine
from pydantic import BaseModel


app = FastAPI()

# Create tables on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

# Pydantic schemas for request/response
class UserCreate(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

    class Config:
        orm_mode = True

@app.post("/users/", response_model=UserOut)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    repo = repositories.UserRepository(session)
    db_user = await repo.create(**user.dict())
    return db_user

@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    repo = repositories.UserRepository(session)
    user = await repo.find(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=list[UserOut])
async def list_users(
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_session)
):
    repo = repositories.UserRepository(session)
    filters = {"is_active": is_active} if is_active is not None else {}
    users = await repo.where(**filters)
    return users

@app.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user: UserUpdate,
    session: AsyncSession = Depends(get_session)
):
    repo = repositories.UserRepository(session)
    # Pass only non-None values to update
    update_data = {k: v for k, v in user.dict().items() if v is not None}
    db_user = await repo.update(user_id, **update_data)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    repo = repositories.UserRepository(session)
    await repo.destroy(user_id)
    return None
```

## API Reference

Here are the core methods available on `BaseRepository`.

### `find(id, **kwargs)`

Finds a record by its primary key.

- **Raises:** `NoResultFound` if the record does not exist.
- **Example:** `await repo.find(1)`

### `find_by(**search_params)`

Finds the first record matching the criteria.

- **Returns:** The model instance or `None`.
- **Example:** `await repo.find_by(email="user@example.com")`

### `find_by_or_raise(**search_params)`

Like `find_by`, but raises `NoResultFound` if no record is found.

- **Example:** `await repo.find_by_or_raise(email="user@example.com")`

### `where(**search_params)`

Finds all records matching the criteria. Supports pagination and sorting.

- **Parameters:**
  - `limit`: Max number of records.
  - `offset`: Number of records to skip.
  - `sorted_by`: Field to sort by (e.g., `"name"`).
  - `sorted_order`: `"asc"` or `"desc"`.
- **Example:** `await repo.where(is_active=True, limit=10, sorted_by="name", sorted_order="desc")`

### `count(**search_params)`

Counts records matching the criteria.

- **Example:** `await repo.count(is_active=True)`

### `exists(**search_params)`

Checks if a record matching the criteria exists.

- **Example:** `await repo.exists(email="user@example.com")`

### `create(**create_params)`

Creates a new record.

- **Example:** `await repo.create(name="John Doe", email="john@example.com")`

### `update(id, **update_params)`

Updates a record by its primary key.

- **Example:** `await repo.update(1, name="Jane Doe")`

### `update_all(updates, **search_params)`

Updates all records matching the criteria.

- **Example:** `await repo.update_all({"is_active": False}, name__icontains="spam")`

### `destroy(id)`

Deletes a record by its primary key.

- **Example:** `await repo.destroy(1)`

### `destroy_all(**search_params)`

Deletes all records matching the criteria.

- **Example:** `await repo.destroy_all(is_active=False)`

## Advanced Topics

### Advanced Filtering

The `where`, `find_by`, and other query methods support Ransack-style filtering on model fields. The format is `field__operator=value`.

**Supported Operators:**

| Operator      | Description               | Example                 |
| ------------- | ------------------------- | ----------------------- |
| `exact`       | Exact match               | `name__exact="John"`    |
| `iexact`      | Case-insensitive match    | `name__iexact="john"`   |
| `contains`    | Contains substring        | `name__contains="oh"`   |
| `icontains`   | Case-insensitive contains | `name__icontains="OH"`  |
| `in`          | In a list of values       | `id__in=[1, 2, 3]`      |
| `gt`          | Greater than              | `age__gt=18`            |
| `gte`         | Greater than or equal to  | `age__gte=18`           |
| `lt`          | Less than                 | `age__lt=65`            |
| `lte`         | Less than or equal to     | `age__lte=65`           |
| `startswith`  | Starts with a string      | `name__startswith="J"`  |
| `istartswith` | Case-insensitive starts   | `name__istartswith="j"` |
| `endswith`    | Ends with a string        | `name__endswith="n"`    |
| `iendswith`   | Case-insensitive ends     | `name__iendswith="N"`   |

### Eager and Lazy Loading

To avoid the N+1 problem, you can specify relationships to be loaded eagerly (`joinedload`) or lazily (`lazyload`).

- `joinedload_models`: A list of relationships to eager-load.
- `lazyload_models`: A list of relationships to lazy-load.

```python
# Eager load the 'profile' relationship for a user
user = await repo.find(1, joinedload_models=[User.profile])

# Find all users and eager load their 'addresses'
users = await repo.where(joinedload_models=[User.addresses])
```

if you'd like to join multiple tables, you can use this.

```python
# Multi-level relationship loading using string paths (separated by '__')
await repo.where(joinedload_models=["orders__items__product"])

# You can also use a list of strings
await repo.where(joinedload_models=[["orders", "items", "product"]])

# Single-level attribute reference (as before)
await repo.where(joinedload_models=[User.profile])

# Multi-level attribute chaining
await repo.where(joinedload_models=[(User.orders, Order.items, Item.product)])
```

### Default Scope

Define a `default_scope` on your repository to apply conditions to all queries automatically.

```python
class UserRepository(BaseRepository):
    # Only query active users by default
    default_scope = {"is_active": True}

    def __init__(self, session: AsyncSession):
        super().__init__(session, model=User)

# This will only find active users
active_users = await UserRepository(session).where()
```

To bypass the default scope for a single query, use `disable_default_scope=True`.

```python
# This will find all users, including inactive ones
all_users = await UserRepository(session).where(disable_default_scope=True)
```
