from __future__ import annotations
import anyio
from git.repo import Repo
import os
from typing import Set
import logging
from dagger import Config, Connection, Client


import os
from typing import TYPE_CHECKING

import datetime

from rich.console import Console

if TYPE_CHECKING:
    from logging import Logger

from github import Github

console = Console()

def get_current_git_branch() -> str:
    return str(Repo().active_branch.name)


def get_current_git_revision() -> str:
    return str(Repo().head.object.hexsha)


def get_current_epoch_time() -> int:
    return round(datetime.datetime.utcnow().timestamp())

def get_current_git_repo() -> str:
    repo = Repo()
    if isinstance(repo, str):
        return str(repo.working_tree_dir.split("/")[-1])
    return "local"


async def get_modified_files_remote(dagger_client: Client, url: str, current_git_branch: str, current_git_revision: str, diffed_branch: str = "origin/master") -> Set[str]:
    modified_files = await (
        dagger_client.container()
        .from_("alpine/git:latest")
        .with_workdir("/repo")
        .with_exec(["init"])
        .with_env_variable("CACHEBUSTER", current_git_revision)
        .with_exec(
            [
                "remote",
                "add",
                "--fetch",
                "--track",
                diffed_branch.split("/")[-1],
                "--track",
                current_git_branch,
                "origin",
                url,
            ]
        )
        .with_exec(["checkout", "-t", f"origin/{current_git_branch}"])
        .with_exec(["diff", "--diff-filter=MA", "--name-only", f"{diffed_branch}...{current_git_revision}"])
        .stdout()
    )
    return set(modified_files.split("\n"))


def get_modified_files_local(current_git_revision: str, diffed_branch: str = "master") -> Set[str]:
    airbyte_repo = Repo()
    modified_files = airbyte_repo.git.diff("--diff-filter=MA", "--name-only", f"{diffed_branch}...{current_git_revision}").split("\n")
    return set(modified_files)


def get_modified_files(current_git_branch: str, current_git_revision: str, diffed_branch: str, is_local: bool = True) -> Set[str]:
    if is_local:
        return get_modified_files_local(current_git_revision, diffed_branch)
    else:
        return anyio.run(get_modified_files_remote, current_git_branch, current_git_revision, diffed_branch)
    

def is_local() -> bool:
    return os.getenv("CI") is None

def update_commit_status_check(sha: str, state: str, target_url: str, description: str, context: str, should_send: bool =True, logger: Logger = logging.getLogger(__name__), repo: str = "local") -> None:
    if not should_send:
        return
    try:
        github_client = Github(os.environ["CI_GITHUB_ACCESS_TOKEN"])
        airbyte_repo = github_client.get_repo(repo)
    except Exception as e:
        logger.error("No commit status check sent, the connection to Github API failed", exc_info=True)
        return

    airbyte_repo.get_commit(sha=sha).create_status(
        state=state,
        target_url=target_url,
        description=description,
        context=context,
    )
    logger.info(f"Created {state} status for commit {sha} on Github in {context} context.")
