# FastAPI Repository

A base repository for FastAPI projects, inspired by Ruby on Rails' Active Record and Ransack.

## Installation

```bash
pip install fastapi-repository
```

## Usage

```python
from fastapi_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, model=User)
```
