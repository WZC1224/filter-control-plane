from typing import Optional

from pydantic import BaseModel, Field


class LoginSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordSchema(BaseModel):
    oldPassword: str = Field(..., min_length=1, max_length=128)
    newPassword: str = Field(..., min_length=6, max_length=128)


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


class BillListSchema(BaseModel):
    pageNo: int = Field(1, ge=1)
    pageSize: int = Field(20, ge=1, le=100)
    billId: Optional[str] = None
    orderId: Optional[str] = None
    ledgerType: Optional[str] = None
