from typing import List, Optional

from pathlib import Path
from pydantic import BaseModel



class GithubReposRequest(BaseModel):
    id: int
    name: Optional[str]
    local: Path
    remote_url: str
    github_token: str
    remote_name: str = 'origin'
    branch: str = 'master'
    commit_message: str = 'Default message'


class GithubReposResponse(BaseModel):
    id: int
    remote_url: str
    remote_name: str
    status: bool = 'OK'


class GenerateProgramRequest(BaseModel):
    idea: str
    project_name: str
    n_rounds: int = 1
    incremental: bool = False


class GenerateProgramResponse(BaseModel):
    repo_name: str
    n_rounds: int