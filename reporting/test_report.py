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
from ..utils.dagger import with_exit_code, with_stderr, with_stdout
from ..models.contexts import GlobalContext
from ..models.pipelines import StepResult
from dagger import Client, Container, QueryError
from rich import Console
from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

console = Console()


@dataclass(frozen=True)
class GlobalTestReport:
    global_context: GLOBAL_CONTEXT
    steps_results: List[StepResult]
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def failed_steps(self) -> StepResult:
        return [step_result for step_result in self.steps_results if step_result.status is StepStatus.FAILURE]

    @property
    def successful_steps(self) -> StepResult:
        return [step_result for step_result in self.steps_results if step_result.status is StepStatus.SUCCESS]

    @property
    def skipped_steps(self) -> StepResult:
        return [step_result for step_result in self.steps_results if step_result.status is StepStatus.SKIPPED]

    @property
    def success(self) -> StepResult:
        return len(self.failed_steps) == 0 and len(self.steps_results) > 0

    @property
    def should_be_saved(self) -> bool:
        return self.global_context.is_ci

    @property
    def run_duration(self) -> int:
        return (self.created_at - self.global_context.created_at).total_seconds()

    def to_json(self) -> str:
        return json.dumps(
            {
                "run_timestamp": self.created_at.isoformat(),
                "run_duration": self.run_duration,
                "success": self.success,
                "failed_steps": [s.step.__class__.__name__ for s in self.failed_steps],
                "successful_steps": [s.step.__class__.__name__ for s in self.successful_steps],
                "skipped_steps": [s.step.__class__.__name__ for s in self.skipped_steps],
                "gha_workflow_run_url": self.global_context.gha_workflow_run_url,
                "pipeline_start_timestamp": self.global_context.pipeline_start_timestamp,
                "pipeline_end_timestamp": round(self.created_at.timestamp()),
                "pipeline_duration": round(self.created_at.timestamp()) - self.global_context.pipeline_start_timestamp,
                "git_branch": self.global_context.git_branch,
                "git_revision": self.global_context.git_revision,
                "ci_context": self.global_context.ci_context,
            }
        )

    def print(self):
        main_panel_title = Text(f"TEST RESULTS")
        main_panel_title.stylize(Style(color="blue", bold=True))
        duration_subtitle = Text(f"⏲️  Total pipeline duration: {round(self.run_duration)} seconds")
        step_results_table = Table(title="Steps results")
        step_results_table.add_column("Step")
        step_results_table.add_column("Result")
        step_results_table.add_column("Finished after")

        for step_result in self.steps_results:
            step = Text(step_result.step.title)
            step.stylize(step_result.status.get_rich_style())
            result = Text(step_result.status.value)
            result.stylize(step_result.status.get_rich_style())
            step_results_table.add_row(step, result, f"{round((self.created_at - step_result.created_at).total_seconds())}s")

        to_render = [step_results_table]
        if self.failed_steps:
            sub_panels = []
            for failed_step in self.failed_steps:
                errors = Text(failed_step.stderr)
                panel_title = Text(f"{failed_step.step.title.lower()} failures")
                panel_title.stylize(Style(color="red", bold=True))
                sub_panel = Panel(errors, title=panel_title)
                sub_panels.append(sub_panel)
            failures_group = Group(*sub_panels)
            to_render.append(failures_group)

        main_panel = Panel(Group(*to_render), title=main_panel_title, subtitle=duration_subtitle)
        console.print(main_panel)


@dataclass(frozen=True)
class PipelineTestReport:
    global_context: GLOBAL_CONTEXT
    steps_results: List[StepResult]
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def failed_steps(self) -> StepResult:
        return [step_result for step_result in self.steps_results if step_result.status is StepStatus.FAILURE]

    @property
    def successful_steps(self) -> StepResult:
        return [step_result for step_result in self.steps_results if step_result.status is StepStatus.SUCCESS]

    @property
    def skipped_steps(self) -> StepResult:
        return [step_result for step_result in self.steps_results if step_result.status is StepStatus.SKIPPED]

    @property
    def success(self) -> StepResult:
        return len(self.failed_steps) == 0 and len(self.steps_results) > 0

    @property
    def should_be_saved(self) -> bool:
        return self.global_context.is_ci

    @property
    def run_duration(self) -> int:
        return (self.created_at - self.global_context.created_at).total_seconds()

    def to_json(self) -> str:
        return json.dumps(
            {
                "run_timestamp": self.created_at.isoformat(),
                "run_duration": self.run_duration,
                "success": self.success,
                "failed_steps": [s.step.__class__.__name__ for s in self.failed_steps],
                "successful_steps": [s.step.__class__.__name__ for s in self.successful_steps],
                "skipped_steps": [s.step.__class__.__name__ for s in self.skipped_steps],
                "gha_workflow_run_url": self.global_context.gha_workflow_run_url,
                "pipeline_start_timestamp": self.global_context.pipeline_start_timestamp,
                "pipeline_end_timestamp": round(self.created_at.timestamp()),
                "pipeline_duration": round(self.created_at.timestamp()) - self.global_context.pipeline_start_timestamp,
                "git_branch": self.global_context.git_branch,
                "git_revision": self.global_context.git_revision,
                "ci_context": self.global_context.ci_context,
            }
        )

    def print(self):
        main_panel_title = Text(f"TEST RESULTS")
        main_panel_title.stylize(Style(color="blue", bold=True))
        duration_subtitle = Text(f"⏲️  Total pipeline duration: {round(self.run_duration)} seconds")
        step_results_table = Table(title="Steps results")
        step_results_table.add_column("Step")
        step_results_table.add_column("Result")
        step_results_table.add_column("Finished after")

        for step_result in self.steps_results:
            step = Text(step_result.step.title)
            step.stylize(step_result.status.get_rich_style())
            result = Text(step_result.status.value)
            result.stylize(step_result.status.get_rich_style())
            step_results_table.add_row(step, result, f"{round((self.created_at - step_result.created_at).total_seconds())}s")

        to_render = [step_results_table]
        if self.failed_steps:
            sub_panels = []
            for failed_step in self.failed_steps:
                errors = Text(failed_step.stderr)
                panel_title = Text(f"{failed_step.step.title.lower()} failures")
                panel_title.stylize(Style(color="red", bold=True))
                sub_panel = Panel(errors, title=panel_title)
                sub_panels.append(sub_panel)
            failures_group = Group(*sub_panels)
            to_render.append(failures_group)

        main_panel = Panel(Group(*to_render), title=main_panel_title, subtitle=duration_subtitle)
        console.print(main_panel)

