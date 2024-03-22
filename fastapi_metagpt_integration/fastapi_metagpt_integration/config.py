## config.py
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv
import os

class Config:
    """
    Config class for loading environment variables from .env file.
    Enhanced with error handling and validation of environment variables.
    """
    SERVER_NAME = 'MANDOGURU'
    VERSION: str = 'v1.0.0'
    PREFIX: str = f'/{VERSION}'
    WORKSPACE: Path = Path('./static')

    @staticmethod
    def load_env() -> Dict[str, str]:
        """
        Loads the environment variables from the .env file and returns them as a dictionary.
        Includes error handling for missing or corrupted .env files.
        
        Returns:
            Dict[str, str]: A dictionary containing the loaded environment variables.
        """
        # Load the environment variables from the .env file
        load_dotenv()

        # Check if the required environment variables are present
        if not os.getenv("GITHUB_TOKEN") or not os.getenv("METAGPT_API_KEY"):
            print("Required environment variables GITHUB_TOKEN or METAGPT_API_KEY are missing.")
            return {}

        # Define the environment variables to load with default values
        env_vars = {
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "default_token"),
            "METAGPT_API_KEY": os.getenv("METAGPT_API_KEY", "default_api_key"),
            "UVICORN_HOST": os.getenv("UVICORN_HOST", "127.0.0.1"),
            "UVICORN_PORT": os.getenv("UVICORN_PORT", "8000"),
            "API_KEY": os.getenv("API_KEY", "")
        }

        # Validate the loaded environment variables
        if not Config.validate_env_vars(env_vars):
            print("Invalid or missing environment variables.")
            return {}

        return env_vars

    @staticmethod
    def validate_env_vars(env_vars: Dict[str, str]) -> bool:
        """
        Validates the loaded environment variables to ensure they are present and correctly formatted.
        
        Args:
            env_vars (Dict[str, str]): The environment variables to validate.
        
        Returns:
            bool: True if all environment variables are valid, False otherwise.
        """
        # Example validation: Ensure GITHUB_TOKEN and METAGPT_API_KEY are not default values
        if env_vars["GITHUB_TOKEN"] == "default_token" \
            or env_vars["METAGPT_API_KEY"] == "default_api_key" \
            or env_vars["API_KEY"] == "":
            return False
        # Additional validation example: Check if UVICORN_PORT is within a valid range
        if not 1024 <= int(env_vars["UVICORN_PORT"]) <= 65535:
            print("UVICORN_PORT is out of the valid range (1024-65535).")
            return False
        return True


config = Config()
config_env = config.load_env()