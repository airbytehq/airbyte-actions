#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import itertools
import logging
import os
import sys
sys.path.insert(0, os.getcwd())
from pathlib import Path
from typing import List, Tuple, Any

from asyncer import create_task_group
import anyio
from _pipelines.actions_runner import ActionsRunnerPipeline
from src.models.contexts import GlobalContext
from src.reporting.test_report import GlobalTestReport
from src.utils.repo import is_local, get_current_git_branch, get_current_git_revision, get_current_git_repo
from rich.logging import RichHandler

GIT_REPOSITORY = "airbytehq/airbyte_actions"
GLOBAL_CONTEXT = GlobalContext(is_local = is_local()
                               , git_branch = get_current_git_branch()
                               , git_revision = get_current_git_revision()
                               , git_repo_url = get_current_git_repo())

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])

logger = logging.getLogger(__name__)

# PASS IN CONFIG VIA CLI ARGUMENTS
async def _run(context: GlobalContext) -> GlobalTestReport:

    ## THIS IS WHERE YOU HAVE SOME CASE SWITCH TO DETERMINE WHICH TASKS TO PUT INTO THE QUEUE

    """Runs airbyte_actions ci pipeline

    Args:
        context (GlobalContext): The initialized global test context.

    Returns:
        GlobalTestReport: The test reports holding tests results.
    """
    async with context:
        async with create_task_group() as task_group:
            tasks: list[Any] = [
                task_group.soonify(ActionsRunnerPipeline(context)._run)(),
                ## Pipeline 2 here
                # pipeline 3 here 

            ]
        results = list(itertools.chain(*(task.value for task in tasks)))

        context.test_report = GlobalTestReport(context, pipelines_results=results)
    assert(isinstance(context.test_report, GlobalTestReport))
    return context.test_report


if __name__ == "__main__":
    anyio.run(_run)
