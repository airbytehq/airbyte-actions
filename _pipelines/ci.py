#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import itertools
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Any

import asyncer
import anyio
from .._pipelines.actions_runner import ActionsRunnerPipeline
from ..models.contexts import GlobalContext
from ..reporting.test_report import GlobalTestReport
from ..utils.repo import is_local, get_current_git_branch, get_current_git_revision
from rich.logging import RichHandler

GIT_REPOSITORY = "airbytehq/airbyte_actions"
GLOBAL_CONTEXT = GlobalContext(is_local = is_local()
                               , git_branch = get_current_git_branch()
                               , git_revision = get_current_git_revision()
                               , git_repo_url = GIT_REPOSITORY)

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])

logger = logging.getLogger(__name__)

# PASS IN CONFIG VIA CLI ARGUMENTS
async def run(context: GlobalContext, **kwargs: dict[str, Any]) -> GlobalTestReport:

    ## THIS IS WHERE YOU HAVE SOME CASE SWITCH TO DETERMINE WHICH TASKS TO PUT INTO THE QUEUE

    """Runs airbyte_actions ci pipeline

    Args:
        context (GlobalContext): The initialized global test context.

    Returns:
        GlobalTestReport: The test reports holding tests results.
    """
    async with context:
        async with asyncer.create_task_group() as task_group:
            tasks: list[Any] = [
                task_group.soonify(ActionsRunnerPipeline(context).run)(),
                ## Pipeline 2 here
                # pipeline 3 here 

            ]
        results = list(itertools.chain(*(task.value for task in tasks)))

        context.test_report = GlobalTestReport(context, steps_results=results)

    return context.test_report


if __name__ == "__main__":
    anyio.run(GLOBAL_CONTEXT, backend="asyncio")
