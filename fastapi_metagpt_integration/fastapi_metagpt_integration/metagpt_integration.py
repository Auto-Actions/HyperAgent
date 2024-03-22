## metagpt_integration.py

from typing import Optional
import hypothetical_metagpt_library as metagpt
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class MetaGPTIntegration:
    def __init__(self, model_name: str = "default_model"):
        """
        Initializes the MetaGPTIntegration with a specific model.

        :param model_name: The name of the MetaGPT model to use for code generation.
        """
        self.model_name = model_name
        self.metagpt_client = metagpt.Client(model_name=model_name)

    def generate_code(self, requirements: str) -> Optional[str]:
        """
        Generates code based on the provided project requirements using MetaGPT.

        :param requirements: A string detailing the project requirements.
        :return: A string containing the generated code or None if generation fails.
        """
        try:
            generated_code = self.metagpt_client.generate(requirements)
            return generated_code
        except metagpt.GenerationError as e:
            logging.error(f"Error generating code with MetaGPT: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None
