from typing import Optional

from pydantic import BaseModel, Field


class LoginSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordSchema(BaseModel):
    oldPassword: str = Field(..., min_length=1, max_length=128)
    newPassword: str = Field(..., min_length=6, max_length=128)


class CreateUserSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field('operator', pattern='^(admin|operator)$')


class PatchUserSchema(BaseModel):
    role: Optional[str] = Field(None, pattern='^(admin|operator)$')
    isActive: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class TaskListSchema(BaseModel):
    pageNo: int = Field(1, ge=1)
    pageSize: int = Field(20, ge=1, le=100)
    taskType: Optional[str] = None
    taskNo: Optional[str] = None
    countryCode: Optional[str] = None
    taskStatus: Optional[int] = None


class CreateTaskFieldsSchema(BaseModel):
    filterType: str = Field(..., min_length=1, max_length=64)
    countryCode: str = Field(..., min_length=1, max_length=16)
    describe: str = Field('', max_length=200)


class OrderListSchema(BaseModel):
    pageNo: int = Field(1, ge=1)
    pageSize: int = Field(20, ge=1, le=100)
    orderId: Optional[str] = None
    taskType: Optional[str] = None
    description: Optional[str] = None
    username: Optional[str] = None
    consumeType: Optional[int] = None
    createTimeBegin: Optional[str] = None
    createTimeEnd: Optional[str] = None


class BillListSchema(BaseModel):
    pageNo: int = Field(1, ge=1)
    pageSize: int = Field(20, ge=1, le=100)
    billId: Optional[str] = None
    orderId: Optional[str] = None
    ledgerType: Optional[str] = None


class PatchDownstreamSecretsSchema(BaseModel):
    """空字符串 = 清除文件覆盖（回退 .env）；省略 = 不改。"""

    data818Token: Optional[str] = Field(None, max_length=8192)
    data818AgentToken: Optional[str] = Field(None, max_length=8192)
