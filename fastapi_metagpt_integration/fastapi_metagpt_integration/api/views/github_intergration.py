import httpx
import base64
import git
from pathlib import Path
from fastapi import APIRouter, Security

from ...schemas.fields import (
   GithubReposRequest,
   GithubReposResponse
)
from ...config import config, config_env
from ...const import ROOT_PATH, WORKSPACE
from ...logs import logger
from ...auth import get_api_key


router = APIRouter()


def add_remote_url(repo_dir: Path, remote_name: str, remote_url: str):
    """
    Adds a remote URL to a Git repository using Python's Git library.

    Args:
        repo_dir (str): Path to the local Git repository.
        remote_name (str): Name for the remote (e.g., "origin").
        remote_url (str): URL of the remote Git repository on GitHub (e.g., "https://github.com/username/repo.git").
    """
    try:
        # Open the local Git repository
        repo = git.Repo(repo_dir)

        # Check if the remote already exists
        if remote_name in repo.remotes:
            logger.info(f"Remote '{remote_name}' already exists in the repository.")
            return

        # Add the remote with the specified name and URL
        origin = repo.create_remote(remote_name, url=remote_url)
        origin.fetch()
        repo.heads.master.checkout()
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        origin.pull()

        logger.info(f"Successfully added remote '{remote_name}' to the repository.")

    except git.exc.InvalidGitRepositoryError:
        logger.info(f"Invalid Git repository at '{repo_dir}'.")
    except Exception as e:
        logger.info(f"An error occurred: {e}")
    

def push_to_new_branch(repo_dir: Path, remote_name: str, remote_url: str, branch_name: str, commit_message: str):
    try:
        # Open the local Git repository
        repo = git.Repo(repo_dir)
        if remote_name not in repo.remotes:
            # Add the remote if it doesn't exist
            origin = repo.create_remote(remote_name, url=remote_url)
            logger.info(f"Successfully added remote '{remote_name}' to the repository.")
        else:
            logger.info(f'Remote {remote_name} does already exist.')
            origin = repo.remote(remote_name)
        # Create a new branch
        logger.info(repo.branches)
        existing_branch = [b.name for b in repo.branches]
        if branch_name in existing_branch:
            new_branch = branch_name
            # repo.git.checkout('HEAD', b=new_branch)
            logger.info(f'Branch {branch_name} does already exist.')
        else:
            logger.info(f"Created new local branch '{branch_name}'.")
            new_branch = repo.create_head(branch_name)
        if commit_message:
            repo.index.commit(commit_message)
            logger.info(f"Committed changes with message: '{commit_message}'.")
        # Push the new branch to the remote (set upstream for convenience)
        origin.pull(new_branch)
        origin.push(f'master:{new_branch}', set_upstream=True)
        logger.info(f"Successfully pushed branch '{branch_name}' to remote '{remote_name}'.")

    except git.exc.InvalidGitRepositoryError:
        logger.info(f"Invalid Git repository at '{repo_dir}'.")
    # except Exception as e:
    #     logger.info(f"An error occurred: {e}")


class GitHubIntegration:
    def __init__(self):
        self.token = self.config.get("GITHUB_TOKEN", "")
        if not self.token:
            raise ValueError("GITHUB_TOKEN is not set in the environment variables.")

    def push_code(self, repository: str, code: str, file_path: str = "path/to/file", branch: str = "main") -> bool:
        """
        Pushes generated code to a specified GitHub repository.

        Args:
            repository (str): The GitHub repository to push the code to.
            code (str): The generated code to be pushed.
            file_path (str): The file path within the repository to push the code to.
            branch (str): The branch name to push the code to.

        Returns:
            bool: True if the code was successfully pushed, False otherwise.
        """
        headers = {"Authorization": f"token {self.token}"}
        api_url = f"https://api.github.com/repos/{repository}/contents/{file_path}"
        encoded_content = base64.b64encode(code.encode("utf-8")).decode("utf-8")
        data = {
            "message": "auto-generated code by MetaGPT",
            "content": encoded_content,
            "branch": branch
        }

        try:
            response = httpx.put(api_url, headers=headers, json=data)
            response.raise_for_status()
            return True
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.info(f"Failed to push code to GitHub: {e}")
            return False


@router.post('/init_repo/', response_model=GithubReposResponse, dependencies=[Security(get_api_key)])
async def push_init_code(data: GithubReposRequest):
    # local_dir = ROOT_PATH / config.WORKSPACE / data.local
    local_dir = WORKSPACE / data.local
    github_token = config_env['GITHUB_TOKEN']
    auth_remote_url = data.remote_url.replace('https://', f'https://{github_token}@')
    logger.info(f'Remote URL {auth_remote_url}')
    add_remote_url(local_dir, data.remote_name, auth_remote_url)

    push_to_new_branch(local_dir, data.remote_name, auth_remote_url, data.branch, data.commit_message)
    response = {
      'id': 1,
      'remote_url': auth_remote_url,
      'remote_name': data.remote_url,
      'status': True
    }
    return response


if __name__ == '__main__':
    repo_dir = 'gomoku_game'
    remote_name = 'origin'
    remote_url = 'https://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@github.com/Auto-Actions/test_3'
    repo = git.Repo(WORKSPACE/repo_dir)
    print(repo.remotes)