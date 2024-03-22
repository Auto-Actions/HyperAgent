import uvicorn
# from fastapi_rfc7807 import middleware
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

from .api.views import github_intergration
from .api.views import program_generation
# from .api.views.program_generation import MetaGPTIntegration

from .config import config
from .api.common import app
from .logs import logger


# middleware.register(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
config_env = config.load_env()

# def get_github_integration():
#     return GitHubIntegration(token=config_env.get("GITHUB_TOKEN", ""))

# def get_metagpt_integration():
#     return MetaGPTIntegration()

# class FastAPIServer:
#     def __init__(self):
#         self.setup_api_endpoints()

#     def uvicorn_server(self):
#         uvicorn.run(app, host="0.0.0.0", port=8000)

#     def setup_api_endpoints(self):
#         app.post("/generate-and-push-code/")(self.generate_and_push_code)

#     async def generate_and_push_code(self, repository: str, requirements: str, github_integration: GitHubIntegration = Depends(get_github_integration), metagpt_integration: MetaGPTIntegration = Depends(get_metagpt_integration)):
#         try:
#             generated_code = await metagpt_integration.generate_code(requirements)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Failed to generate code: {str(e)}")

#         try:
#             success = await github_integration.push_code(repository, generated_code)
#             if not success:
#                 raise HTTPException(status_code=500, detail="Failed to push code to GitHub.")
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Failed to push code to GitHub: {str(e)}")

#         return {"message": "Code generated and pushed successfully."}
    

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        # swagger_js_url="/static/swagger-ui-bundle.js",
        # swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


app.include_router(github_intergration.router, prefix=config.PREFIX)
app.include_router(program_generation.router, prefix=config.PREFIX)


def run_app():
    uvicorn.run('fastapi_metagpt_integration.main:app', host=config_env.get('UVICORN_HOST', '0.0.0.0'), port=int(config_env.get('UVICORN_PORT', '8000')), reload=True)


if __name__ == "__main__":
    # server = FastAPIServer()
    # server.uvicorn_server()
    logger.info('Launching Auto Startup service')
    run_app()