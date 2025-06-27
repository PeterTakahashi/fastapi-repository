from sqlalchemy.exc import NoResultFound
import pytest
from uuid import uuid4
from faker import Faker

fake = Faker()

@pytest.mark.asyncio
async def test_find_user_by_id(user_repository, user):
    found_user = await user_repository.find(user.id)
    assert found_user is not None
    assert found_user.id == user.id


@pytest.mark.asyncio
async def test_find_user_not_found(user_repository):
    with pytest.raises(NoResultFound):
        await user_repository.find(uuid4())


@pytest.mark.asyncio
async def test_count_users(user_repository, users, user):
    count = await user_repository.count()
    assert count == len(users) + 1


@pytest.mark.asyncio
async def test_count_users_with_filter(user_repository, users):
    count = await user_repository.count(email=users[0].email)
    assert count == 1


@pytest.mark.asyncio
async def test_count_users_with_non_existent_filter(user_repository):
    count = await user_repository.count(email="non_existent_email@example.com")
    assert count == 0


@pytest.mark.asyncio
async def test_exists_user(user_repository, user):
    exists = await user_repository.exists(email=user.email)
    assert exists is True


@pytest.mark.asyncio
async def test_exists_user_not_found(user_repository):
    exists = await user_repository.exists(email=fake.email())
    assert exists is False


@pytest.mark.asyncio
async def test_find_by_or_raise_user(user_repository, user):
    found_user = await user_repository.find_by_or_raise(email=user.email)
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == user.email


@pytest.mark.asyncio
async def test_find_by_or_raise_user_not_found(user_repository):
    with pytest.raises(NoResultFound):
        await user_repository.find_by_or_raise(
            email=fake.email()
        )


@pytest.mark.asyncio
async def test_find_user_by_email(user_repository, user):
    found_user = await user_repository.find_by(email=user.email)
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == user.email


@pytest.mark.asyncio
async def test_find_user_by_email_not_found(user_repository):
    not_found_user = await user_repository.find_by(email=fake.email())
    assert not_found_user is None


@pytest.mark.asyncio
async def test_where_exact(user_repository, user):
    found_users = await user_repository.where(email__exact=user.email)
    assert len(found_users) == 1
    assert found_users[0].id == user.id


@pytest.mark.asyncio
async def test_where_iexact(user_repository, user):
    found_users = await user_repository.where(email__iexact=user.email.upper())
    assert len(found_users) == 1
    assert found_users[0].id == user.id


@pytest.mark.asyncio
async def test_where_contains(user_repository, user):
    substring = user.email[:3]
    found_users = await user_repository.where(email__contains=substring)
    assert any(u.id == user.id for u in found_users)


@pytest.mark.asyncio
async def test_where_icontains(user_repository, user):
    substring = user.email[:3].upper()
    found_users = await user_repository.where(email__icontains=substring)
    assert any(u.id == user.id for u in found_users)


@pytest.mark.asyncio
async def test_where_in(user_repository, user):
    fake_email = fake.email()
    found_users = await user_repository.where(email__in=[user.email, fake_email])
    assert len(found_users) == 1
    assert found_users[0].id == user.id


@pytest.mark.asyncio
async def test_where_startswith(user_repository, user):
    prefix = user.email.split("@")[0][:3]
    found_users = await user_repository.where(email__startswith=prefix)
    assert any(u.id == user.id for u in found_users)


@pytest.mark.asyncio
async def test_where_istartswith(user_repository, user):
    prefix = user.email.split("@")[0][:3].upper()
    found_users = await user_repository.where(email__istartswith=prefix)
    assert any(u.id == user.id for u in found_users)


@pytest.mark.asyncio
async def test_where_endswith(user_repository, user):
    suffix = user.email.split("@")[-1]
    found_users = await user_repository.where(email__endswith=suffix)
    assert any(u.id == user.id for u in found_users)


@pytest.mark.asyncio
async def test_where_iendswith(user_repository, user):
    suffix = user.email.split("@")[-1].upper()
    found_users = await user_repository.where(email__iendswith=suffix)
    assert any(u.id == user.id for u in found_users)


@pytest.mark.asyncio
async def test_where_repository(user_repository, user):
    found_users = await user_repository.where(email=user.email, id=user.id)
    assert len(found_users) == 1
    assert found_users[0].id == user.id


@pytest.mark.asyncio
async def test_where_repository_no_results(user_repository):
    not_found_users = await user_repository.where(email=fake.email())
    assert not_found_users == []


@pytest.mark.asyncio
async def test_where_repository_limit(user_repository, users):
    found_users = await user_repository.where(limit=2)
    assert len(found_users) == 2


@pytest.mark.asyncio
async def test_where_repository_offset(user_repository, users, user):
    found_users = await user_repository.where(offset=5)
    assert len(found_users) == len(users) + 1 - 5


@pytest.mark.asyncio
async def test_where_repository_offset_and_limit(user_repository, users):
    found_users = await user_repository.where(limit=3, offset=2)
    assert len(found_users) == 3


@pytest.mark.asyncio
async def test_where_repository_sorted(user_repository, users, user):
    found_users = await user_repository.where(sorted_by="email", sorted_order="asc")
    assert len(found_users) == len(users) + 1
    assert found_users == sorted(found_users, key=lambda u: u.email)


@pytest.mark.asyncio
async def test_where_repository_sorted_desc(user_repository, users, user):
    found_users = await user_repository.where(sorted_by="email", sorted_order="desc")
    assert len(found_users) == len(users) + 1
    assert found_users == sorted(found_users, key=lambda u: u.email, reverse=True)


@pytest.mark.asyncio
async def test_where_repository_attribute_error(user_repository):
    with pytest.raises(AttributeError, match="User has no attribute 'non_existent_column'"):
        await user_repository.where(non_existent_column="value")


@pytest.mark.asyncio
async def test_where_repository_sorted_attribute_error(user_repository):
    with pytest.raises(AttributeError, match="User has no attribute 'non_existent_column'"):
        await user_repository.where(sorted_by="non_existent_column")

@pytest.mark.asyncio
async def test_create_user(user_repository):
    user_data = {
        "email": "test_create@example.com",
        "hashed_password": "hashed_password_example",
    }
    new_user = await user_repository.create(**user_data)

    assert new_user.id is not None
    assert new_user.email == user_data["email"]
    assert new_user.hashed_password == user_data["hashed_password"]

    found_user = await user_repository.find(new_user.id)
    assert found_user is not None
    assert found_user.id == new_user.id


@pytest.mark.asyncio
async def test_create_user_with_invalid_field(user_repository):
    user_data = {
        "email": "test_invalid@example.com",
        "hashed_password": "hashed_password_example",
        "non_existent_field": "some_value",
    }
    with pytest.raises(TypeError):
        await user_repository.create(**user_data)


@pytest.mark.asyncio
async def test_destroy_user(user_repository, user):
    found_user = await user_repository.find(user.id)
    assert found_user is not None

    await user_repository.destroy(user.id)

    with pytest.raises(NoResultFound):
        await user_repository.find(user.id)


@pytest.mark.asyncio
async def test_destroy_user_not_found(user_repository):
    non_existent_id = uuid4()
    with pytest.raises(NoResultFound):
        await user_repository.destroy(non_existent_id)


@pytest.mark.asyncio
async def test_destroy_all_no_conditions(user_repository, users, user):
    count_before = await user_repository.count()
    assert count_before == len(users) + 1

    deleted_count = await user_repository.destroy_all()
    assert deleted_count == len(users) + 1

    count_after = await user_repository.count()
    assert count_after == 0


@pytest.mark.asyncio
async def test_destroy_all_with_conditions(user_repository, users, user):
    active_users_count = await user_repository.count(is_active=True)
    assert active_users_count > 0

    deleted_count = await user_repository.destroy_all(is_active=True)
    assert deleted_count == active_users_count

    remaining_active = await user_repository.count(is_active=True)
    assert remaining_active == 0


@pytest.mark.asyncio
async def test_destroy_all_no_match(user_repository):
    deleted_count = await user_repository.destroy_all(
        email="this_should_not_match_any@example.com"
    )
    assert deleted_count == 0


@pytest.mark.asyncio
async def test_update_user(user_repository, user):
    new_email = "updated_email@example.com"
    updated_user = await user_repository.update(user.id, email=new_email)

    assert updated_user.id == user.id
    assert updated_user.email == new_email

    found_user = await user_repository.find(user.id)
    assert found_user.email == new_email


@pytest.mark.asyncio
async def test_update_user_not_found(user_repository):
    non_existent_id = uuid4()
    with pytest.raises(NoResultFound):
        await user_repository.update(non_existent_id, email="doesnotexist@example.com")


@pytest.mark.asyncio
async def test_update_all_no_conditions(user_repository, users, user):
    updated_count = await user_repository.update_all({"failed_attempts": 2})
    assert updated_count == len(users) + 1

    # Confirm all users have the new value
    for u in await user_repository.where():
        assert u.failed_attempts == 2


@pytest.mark.asyncio
async def test_update_all_with_conditions(user_repository, users, user):
    updated_count = await user_repository.update_all(
        {"failed_attempts": 3}, is_active=True
    )
    assert updated_count > 0

    updated_users = await user_repository.where(failed_attempts=3)
    for u in updated_users:
        assert u.is_active is True

    # create inactive user
    user_data = {
        "email": "inactive@example.com",
        "hashed_password": "hashed_password_example",
        "is_active": False
    }
    await user_repository.create(**user_data)
    inactive_users = await user_repository.where(is_active=False)
    for iu in inactive_users:
        assert iu.failed_attempts != 3


@pytest.mark.asyncio
async def test_update_all_no_match(user_repository):
    updated_count = await user_repository.update_all(
        {"failed_attempts": 4}, failed_attempts=5
    )
    assert updated_count == 0
