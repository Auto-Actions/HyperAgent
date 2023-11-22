#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_prd.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from metagpt.actions import Action, ActionOutput
from metagpt.actions.search_and_summarize import SearchAndSummarize
from metagpt.config import CONFIG
from metagpt.const import (
    COMPETITIVE_ANALYSIS_FILE_REPO,
    DOCS_FILE_REPO,
    PRD_PDF_FILE_REPO,
    PRDS_FILE_REPO,
    REQUIREMENT_FILENAME,
)
from metagpt.logs import logger
from metagpt.schema import Document, Documents
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.mermaid import mermaid_to_file

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
## Original Requirements
{requirements}

## Search Information
{search_information}

## mermaid quadrantChart code syntax example. DONT USE QUOTO IN CODE DUE TO INVALID SYNTAX. Replace the <Campain X> with REAL COMPETITOR NAME
```mermaid
quadrantChart
    title Reach and engagement of campaigns
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    "Campaign: A": [0.3, 0.6]
    "Campaign B": [0.45, 0.23]
    "Campaign C": [0.57, 0.69]
    "Campaign D": [0.78, 0.34]
    "Campaign E": [0.40, 0.34]
    "Campaign F": [0.35, 0.78]
    "Our Target Product": [0.5, 0.6]
```

## Format example
{format_example}
-----
Role: You are a professional product manager; the goal is to design a concise, usable, efficient product
Requirements: According to the context, fill in the following missing information, each section name is a key in json ,If the requirements are unclear, ensure minimum viability and avoid excessive design

## Original Requirements: Provide as Plain text, place the polished complete original requirements here

## Product Goals: Provided as Python list[str], up to 3 clear, orthogonal product goals. If the requirement itself is simple, the goal should also be simple

## User Stories: Provided as Python list[str], up to 5 scenario-based user stories, If the requirement itself is simple, the user stories should also be less

## Competitive Analysis: Provided as Python list[str], up to 7 competitive product analyses, consider as similar competitors as possible

## Competitive Quadrant Chart: Use mermaid quadrantChart code syntax. up to 14 competitive products. Translation: Distribute these competitor scores evenly between 0 and 1, trying to conform to a normal distribution centered around 0.5 as much as possible.

## Requirement Analysis: Provide as Plain text. Be simple. LESS IS MORE. Make your requirements less dumb. Delete the parts unnessasery.

## Requirement Pool: Provided as Python list[list[str], the parameters are requirement description, priority(P0/P1/P2), respectively, comply with PEP standards; no more than 5 requirements and consider to make its difficulty lower

## UI Design draft: Provide as Plain text. Be simple. Describe the elements and functions, also provide a simple style description and layout description.
## Anything UNCLEAR: Provide as Plain text. Make clear here.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": """
[CONTENT]
{
    "Original Requirements": "",
    "Search Information": "",
    "Requirements": "",
    "Product Goals": [],
    "User Stories": [],
    "Competitive Analysis": [],
    "Competitive Quadrant Chart": "quadrantChart
                title Reach and engagement of campaigns
                x-axis Low Reach --> High Reach
                y-axis Low Engagement --> High Engagement
                quadrant-1 We should expand
                quadrant-2 Need to promote
                quadrant-3 Re-evaluate
                quadrant-4 May be improved
                Campaign A: [0.3, 0.6]
                Campaign B: [0.45, 0.23]
                Campaign C: [0.57, 0.69]
                Campaign D: [0.78, 0.34]
                Campaign E: [0.40, 0.34]
                Campaign F: [0.35, 0.78]",
    "Requirement Analysis": "",
    "Requirement Pool": [["P0","P0 requirement"],["P1","P1 requirement"]],
    "UI Design draft": "",
    "Anything UNCLEAR": "",
}
[/CONTENT]
""",
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
## Original Requirements
{requirements}

## Search Information
{search_information}

## mermaid quadrantChart code syntax example. DONT USE QUOTO IN CODE DUE TO INVALID SYNTAX. Replace the <Campain X> with REAL COMPETITOR NAME
```mermaid
quadrantChart
    title Reach and engagement of campaigns
    x-axis Low Reach --> High Reach
    y-axis Low Engagement --> High Engagement
    quadrant-1 We should expand
    quadrant-2 Need to promote
    quadrant-3 Re-evaluate
    quadrant-4 May be improved
    "Campaign: A": [0.3, 0.6]
    "Campaign B": [0.45, 0.23]
    "Campaign C": [0.57, 0.69]
    "Campaign D": [0.78, 0.34]
    "Campaign E": [0.40, 0.34]
    "Campaign F": [0.35, 0.78]
    "Our Target Product": [0.5, 0.6]
```

## Format example
{format_example}
-----
Role: You are a professional product manager; the goal is to design a concise, usable, efficient product
Requirements: According to the context, fill in the following missing information, note that each sections are returned in Python code triple quote form seperatedly. If the requirements are unclear, ensure minimum viability and avoid excessive design
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. AND '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote. Output carefully referenced "Format example" in format.

## Original Requirements: Provide as Plain text, place the polished complete original requirements here

## Product Goals: Provided as Python list[str], up to 3 clear, orthogonal product goals. If the requirement itself is simple, the goal should also be simple

## User Stories: Provided as Python list[str], up to 5 scenario-based user stories, If the requirement itself is simple, the user stories should also be less

## Competitive Analysis: Provided as Python list[str], up to 7 competitive product analyses, consider as similar competitors as possible

## Competitive Quadrant Chart: Use mermaid quadrantChart code syntax. up to 14 competitive products. Translation: Distribute these competitor scores evenly between 0 and 1, trying to conform to a normal distribution centered around 0.5 as much as possible.

## Requirement Analysis: Provide as Plain text. Be simple. LESS IS MORE. Make your requirements less dumb. Delete the parts unnessasery.

## Requirement Pool: Provided as Python list[list[str], the parameters are requirement description, priority(P0/P1/P2), respectively, comply with PEP standards; no more than 5 requirements and consider to make its difficulty lower

## UI Design draft: Provide as Plain text. Be simple. Describe the elements and functions, also provide a simple style description and layout description.
## Anything UNCLEAR: Provide as Plain text. Make clear here.
""",
        "FORMAT_EXAMPLE": """
---
## Original Requirements
The boss ... 

## Product Goals
```python
[
    "Create a ...",
]
```

## User Stories
```python
[
    "As a user, ...",
]
```

## Competitive Analysis
```python
[
    "Python Snake Game: ...",
]
```

## Competitive Quadrant Chart
```mermaid
quadrantChart
    title Reach and engagement of campaigns
    ...
    "Our Target Product": [0.6, 0.7]
```

## Requirement Analysis
The product should be a ...

## Requirement Pool
```python
[
    ["End game ...", "P0"]
]
```

## UI Design draft
Give a basic function description, and a draft

## Anything UNCLEAR
There are no unclear points.
---
""",
    },
}

OUTPUT_MAPPING = {
    "Original Requirements": (str, ...),
    "Product Goals": (List[str], ...),
    "User Stories": (List[str], ...),
    "Competitive Analysis": (List[str], ...),
    "Competitive Quadrant Chart": (str, ...),
    "Requirement Analysis": (str, ...),
    "Requirement Pool": (List[List[str]], ...),
    "UI Design draft": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WritePRD(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, with_messages, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        # 判断哪些需求文档需要重写：调LLM判断新增需求与prd是否相关，若相关就rewrite prd
        docs_file_repo = CONFIG.git_repo.new_file_repository(DOCS_FILE_REPO)
        requirement_doc = await docs_file_repo.get(REQUIREMENT_FILENAME)
        prds_file_repo = CONFIG.git_repo.new_file_repository(PRDS_FILE_REPO)
        prd_docs = await prds_file_repo.get_all()
        change_files = Documents()
        for prd_doc in prd_docs:
            prd_doc = await self._update_prd(requirement_doc, prd_doc, prds_file_repo, *args, **kwargs)
            if not prd_doc:
                continue
            change_files.docs[prd_doc.filename] = prd_doc
        # 如果没有任何PRD，就使用docs/requirement.txt生成一个prd
        if not change_files.docs:
            prd_doc = await self._update_prd(requirement_doc, None, prds_file_repo)
            if prd_doc:
                change_files.docs[prd_doc.filename] = prd_doc
        # 等docs/prds/下所有文件都与新增需求对比完后，再触发publish message让工作流跳转到下一环节。如此设计是为了给后续做全局优化留空间。
        return ActionOutput(content=change_files.json(), instruct_content=change_files)

    async def _run_new_requirement(self, requirements, format=CONFIG.prompt_format, *args, **kwargs) -> ActionOutput:
        sas = SearchAndSummarize()
        # rsp = await sas.run(context=requirements, system_text=SEARCH_AND_SUMMARIZE_SYSTEM_EN_US)
        rsp = ""
        info = f"### Search Results\n{sas.result}\n\n### Search Summary\n{rsp}"
        if sas.result:
            logger.info(sas.result)
            logger.info(rsp)

        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(
            requirements=requirements, search_information=info, format_example=format_example
        )
        logger.debug(prompt)
        # prd = await self._aask_v1(prompt, "prd", OUTPUT_MAPPING)
        prd = await self._aask_v1(prompt, "prd", OUTPUT_MAPPING, format=format)
        return prd

    async def _is_relative_to(self, doc1, doc2) -> bool:
        return False

    async def _merge(self, doc1, doc2) -> Document:
        pass

    async def _update_prd(self, requirement_doc, prd_doc, prds_file_repo, *args, **kwargs) -> Document | None:
        if not prd_doc:
            prd = await self._run_new_requirement(
                requirements=[requirement_doc.content], format=format, *args, **kwargs
            )
            new_prd_doc = Document(
                root_path=PRDS_FILE_REPO,
                filename=FileRepository.new_file_name() + ".json",
                content=prd.instruct_content.json(),
            )
        elif await self._is_relative_to(requirement_doc, prd_doc):
            new_prd_doc = await self._merge(requirement_doc, prd_doc)
        else:
            return None
        await prds_file_repo.save(filename=new_prd_doc.filename, content=new_prd_doc.content)
        await self._save_competitive_analysis(new_prd_doc)
        await self._save_pdf(new_prd_doc)

    @staticmethod
    async def _save_competitive_analysis(prd_doc):
        m = json.loads(prd_doc.content)
        quadrant_chart = m.get("Competitive Quadrant Chart")
        if not quadrant_chart:
            return
        pathname = CONFIG.git_repo.workdir / Path(COMPETITIVE_ANALYSIS_FILE_REPO) / Path(prd_doc).with_suffix(".mmd")
        if not pathname.parent.exists():
            pathname.parent.mkdir(parents=True, exists_ok=True)
        await mermaid_to_file(quadrant_chart, pathname)

    @staticmethod
    async def _save_pdf(prd_doc):
        m = json.loads(prd_doc.content)
        file_repo = CONFIG.git_repo.new_file_repository(PRD_PDF_FILE_REPO)
        await file_repo.save(filename=prd_doc.filename, content=json_to_markdown(m))
