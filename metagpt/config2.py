#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 01:25
@Author  : alexanderwu
@File    : llm_factory.py
"""
import os
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from metagpt.configs.browser_config import BrowserConfig
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.configs.mermaid_config import MermaidConfig
from metagpt.configs.redis_config import RedisConfig
from metagpt.configs.s3_config import S3Config
from metagpt.configs.search_config import SearchConfig
from metagpt.configs.workspace_config import WorkspaceConfig
from metagpt.const import METAGPT_ROOT
from metagpt.utils.yaml_model import YamlModel


class CLIParams(BaseModel):
    project_path: str = ""
    project_name: str = ""
    inc: bool = False
    reqa_file: str = ""
    max_auto_summarize_code: int = 0
    git_reinit: bool = False

    @model_validator(mode="after")
    def check_project_path(self):
        if self.project_path:
            self.inc = True
            self.project_name = self.project_name or Path(self.project_path).name


class Config(CLIParams, YamlModel):
    # Key Parameters
    llm: Dict[str, LLMConfig] = Field(default_factory=Dict)

    # Global Proxy. Will be used if llm.proxy is not set
    proxy: str = ""

    # Tool Parameters
    search: Dict[str, SearchConfig] = {}
    browser: Dict[str, BrowserConfig] = {"default": BrowserConfig()}
    mermaid: Dict[str, MermaidConfig] = {"default": MermaidConfig()}

    # Storage Parameters
    s3: Optional[S3Config] = None
    redis: Optional[RedisConfig] = None

    # Misc Parameters
    repair_llm_output: bool = False
    prompt_schema: Literal["json", "markdown", "raw"] = "json"
    workspace: WorkspaceConfig = WorkspaceConfig()
    enable_longterm_memory: bool = False
    code_review_k_times: int = 2

    # Will be removed in the future
    llm_for_researcher_summary: str = "gpt3"
    llm_for_researcher_report: str = "gpt3"
    METAGPT_TEXT_TO_IMAGE_MODEL_URL: str = ""

    @classmethod
    def default(cls):
        """Load default config
        - Priority: env < default_config_paths
        - Inside default_config_paths, the latter one overwrites the former one
        """
        default_config_paths: List[Path] = [
            METAGPT_ROOT / "config/config2.yaml",
            Path.home() / ".metagpt/config2.yaml",
        ]

        dicts = [dict(os.environ)]
        dicts += [Config.read_yaml(path) for path in default_config_paths]
        final = merge_dict(dicts)
        return Config(**final)

    def update_via_cli(self, project_path, project_name, inc, reqa_file, max_auto_summarize_code):
        """update config via cli"""

        # Use in the PrepareDocuments action according to Section 2.2.3.5.1 of RFC 135.
        if project_path:
            inc = True
            project_name = project_name or Path(project_path).name
        self.project_path = project_path
        self.project_name = project_name
        self.inc = inc
        self.reqa_file = reqa_file
        self.max_auto_summarize_code = max_auto_summarize_code

    def get_llm_config(self, name: Optional[str] = None) -> LLMConfig:
        """Get LLM instance by name"""
        if name is None:
            # Use the first LLM as default
            name = list(self.llm.keys())[0]
        if name not in self.llm:
            raise ValueError(f"LLM {name} not found in config")
        return self.llm[name]

    def get_openai_llm(self, name: Optional[str] = None) -> LLMConfig:
        """Get OpenAI LLMConfig by name. If no OpenAI, raise Exception"""
        if name is None:
            # Use the first OpenAI LLM as default
            name = [k for k, v in self.llm.items() if v.api_type == LLMType.OPENAI][0]
        if name not in self.llm:
            raise ValueError(f"OpenAI LLM {name} not found in config")
        return self.llm[name]


def merge_dict(dicts: Iterable[Dict]) -> Dict:
    """Merge multiple dicts into one, with the latter dict overwriting the former"""
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


config = Config.default()
