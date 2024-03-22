from typing import Optional
from fastapi import APIRouter, Security
from metagpt.software_company import generate_repo, ProjectRepo

from ...schemas.fields import (
   GenerateProgramRequest,
   GenerateProgramResponse
)
from ...config import config, config_env
from ...const import ROOT_PATH
from ...logs import logger
from ...auth import get_api_key


router = APIRouter()


# class MetaGPTIntegration:
#     def __init__(self, model_name: str = "default_model"):
#         """
#         Initializes the MetaGPTIntegration with a specific model.

#         :param model_name: The name of the MetaGPT model to use for code generation.
#         """
#         self.model_name = model_name
#         self.metagpt_client = metagpt.Client(model_name=model_name)

#     def generate_code(self, requirements: str) -> Optional[str]:
#         """
#         Generates code based on the provided project requirements using MetaGPT.

#         :param requirements: A string detailing the project requirements.
#         :return: A string containing the generated code or None if generation fails.
#         """
#         try:
#             generated_code = self.metagpt_client.generate(requirements)
#             return generated_code
#         except metagpt.GenerationError as e:
#             logger.error(f"Error generating code with MetaGPT: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error: {e}")
#             return None


@router.post('/gen_prog/', response_model=GenerateProgramResponse, dependencies=[Security(get_api_key)])
def generate_program(data: GenerateProgramRequest, dependencies=[Security(get_api_key)]):
    local_dir = ROOT_PATH / config.WORKSPACE
    logger.info(f'Idea: {data.idea}')
    repo: ProjectRepo = generate_repo(data.idea, n_round=1, code_review=False)
    logger.info(f'Workdir: {repo.workdir.name}')
    return {'repo_name':  repo.workdir.name}
