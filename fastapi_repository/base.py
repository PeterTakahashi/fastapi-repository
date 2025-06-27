from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.orm import joinedload, lazyload
from sqlalchemy import func, update, delete
from typing import Optional, List, Union, Dict, Any

OPERATORS = {
    # Exact match
    "exact": lambda col, val: col == val,
    "iexact": lambda col, val: col.ilike(val),
    # Partial match
    "contains": lambda col, val: col.contains(val),
    "icontains": lambda col, val: col.ilike(f"%{val}%"),
    # IN clause
    "in": lambda col, val: col.in_(val) if isinstance(val, list) else col.in_([val]),
    # Comparison operators
    "gt": lambda col, val: col > val,
    "gte": lambda col, val: col >= val,
    "lt": lambda col, val: col < val,
    "lte": lambda col, val: col <= val,
    # Starts/ends with
    "startswith": lambda col, val: col.startswith(val),
    "istartswith": lambda col, val: col.ilike(f"{val}%"),
    "endswith": lambda col, val: col.endswith(val),
    "iendswith": lambda col, val: col.ilike(f"%{val}"),
}


class BaseRepository:
    default_scope: dict = {}

    def __init__(self, session: AsyncSession, model=None):
        self.session = session
        if not model:
            raise ValueError("Model is not set for this repository.")
        self.model = model

    async def find(
        self,
        id: Union[int, UUID],
        sorted_by: Optional[str] = None,
        sorted_order: str = "asc",
        joinedload_models: Optional[List] = None,
        lazyload_models: Optional[List] = None,
        disable_default_scope: bool = False,
    ):
        """
        Find a record by its ID. Raise an exception if not found.
        """
        query = await self.__generate_query(
            limit=1,
            offset=0,
            sorted_by=sorted_by,
            sorted_order=sorted_order,
            joinedload_models=joinedload_models,
            lazyload_models=lazyload_models,
            disable_default_scope=disable_default_scope,
            id=id,
        )

        result = await self.session.execute(query)
        instance = result.scalars().first()

        if not instance:
            raise NoResultFound(f"{self.model.__name__} with id {id} not found.")

        return instance

    async def find_by(
        self,
        sorted_by: Optional[str] = None,
        sorted_order: str = "asc",
        joinedload_models: Optional[List] = None,
        lazyload_models: Optional[List] = None,
        disable_default_scope: bool = False,
        **search_params,
    ):
        """
        Find a record by given attributes. Return None if not found.
        """
        query = await self.__generate_query(
            limit=1,
            offset=0,
            sorted_by=sorted_by,
            sorted_order=sorted_order,
            joinedload_models=joinedload_models,
            lazyload_models=lazyload_models,
            disable_default_scope=disable_default_scope,
            **search_params,
        )
        result = await self.session.execute(query)
        instance = result.scalars().first()
        return instance

    async def find_by_or_raise(
        self,
        sorted_by: Optional[str] = None,
        sorted_order: str = "asc",
        joinedload_models: Optional[List] = None,
        lazyload_models: Optional[List] = None,
        disable_default_scope: bool = False,
        **search_params,
    ):
        """
        Find a record by given attributes. Raise an exception if not found.
        """
        instance = await self.find_by(
            sorted_by=sorted_by,
            sorted_order=sorted_order,
            joinedload_models=joinedload_models,
            lazyload_models=lazyload_models,
            disable_default_scope=disable_default_scope,
            **search_params,
        )
        if not instance:
            raise NoResultFound(
                f"{self.model.__name__} with attributes {search_params} not found."
            )
        return instance

    async def where(
        self,
        limit: int = 100,
        offset: int = 0,
        sorted_by: Optional[str] = None,
        sorted_order: str = "asc",
        joinedload_models: Optional[List] = None,
        lazyload_models: Optional[List] = None,
        disable_default_scope: bool = False,
        **search_params,
    ):
        """
        Find records with optional filtering, sorting, and pagination.
        """
        query = await self.__generate_query(
            limit=limit,
            offset=offset,
            sorted_by=sorted_by,
            sorted_order=sorted_order,
            joinedload_models=joinedload_models,
            lazyload_models=lazyload_models,
            disable_default_scope=disable_default_scope,
            **search_params,
        )
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def count(self, disable_default_scope: bool = False, **search_params) -> int:
        """
        Count records with optional filtering.
        """
        conditions = []
        if not disable_default_scope:
            default_conditions = await self.__get_conditions(**self.default_scope)
            conditions.extend(default_conditions)

        conditions += await self.__get_conditions(**search_params)
        query = select(func.count("*")).select_from(self.model).where(*conditions)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists(
        self, disable_default_scope: bool = False, **search_params
    ) -> bool:
        """
        Check if any record exists with the given attributes.
        """
        counted = await self.count(
            disable_default_scope=disable_default_scope, **search_params
        )
        return counted > 0

    async def __generate_query(
        self,
        limit: int = 100,
        offset: int = 0,
        sorted_by: Optional[str] = None,
        sorted_order: str = "asc",
        joinedload_models: Optional[List] = None,
        lazyload_models: Optional[List] = None,
        disable_default_scope: bool = False,
        **search_params,
    ):
        """
        Generate a query with optional filtering, sorting, and pagination.
        Apply default scope if not disabled.
        """
        conditions = []
        if not disable_default_scope:
            default_conditions = await self.__get_conditions(**self.default_scope)
            conditions.extend(default_conditions)

        conditions += await self.__get_conditions(**search_params)

        query = select(self.model).where(*conditions)

        if joinedload_models:
            for model in joinedload_models:
                query = query.options(joinedload(model))
        if lazyload_models:
            for model in lazyload_models:
                query = query.options(lazyload(model))

        if sorted_by:
            query = self._apply_order_by(query, sorted_by, sorted_order)

        return query.limit(limit).offset(offset)

    def _apply_order_by(self, query, sorted_by: str, sorted_order: str):
        """
        Helper to apply order_by to a query.
        """
        column = getattr(self.model, sorted_by, None)
        if not column:
            raise AttributeError(
                f"{self.model.__name__} has no attribute '{sorted_by}'"
            )

        if sorted_order.lower() == "asc":
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())
        return query

    async def __get_conditions(self, **search_params):
        """
        Generate conditions for filtering based on provided keyword arguments.
        Supports Ransack-like operators (field__operator=value).
        """
        conditions = []
        for key, value in search_params.items():
            # If "__" is included in the key, split into field name and operator
            if "__" in key:
                parts = key.split("__")
                op = "exact"
                if parts[-1] in OPERATORS:  # If the last part is an operator, remove it
                    op = parts.pop()

                # Simple column: foo__icontains=bar
                if len(parts) == 1:
                    column = getattr(self.model, parts[0], None)
                    if column is None:
                        raise AttributeError(
                            f"{self.model.__name__} has no attribute '{parts[0]}'"
                        )
                    conditions.append(OPERATORS[op](column, value))
                    continue

                # One-hop relationship: rel__field__op=value
                rel_attr = getattr(self.model, parts[0], None)
                if rel_attr is None or not hasattr(rel_attr, "property"):
                    raise AttributeError(
                        f"{self.model.__name__} has no relationship '{parts[0]}'"
                    )
                target_cls = rel_attr.property.mapper.class_
                target_column = getattr(target_cls, parts[1], None)
                if target_column is None:
                    raise AttributeError(
                        f"{target_cls.__name__} has no attribute '{parts[1]}'"
                    )
                conditions.append(rel_attr.any(OPERATORS[op](target_column, value)))
                continue
            else:
                # If "__" is not included, treat as simple eq (=) comparison
                column = getattr(self.model, key, None)
                if column is None:
                    raise AttributeError(
                        f"{self.model.__name__} has no attribute '{key}'"
                    )
                conditions.append(column == value)

    async def create(self, **create_params):
        """
        Generic create method that instantiates the model,
        saves it, and returns the new instance.
        """
        instance = self.model(**create_params)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: Union[int, UUID], **update_params):
        """
        Update a single record by its primary key.
        Raises NoResultFound if the record doesn't exist.

        Usage:
            await repository.update(some_id, field1='value1', field2='value2')
        """
        instance = await self.find(id)
        for field, value in update_params.items():
            setattr(instance, field, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update_all(self, updates: Dict[str, Any], **search_params) -> int:
        """
        Update all records that match the given conditions in one query.
        Returns the number of rows that were updated.

        Usage:
            await repository.update_all(
                {"field1": "new_value", "field2": 123},
                some_field__gte=10,
                other_field="foo"
            )
        """
        conditions = await self.__get_conditions(**search_params)
        stmt = update(self.model).where(*conditions).values(**updates)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def destroy(self, id: Union[int, UUID]) -> None:
        """
        Destroy (delete) a single record by its primary key.
        Raises NoResultFound if the record doesn't exist.
        """
        instance = await self.find(id)  # Will raise NoResultFound if not found
        await self.session.delete(instance)
        await self.session.commit()

    async def destroy_all(self, **search_params) -> int:
        """
        Destroy (delete) all records that match the given conditions in one query.
        Returns the number of rows that were deleted.

        Usage:
            await repository.destroy_all(field1="value1", field2__gte=10)
        """
        conditions = await self.__get_conditions(**search_params)
        stmt = delete(self.model).where(*conditions)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
