#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

from __future__ import annotations
import logging



import anyio
from .actions.environments import with_actions_runner_base
from typing import List, TYPE_CHECKING

from src.utils.repo import is_local, get_current_git_branch, get_current_git_revision, get_current_git_repo
from rich.logging import RichHandler
from dagger import Container

if TYPE_CHECKING: 
    from src.models.contexts import GlobalContext, PipelineContext
    from src.models.pipeline import Pipeline, PipelineResult
    from src.reporting.test_report import PipelineTestReport

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])

logger = logging.getLogger(__name__)

class ActionsRunnerPipeline(Pipeline):
    title = "Actions Runner Pipeline"

    async def _run(self) -> PipelineResult:
        actions_runner_base = with_actions_runner_base(self.pipeline_context)
        pipeline = self.get_dagger_pipeline(actions_runner_base)
        if isinstance(pipeline, Container):
            actions_runner_base = pipeline
        filtered_repo = self.pipeline_context.get_repo_dir(
            include=[
                "."
            ],
        )
        airbyte_runner_image = (
            actions_runner_base.with_mounted_directory("/airbyte", filtered_repo)
            .with_workdir("/airbyte")
        )
        return await self.get_pipeline_result(airbyte_runner_image)


if __name__ == "__main__":
    GLOBAL_CONTEXT = GlobalContext(is_local = is_local()
                               , git_branch = get_current_git_branch()
                               , git_revision = get_current_git_revision()
                               , git_repo_url = get_current_git_repo())

    anyio.run(ActionsRunnerPipeline(GLOBAL_CONTEXT)._run)
