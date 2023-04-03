#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, List, Optional, Union

import asyncer
from utils.dagger_helpers import with_exit_code, with_stderr, with_stdout
from dagger import Client, Container
from rich.style import Style

if TYPE_CHECKING:
    from contexts import GlobalContext


class StepStatus(Enum):
    SUCCESS = "Successful"
    FAILURE = "Failed"
    SKIPPED = "Skipped"

    def from_exit_code(self, exit_code: int) -> StepStatus:
        if exit_code == 0:
            return StepStatus.SUCCESS
        if exit_code == 1:
            return StepStatus.FAILURE
        # pytest returns a 5 exit code when no test is found.
        if exit_code == 5:
            return StepStatus.SKIPPED
        else:
            raise ValueError(f"No step status is mapped to exit code {exit_code}")

    def get_rich_style(self) -> Style:
        if self is StepStatus.SUCCESS:
            return Style(color="green")
        if self is StepStatus.FAILURE:
            return Style(color="red", bold=True)
        if self is StepStatus.SKIPPED:
            return Style(color="yellow")

    def __str__(self) -> str:
        return self.value


class Step(ABC):
    title: ClassVar

    def __init__(self, context: GlobalContext) -> None:
        self.context = context

    @abstractmethod
    async def run(self) -> StepResult:
        """Run the step and output a step result.

        Returns:
            StepResult: The result of the step run.
        """
        ...

    def skip(self, reason: Optional[str] = None) -> StepResult:
        return StepResult(self, StepStatus.SKIPPED, stdout=reason)

    def get_dagger_pipeline(self, dagger_client_or_container: Union[Client, Container]) -> Union[Client, Container]:
        return dagger_client_or_container.pipeline(self.title)

    async def get_step_result(self, container: Container) -> StepResult:
        """Concurrent retrieval of exit code, stdout and stdout of a container.
        Create a StepResult object from these objects.

        Args:
            container (Container): The container from which we want to infer a step result/

        Returns:
            StepResult: Failure or success with stdout and stderr.
        """
        async with asyncer.create_task_group() as task_group:
            soon_exit_code = task_group.soonify(with_exit_code)(container)
            soon_stderr = task_group.soonify(with_stderr)(container)
            soon_stdout = task_group.soonify(with_stdout)(container)
        return StepResult(self, StepStatus.from_exit_code(soon_exit_code.value), stderr=soon_stderr.value, stdout=soon_stdout.value)


@dataclass(frozen=True)
class StepResult:
    step: Step
    status: StepStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    stderr: Optional[str] = None
    stdout: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.step.title}: {self.status.value}"

