
import anyio
import git
import os
from dagger import Config, Connection, Container, QueryError
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from logging import Logger

from github import Github

console = Console()

def get_current_git_branch() -> str:
    return git.Repo().active_branch.name


def get_current_git_revision() -> str:
    return git.Repo().head.object.hexsha


def get_current_epoch_time() -> int:
    return round(datetime.datetime.utcnow().timestamp())


async def get_modified_files_remote(current_git_branch: str, current_git_revision: str, diffed_branch: str = "origin/master") -> Set[str]:
    async with Connection(DAGGER_CONFIG) as dagger_client:
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
                    AIRBYTE_REPO_URL,
                ]
            )
            .with_exec(["checkout", "-t", f"origin/{current_git_branch}"])
            .with_exec(["diff", "--diff-filter=MA", "--name-only", f"{diffed_branch}...{current_git_revision}"])
            .stdout()
        )
    return set(modified_files.split("\n"))


def get_modified_files_local(current_git_revision: str, diffed_branch: str = "master") -> Set[str]:
    airbyte_repo = git.Repo()
    modified_files = airbyte_repo.git.diff("--diff-filter=MA", "--name-only", f"{diffed_branch}...{current_git_revision}").split("\n")
    return set(modified_files)


def get_modified_files(current_git_branch: str, current_git_revision: str, diffed_branch: str, is_local: bool = True) -> Set[str]:
    if is_local:
        return get_modified_files_local(current_git_revision, diffed_branch)
    else:
        return anyio.run(get_modified_files_remote, current_git_branch, current_git_revision, diffed_branch)
    

def is_local() -> bool:
    return os.getenv("CI") is None

def update_commit_status_check(
    sha: str, state: str, target_url: str, description: str, context: str, should_send=True, logger: Logger = None, repo: str = None
):
    if not should_send:
        return

    try:
        github_client = Github(os.environ["CI_GITHUB_ACCESS_TOKEN"])
        airbyte_repo = github_client.get_repo(repo)
    except Exception as e:
        if logger:
            logger.error("No commit status check sent, the connection to Github API failed", exc_info=True)
        else:
            console.print(e)
        return

    airbyte_repo.get_commit(sha=sha).create_status(
        state=state,
        target_url=target_url,
        description=description,
        context=context,
    )
    logger.info(f"Created {state} status for commit {sha} on Github in {context} context.")
