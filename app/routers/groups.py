import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.db import get_conn
from app.queries import groups as groups_q
from app.schemas.groups import GroupCreate, GroupMemberAdd, GroupMemberOut, GroupOut

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await groups_q.create_group(
        conn, current_user_id, payload.name, payload.slug, payload.description, payload.is_private
    )
    return GroupOut(**row)


@router.get("/{group_id}", response_model=GroupOut)
async def get_group(group_id: int, conn: asyncpg.Connection = Depends(get_conn)):
    row = await groups_q.get_group_by_id(conn, group_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")
    return GroupOut(**row)


@router.post("/{group_id}/members", response_model=GroupMemberOut, status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: int,
    payload: GroupMemberAdd,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    group = await groups_q.get_group_by_id(conn, group_id)
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")

    if payload.user_id != current_user_id and group["owner_id"] != current_user_id:
        is_mod = await groups_q.is_member(conn, group_id, current_user_id)
        if not is_mod:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to add members")

    row = await groups_q.add_member(conn, group_id, payload.user_id)
    if row is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already a member")

    return GroupMemberOut(**row)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: int,
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    group = await groups_q.get_group_by_id(conn, group_id)
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")

    if user_id != current_user_id and group["owner_id"] != current_user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to remove this member")

    removed = await groups_q.remove_member(conn, group_id, user_id)
    if removed is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membership not found")


@router.get("/{group_id}/members", response_model=list[GroupMemberOut])
async def list_members(group_id: int, conn: asyncpg.Connection = Depends(get_conn)):
    rows = await groups_q.list_members(conn, group_id)
    return [GroupMemberOut(**r) for r in rows]
