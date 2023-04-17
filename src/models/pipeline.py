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
from ..utils.dagger_helpers import with_exit_code, with_stderr, with_stdout
from dagger import Client, Container
from rich.style import Style
from .contexts import GlobalContext, PipelineContext


class PipelineStatus(Enum):
    SUCCESS = "Successful"
    FAILURE = "Failed"
    SKIPPED = "Skipped"

    def from_exit_code(self, exit_code: int) -> PipelineStatus:
        if exit_code == 0:
            return PipelineStatus.SUCCESS
        if exit_code == 1:
            return PipelineStatus.FAILURE
        # pytest returns a 5 exit code when no test is found.
        if exit_code == 5:
            return PipelineStatus.SKIPPED
        else:
            raise ValueError(f"No pipeline status is mapped to exit code {exit_code}")

    def get_rich_style(self) -> Style:
        if self is PipelineStatus.SUCCESS:
            return Style(color="green")
        if self is PipelineStatus.FAILURE:
            return Style(color="red", bold=True)
        if self is PipelineStatus.SKIPPED:
            return Style(color="yellow")

    def __str__(self) -> str:
        return self.value


class Pipeline(ABC):
    title: ClassVar

    def __init__(self, context: GlobalContext) -> None:
        self.global_context = context
        self.pipeline_context = PipelineContext(
            is_local=context.is_local,
            git_branch=context.git_branch,
            git_revision=context.git_revision,
            git_repo_url=context.git_repo_url,
        )

    @abstractmethod
    async def _run(self) -> PipelineResult:
        """Run the pipeline and output a pipeline result.

        Returns:
            PipelineResult: The result of the pipeline run.
        """
        ...

    def skip(self, reason: Optional[str] = None) -> PipelineResult:
        return PipelineResult(self, PipelineStatus.SKIPPED, stdout=reason)

    def get_dagger_pipeline(self, dagger_client_or_container: Union[Client, Container]) -> Client | Container:
        return dagger_client_or_container.pipeline(self.title)

    async def get_pipeline_result(self, container: Container) -> PipelineResult:
        """Concurrent retrieval of exit code, stdout and stdout of a container.
        Create a PipelineResult object from these objects.

        Args:
            container (Container): The container from which we want to infer a step result/

        Returns:
            PipelineResult: Failure or success with stdout and stderr.
        """
        pipeline_status = PipelineStatus(self.title)
        async with asyncer.create_task_group() as task_group:
            soon_exit_code = task_group.soonify(with_exit_code)(container)
            soon_stderr = task_group.soonify(with_stderr)(container)
            soon_stdout = task_group.soonify(with_stdout)(container)
        return PipelineResult(self, pipeline_status.from_exit_code(soon_exit_code.value), stderr=soon_stderr.value, stdout=soon_stdout.value)


@dataclass(frozen=True)
class PipelineResult:
    pipeline: Pipeline
    status: PipelineStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    stderr: Optional[str] = None
    stdout: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.pipeline.title}: {self.status.value}"

