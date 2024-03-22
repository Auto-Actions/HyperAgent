from fastapi import Security, HTTPException
from fastapi.security import HTTPBasic
from fastapi.security import APIKeyHeader
from starlette import status

from .config import config_env

basic_auth = HTTPBasic()
api_key_header_auth = APIKeyHeader(name="KEY", auto_error=True)


async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    if api_key_header != config_env.get("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
