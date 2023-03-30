#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

"""This modules groups functions made to create reusable environments packaged in dagger containers."""

from typing import List, Optional

from ci_connector_ops.pipelines.contexts import ConnectorTestContext
from ...utils.repo import get_file_contents
from dagger import CacheSharingMode, CacheVolume, Container, Directory, Secret

PYPROJECT_TOML_FILE_PATH = "pyproject.toml"

CI_CONNECTOR_OPS_SOURCE_PATH = "tools/ci_connector_ops"


def with_actions_runner_base(context: PipelineContext, runner_image_name: str = "summerwind/actions-runner:ubuntu-22.04") -> Container:
    """Builds an actions runner with a cache volume for cache.

    Args:
        context (ConnectorTestContext): The current test context, providing a dagger client and a repository directory.
        python_image_name (str, optional): The python image to use to build the python base environment. Defaults to "python:3.9-slim".

    Raises:
        ValueError: Raised if the python_image_name is not a python image.

    Returns:
        Container: The python base environment container.
    """
    if not python_image_name.startswith("python:3"):
        raise ValueError("You have to use a python image to build the python base environment")
    pip_cache: CacheVolume = context.dagger_client.cache_volume("pip_cache")
    return (
        context.dagger_client.container()
        .from_(python_image_name)
        .with_mounted_cache("/root/.cache/pip", pip_cache, sharing=CacheSharingMode.SHARED)
        .with_mounted_directory("/tools", context.get_repo_dir("tools", include=["ci_credentials", "ci_common_utils"], exclude=[".venv"]))
        .with_exec(["pip", "install", "--upgrade", "pip"])
    )

