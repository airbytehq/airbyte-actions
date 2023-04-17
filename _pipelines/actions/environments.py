#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

"""This modules groups functions made to create reusable environments packaged in dagger containers."""
from __future__ import annotations
from typing import List, TYPE_CHECKING

from dagger import CacheSharingMode, CacheVolume, Container, Client

PYPROJECT_TOML_FILE_PATH = "pyproject.toml"

if TYPE_CHECKING:
    from src.models.contexts import PipelineContext


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
    assert isinstance(context.dagger_client, Client)
    pip_cache: CacheVolume = context.dagger_client.cache_volume("pip_cache")
    
    return (
        context.dagger_client.container()
        .from_(runner_image_name)
        .with_mounted_cache("/root/.cache/pip", pip_cache, sharing=CacheSharingMode.SHARED)
        .with_exec(["pip", "install", "--upgrade", "pip"])
    )

