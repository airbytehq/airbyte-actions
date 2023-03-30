#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import logging

from actions.environments import with_actions_runner_base
from typing import List
from ..models.contexts import GlobalContext, PipelineContext
from ..models.pipelines import Step, StepResult
from ..reporting.test_report import PipelineTestReport
from rich.logging import RichHandler

GLOBAL_CONTEXT = GlobalContext()

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])

logger = logging.getLogger(__name__)

class ActionsRunnerPipeline(Step):
    title = "Actions Runner Pipeline"

    async def _run(self) -> List[StepResult]:
        """
        """
        actions_runner_base = await with_actions_runner_base(self.context)
        actions_runner_base = self.get_dagger_pipeline(actions_runner_base)
        filtered_repo = self.context.get_repo_dir(
            include=[
                str(self.context.connector.code_directory),
                str(self.context.connector.documentation_file_path),
                str(self.context.connector.icon_path),
                "airbyte-config/init/src/main/resources/seed/source_definitions.yaml",
                "airbyte-config/init/src/main/resources/seed/destination_definitions.yaml",
            ],
        )
        airbyte_runner_image = (
            actions_runner_base.with_mounted_directory("/airbyte", filtered_repo)
            .with_workdir("/airbyte")
            .with_exec(["run-qa-checks", f"connectors/{self.context.connector.technical_name}"])
        )
        return [await self.get_step_result(airbyte_runner_image)]


if __name__ == "__main__":
    run(GLOBAL_CONTEXT)
