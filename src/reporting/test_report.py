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
from ..utils.repo import is_local, get_current_git_branch, get_current_git_revision, get_current_git_repo
from ..models.pipeline import PipelineResult, PipelineStatus
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

console = Console()

if TYPE_CHECKING:
    from ..models.contexts import GlobalContext, PipelineContext

@dataclass(frozen=True)
class GlobalTestReport():

    global_context: GlobalContext
    pipelines_results: List[PipelineResult]
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def failed_pipelines(self) -> List[PipelineResult]:
        return [pipeline_result for pipeline_result in self.pipelines_results if pipeline_result.status is PipelineStatus.FAILURE]

    @property
    def successful_pipelines(self) -> List[PipelineResult]:
        return [pipeline_result for pipeline_result in self.pipelines_results if pipeline_result.status is PipelineStatus.SUCCESS]

    @property
    def skipped_pipelines(self) -> List[PipelineResult]:
        return [pipeline_result for pipeline_result in self.pipelines_results if pipeline_result.status is PipelineStatus.SKIPPED]

    @property
    def success(self) -> bool:
        return len(self.failed_pipelines) == 0 and len(self.pipelines_results) > 0

    @property
    def should_be_saved(self) -> bool:
        assert isinstance(self.global_context.is_ci, bool)
        return self.global_context.is_ci

    @property
    def run_duration(self) -> float:
        assert isinstance(self.global_context.created_at, datetime)
        return (self.created_at - self.global_context.created_at).total_seconds()

    def to_json(self) -> str:
        return json.dumps(
            {
                "run_timestamp": self.created_at.isoformat(),
                "run_duration": self.run_duration,
                "success": self.success,
                "failed_steps": [s.pipeline.__class__.__name__ for s in self.failed_pipelines],
                "successful_steps": [s.pipeline.__class__.__name__ for s in self.successful_pipelines],
                "skipped_steps": [s.pipeline.__class__.__name__ for s in self.skipped_pipelines],
                "gha_workflow_run_url": self.global_context.gha_workflow_run_url,
                "pipeline_start_timestamp": self.global_context.pipeline_start_timestamp,
                "pipeline_end_timestamp": round(self.created_at.timestamp()),
                "pipeline_duration": round(self.created_at.timestamp()) - int(self.global_context.pipeline_start_timestamp if self.global_context.pipeline_start_timestamp is not None else 0),
                "git_branch": self.global_context.git_branch,
                "git_revision": self.global_context.git_revision,
                "ci_context": self.global_context.ci_context,
            }
        )

    def print(self) -> None:
        main_panel_title = Text(f"TEST RESULTS")
        main_panel_title.stylize(Style(color="blue", bold=True))
        duration_subtitle = Text(f"⏲️  Total pipeline duration: {round(self.run_duration)} seconds")
        pipeline_results_table = Table(title="Pipeline results")
        pipeline_results_table.add_column("Pipeline")
        pipeline_results_table.add_column("Result")
        pipeline_results_table.add_column("Finished after")

        for pipeline_result in self.pipelines_results:
            pipeline = Text(pipeline_result.pipeline.title)
            pipeline.stylize(pipeline_result.status.get_rich_style())
            result = Text(pipeline_result.status.value)
            result.stylize(pipeline_result.status.get_rich_style())
            pipeline_results_table.add_row(pipeline, result, f"{round((self.created_at - pipeline_result.created_at).total_seconds())}s")

        to_render: list[Table | Group] = [pipeline_results_table]
        if self.failed_pipelines:
            sub_panels = []
            for failed_pipeline in self.failed_pipelines:
                errors = Text(failed_pipeline.stderr if failed_pipeline.stderr else "No error message")
                panel_title = Text(f"{failed_pipeline.pipeline.title.lower()} failures")
                panel_title.stylize(Style(color="red", bold=True))
                sub_panel = Panel(errors, title=panel_title)
                sub_panels.append(sub_panel)
            failures_group = Group(*sub_panels)
            to_render.append(failures_group)

        main_panel = Panel(Group(*to_render), title=main_panel_title, subtitle=duration_subtitle)
        console.print(main_panel)


@dataclass(frozen=True)
class PipelineTestReport(GlobalTestReport):
    #def __init__(self, global_context: GlobalContext, pipeline_context: pipeline_context) -> None:
        #self.context = context
    pipeline_context: PipelineContext = PipelineContext(is_local = is_local()
                               , git_branch = get_current_git_branch()
                               , git_revision = get_current_git_revision()
                               , git_repo_url = get_current_git_repo())
    global_context: GlobalContext
    
   
