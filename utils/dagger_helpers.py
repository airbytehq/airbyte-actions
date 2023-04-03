#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import datetime
import re
import sys
from pathlib import Path
from typing import Optional, Set

import anyio
import git
from dagger import Config, Connection, Container, QueryError

DAGGER_CONFIG = Config(log_output=sys.stderr)


# This utils will probably be redundant once https://github.com/dagger/dagger/issues/3764 is implemented
async def check_path_in_workdir(container: Container, path: str) -> bool:
    """Check if a local path is mounted to the working directory of a container

    Args:
        container (Container): The container on which we want the check the path existence.
        path (str): Directory or file path we want to check the existence in the container working directory.

    Returns:
        bool: Whether the path exists in the container working directory.
    """
    workdir = (await container.with_exec(["pwd"]).stdout()).strip()
    mounts = await container.mounts()
    if workdir in mounts:
        expected_file_path = Path(workdir[1:]) / path
        return expected_file_path.is_file() or expected_file_path.is_dir()
    else:
        return False


# This utils will probably be redundant once https://github.com/dagger/dagger/issues/3764 is implemented
async def get_file_contents(container: Container, path: str) -> Optional[str]:
    """Retrieve a container file contents.

    Args:
        container (Container): The container hosting the file you want to read.
        path (str): Path, in the container, to the file you want to read.

    Returns:
        Optional[str]: The file content if the file exists in the container, None otherwise.
    """
    try:
        res = await container.file(path).contents()
        return res
    except QueryError as e:
        if "no such file or directory" not in str(e):
            # this is the hicky bit of the stopgap because
            # this error could come from a network issue
            raise
    return None


# This is a stop-gap solution to capture non 0 exit code on Containers
# The original issue is tracked here https://github.com/dagger/dagger/issues/3192
async def with_exit_code(container: Container) -> int:
    """Read the container exit code. If the exit code is not 0 a QueryError is raised. We extract the non-zero exit code from the QueryError message.

    Args:
        container (Container): The container from which you want to read the exit code.

    Returns:
        int: The exit code.
    """
    try:
        await container.exit_code()
    except QueryError as e:
        error_message = str(e)
        if "exit code: " in error_message:
            exit_code = re.search(r"exit code: (\d+)", error_message)
            if exit_code:
                return int(exit_code.group(1))
            else:
                return 1
        raise
    return 0


async def with_stderr(container: Container) -> str:
    try:
        return await container.stderr()
    except QueryError as e:
        return str(e)


async def with_stdout(container: Container) -> str:
    try:
        return await container.stdout() 
    except QueryError as e:
        return str(e)
