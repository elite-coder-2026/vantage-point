from datetime import datetime

from pydantic import BaseModel


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str


class ChangePasswordResult(BaseModel):
    message: str


class ChangeAccountTypeRequest(BaseModel):
    value: str


class AccountTypeOut(BaseModel):
    type: str | None


class BlockedUserOut(BaseModel):
    id: int
    username: str
    display_name: str
    blocked_at: datetime


class BlockActionOut(BaseModel):
    username: str


class PrivacyRequest(BaseModel):
    value: str


class PrivacyOut(BaseModel):
    options: str | None


class LoginHistoryOut(BaseModel):
    time: datetime
    os: str | None
    browser: str | None
    ip: str | None
    logout: str | datetime
