import json
import time

from flask import Response
from pydantic import BaseModel


class _Exception(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def serialize_result(result):
    if result is None:
        return None
    if isinstance(result, BaseModel):
        return result.model_dump()
    if isinstance(result, list):
        return [serialize_result(item) for item in result]
    if isinstance(result, dict):
        return {key: serialize_result(value) for key, value in result.items()}
    return result


class JsonResponse(Response):
    default_mimetype = 'application/json'

    def __init__(self, code: int, success: bool, message: str, result):
        body = {
            'code': code,
            'success': success,
            'message': message,
            'result': serialize_result(result),
            'timestamp': int(round(time.time() * 1000)),
        }
        # 业务码放 body；HTTP 统一 200，与 data818 前端习惯一致
        super().__init__(json.dumps(body, ensure_ascii=False), status=200)


class Success(JsonResponse):
    def __init__(self, message: str = 'ok', code: int = 200, result=None):
        super().__init__(code, True, message, result)


class Fail(JsonResponse):
    def __init__(self, message: str = 'error', code: int = 400, result=None):
        super().__init__(code, False, message, result)
