# FastAPI Repository

A base repository for FastAPI projects, inspired by Ruby on Rails' [Active Record](https://github.com/rails/rails/tree/main/activerecord) and [Ransack](https://github.com/activerecord-hackery/ransack). It provides a simple, intuitive, and asynchronous interface for data access using SQLAlchemy.

## Key Features

- **Async-first:** Designed for modern asynchronous Python.
- **Simple CRUD:** `find`, `create`, `update`, `destroy` methods out of the box.
- **Powerful Filtering:** Use Ransack-style operators (`__icontains`, `__gt`, etc.) for complex queries.
- **Relationship Loading:** Control eager (`joinedload`) and lazy (`lazyload`) loading.
- **Default Scoping:** Apply default conditions to all queries.

## Installation

```bash
pip install fastapi-repository
```

## Quick Start

1.  **Define a repository for your SQLAlchemy model:**

    ```python
    # repositories.py
    from fastapi_repository import BaseRepository
    from sqlalchemy.ext.asyncio import AsyncSession
    from .models import User  # Your SQLAlchemy model

    class UserRepository(BaseRepository):
        def __init__(self, session: AsyncSession):
            super().__init__(session, model=User)
    ```

2.  **Use it in your FastAPI application:**

    ```python
    # main.py
    from fastapi import FastAPI, Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from .database import get_session
    from .repositories import UserRepository

    app = FastAPI()

    @app.get("/users/{user_id}")
    async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
        repo = UserRepository(session)
        user = await repo.find(user_id)
        return user
    ```

## Documentation

For a complete guide, including a full tutorial, API reference, and advanced usage, please see the [**Full Documentation**](https://github.com/PeterTakahashi/fastapi-repository/blob/main/docs/index.md).
