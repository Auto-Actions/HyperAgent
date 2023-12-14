#!/usr/bin/env python
"""
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Coroutine, Dict, Literal, overload

from metagpt.config import CONFIG
from metagpt.tools import WebBrowserEngineType
from metagpt.utils.parse_html import WebPage


class WebBrowserEngine:
    def __init__(
        self,
        options: Dict,
        engine: WebBrowserEngineType | None = None,
        run_func: Callable[..., Coroutine[Any, Any, WebPage | list[WebPage]]] | None = None,
    ):
        engine = engine or CONFIG.web_browser_engine
        if engine is None:
            raise NotImplementedError

        if WebBrowserEngineType(engine) is WebBrowserEngineType.PLAYWRIGHT:
            module = "metagpt.tools.web_browser_engine_playwright"
            run_func = importlib.import_module(module).PlaywrightWrapper().run
        elif WebBrowserEngineType(engine) is WebBrowserEngineType.SELENIUM:
            module = "metagpt.tools.web_browser_engine_selenium"
            run_func = importlib.import_module(module).SeleniumWrapper().run
        elif WebBrowserEngineType(engine) is WebBrowserEngineType.CUSTOM:
            run_func = run_func
        else:
            raise NotImplementedError
        self.run_func = run_func
        self.engine = engine

    @overload
    async def run(self, url: str) -> WebPage:
        ...

    @overload
    async def run(self, url: str, *urls: str) -> list[WebPage]:
        ...

    async def run(self, url: str, *urls: str) -> WebPage | list[WebPage]:
        return await self.run_func(url, *urls)


if __name__ == "__main__":
    import fire

    async def main(url: str, *urls: str, engine_type: Literal["playwright", "selenium"] = "playwright", **kwargs):
        return await WebBrowserEngine(engine=WebBrowserEngineType(engine_type), **kwargs).run(url, *urls)

    fire.Fire(main)
