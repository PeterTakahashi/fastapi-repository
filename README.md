# FastAPI Repository

A base repository for FastAPI projects, inspired by Ruby on Rails' [Active Record](https://github.com/rails/rails/tree/main/activerecord) and [Ransack](https://github.com/activerecord-hackery/ransack). It provides a simple, intuitive interface for data access in asynchronous applications using SQLAlchemy.

## Features

- **Async-first:** Designed for modern asynchronous Python.
- **Simple CRUD:** `find`, `create`, `update`, `destroy` methods out of the box.
- **Powerful Filtering:** Use Ransack-style operators (`__icontains`, `__gt`, etc.) for complex queries.
- **Eager & Lazy Loading:** Control relationship loading with `joinedload` and `lazyload`.
- **Default Scoping:** Apply default conditions to all queries.

## Installation

```bash
pip install fastapi-repository
```

## Quick Start

```python
from fastapi_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, model=User)
```

## Documentation

For a complete guide, including all available methods, advanced filtering, and default scoping, please see the [full documentation](https://github.com/PeterTakahashi/fastapi-repository/blob/main/docs/index.md).
