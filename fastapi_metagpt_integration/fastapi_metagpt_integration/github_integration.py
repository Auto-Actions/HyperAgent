import httpx
import base64
from .config import Config


class GitHubIntegration:
    def __init__(self):
        self.config = Config.load_env()
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
            print(f"Failed to push code to GitHub: {e}")
            return False
