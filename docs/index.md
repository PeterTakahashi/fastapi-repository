# FastAPI Repository Documentation

`fastapi-repository` provides a `BaseRepository` class for FastAPI applications using SQLAlchemy. It simplifies data access by offering a standardized set of methods for CRUD operations, filtering, sorting, and pagination. This documentation provides a comprehensive guide to using the repository.

## Features

- **Async Support:** Built for modern asynchronous Python applications.
- **Generic Interface:** A base class that can be extended for any SQLAlchemy model.
- **CRUD Operations:** Standard `create`, `find`, `update`, and `destroy` methods.
- **Advanced Filtering:** Ransack-style filtering with operators like `__icontains`, `__gt`, `__in`, etc.
- **Sorting & Pagination:** Easily order and paginate query results.
- **Eager & Lazy Loading:** Control how related models are loaded.
- **Default Scoping:** Apply default filters to all queries on a repository.

## Installation

```bash
pip install fastapi-repository
```

## Basic Usage

To use the `BaseRepository`, create a subclass and associate it with your SQLAlchemy model.

```python
# repositories.py
from fastapi_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, model=User)

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

## API Reference

### `find(id, ...)`

Find a record by its primary key. Raises `NoResultFound` if the record does not exist.

- `id`: The primary key of the record to find.
- `joinedload_models`: A list of relationships to eager-load.
- `lazyload_models`: A list of relationships to lazy-load.

### `find_by(**search_params)`

Find a single record matching the given criteria. Returns `None` if no record is found.

### `find_by_or_raise(**search_params)`

Find a single record matching the given criteria. Raises `NoResultFound` if no record is found.

### `where(**search_params)`

Find all records matching the given criteria. Supports pagination and sorting.

- `limit`: The maximum number of records to return.
- `offset`: The number of records to skip.
- `sorted_by`: The field to sort by.
- `sorted_order`: The sort order (`"asc"` or `"desc"`).

### `count(**search_params)`

Count the number of records matching the given criteria.

### `exists(**search_params)`

Check if a record matching the given criteria exists.

### `create(**create_params)`

Create a new record.

### `update(id, **update_params)`

Update a single record by its primary key.

### `update_all(updates, **search_params)`

Update all records matching the given criteria.

### `destroy(id)`

Delete a single record by its primary key.

### `destroy_all(**search_params)`

Delete all records matching the given criteria.

## Advanced Filtering

The `where`, `find_by`, and other query methods support Ransack-style filtering on model fields. The format is `field__operator=value`.

**Supported Operators:**

| Operator      | Description              | Example                            |
|---------------|--------------------------|------------------------------------|
| `exact`       | Exact match              | `name__exact="John"`               |
| `iexact`      | Case-insensitive match   | `name__iexact="john"`              |
| `contains`    | Contains substring       | `name__contains="oh"`              |
| `icontains`   | Case-insensitive contains| `name__icontains="OH"`             |
| `in`          | In a list of values      | `id__in=[1, 2, 3]`                 |
| `gt`          | Greater than             | `age__gt=18`                       |
| `gte`         | Greater than or equal to | `age__gte=18`                      |
| `lt`          | Less than                | `age__lt=65`                       |
| `lte`         | Less than or equal to    | `age__lte=65`                      |
| `startswith`  | Starts with a string     | `name__startswith="J"`             |
| `istartswith` | Case-insensitive starts  | `name__istartswith="j"`            |
| `endswith`    | Ends with a string       | `name__endswith="n"`               |
| `iendswith`   | Case-insensitive ends    | `name__iendswith="N"`              |

## Default Scope

You can define a `default_scope` on your repository to apply a set of conditions to all queries.

```python
class UserRepository(BaseRepository):
    default_scope = {"is_active": True}

    def __init__(self, session: AsyncSession):
        super().__init__(session, model=User)

# This will only find active users
active_users = await UserRepository(session).where()
```

To disable the default scope for a single query, use the `disable_default_scope=True` flag.

```python
# This will find all users, including inactive ones
all_users = await UserRepository(session).where(disable_default_scope=True)
```
