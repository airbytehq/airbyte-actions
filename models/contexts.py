#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any

from anyio import Path
from asyncer import asyncify
from ..reporting.test_report import GlobalTestReport, PipelineTestReport
from ..utils.gh import update_commit_status_check
from dagger import Config, Client, Directory, GitRepository


class ContextState(Enum):
    INITIALIZED = {"github_state": "pending", "description": "Tests are being initialized..."}
    RUNNING = {"github_state": "pending", "description": "Tests are running..."}
    ERROR = {"github_state": "error", "description": "Something went wrong while running the tests."}
    SUCCESSFUL = {"github_state": "success", "description": "All tests ran successfully."}
    FAILURE = {"github_state": "failure", "description": "Test failed."}

class GlobalContext():
    """The global context is used to store configuration for the entire CI run"""

    def __init__(
        self,
        is_local: bool,
        git_branch: str,
        git_revision: str,
        git_repo_url: str,
        gha_workflow_run_url: Optional[str] = None,
        ci_context: Optional[str] = None,
    ):
        self.is_local = is_local
        self.git_branch = git_branch
        self.git_revision = git_revision
        self.git_repo_url = git_repo_url
        self.gha_workflow_run_url = gha_workflow_run_url
        self.created_at = datetime.utcnow()
        self.ci_context = ci_context

        self.state = ContextState.INITIALIZED
        self.logger = logging.getLogger(self.main_pipeline_name)
        self.dagger_client = None
        self._secrets_dir = None
        self._test_report = None
        update_commit_status_check(**self.github_commit_status)

    @property
    def secrets_dir(self) -> Directory:
        return self._secrets_dir

    @secrets_dir.setter
    def secrets_dir(self, secrets_dir: Directory) -> Directory:
        self._secrets_dir = secrets_dir

    @property
    def dagger_client(self) -> Client:
        return self._dagger_client

    @dagger_client.setter
    def dagger_client(self, dagger_client: Client) -> Client:
        self._dagger_client = dagger_client

    @property
    def dagger_config(self) -> Config:
        return self.dagger_config

    @property
    def is_ci(self) -> bool:
        return self.is_local is False

    @property
    def repo(self) -> GitRepository:
        return self.dagger_client.git(self.git_repo_url, keep_git_dir=True)

    @property
    def main_pipeline_name(self) -> str:
        return f"Dagger CI for {self.git_repo_url}"

    @property
    def test_report(self) -> GlobalTestReport:
        return self._test_report

    @test_report.setter
    def test_report(self, test_report: GlobalTestReport) -> None:
        self._test_report = test_report
        self.state = ContextState.SUCCESSFUL if test_report.success else ContextState.FAILURE

    @property
    def github_commit_status(self) -> dict[str, Any]:
        return {
            "sha": self.git_revision,
            "state": self.state.value["github_state"],
            "target_url": self.gha_workflow_run_url,
            "description": self.state.value["description"],
            "context": f"Dagger CI for {self.git_repo_url}",
            "should_send": self.is_ci,
            "logger": self.logger,
        }

    def get_repo_dir(self, subdir: str=".", exclude:Optional[List[str]]=None, include=None) -> Directory:
        if self.is_local:
            return self.dagger_client.host().directory(subdir, exclude=exclude, include=include)
        else:
            return self.repo.branch(self.git_branch).tree().directory(subdir)


    async def __aenter__(self):
        if self.dagger_client is None:
            self.dagger_client = Client() 
        self.state = ContextState.RUNNING
        await asyncify(update_commit_status_check)(**self.github_commit_status)
        return self

    async def __aexit__(self, exception_type, exception_value, traceback) -> bool:
        if exception_value:
            self.logger.error("An error got handled by the ConnectorTestContext", exc_info=True)
            self.state = ContextState.ERROR
        elif self.test_report is None:
            self.logger.error("No test report was provided. This is probably due to an upstream error")
            self.state = ContextState.ERROR
            return True
        else:
            self.dagger_client = self.dagger_client.pipeline(f"Teardown {self.connector.technical_name}")
            if self.should_save_updated_secrets:
                await secrets.upload(self)
            self.test_report.print()
            self.logger.info(self.test_report.to_json())
            local_test_reports_path_root = "/"
            git_revision = self.test_report.connector_test_context.git_revision
            git_branch = self.test_report.connector_test_context.git_branch.replace("/", "_")
            suffix = f"/{git_branch}/{git_revision}.json"
            local_report_path = Path(local_test_reports_path_root + suffix)
            await local_report_path.parents[0].mkdir(parents=True, exist_ok=True)
            await local_report_path.write_text(self.test_report.to_json())
            if self.test_report.should_be_saved:
                s3_reports_path_root = "python-poc/tests/history/"
                s3_key = s3_reports_path_root + suffix
                report_upload_exit_code = await remote_storage.upload_to_s3(
                    self.dagger_client, str(local_report_path), s3_key, os.environ["TEST_REPORTS_BUCKET_NAME"]
                )
                if report_upload_exit_code != 0:
                    self.logger.error("Uploading the report to S3 failed.")

        await asyncify(update_commit_status_check)(**self.github_commit_status)
        return True


class PipelineContext(GlobalContext):
    pass
    """The pipeline context is used to store configuration for a specific pipeline run. 
    
    It extends the GlobalContext class"""

class GitContext(GlobalContext):
    pass
    """The pipeline context is used to store configuration for a specific pipeline run. 
    
    It extends the GlobalContext class"""
