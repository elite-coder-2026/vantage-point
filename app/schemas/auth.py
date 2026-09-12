from pydantic import BaseModel

from app.schemas.users import UserPublic


class LoginRequest(BaseModel):
    username: str
    password: str


class SessionOut(BaseModel):
    token: str
    user: UserPublic
