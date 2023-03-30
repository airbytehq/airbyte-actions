from pathlib import Path
import os
import anyio
from dagger import Container
from ...models import contexts
from datetime import datetime

GLOBAL_CONTEXT = contexts.GlobalContext()

async def build(context: GLOBAL_CONTEXT):

    client = context.dagger_client

    linux_cmd = ["echo", "using host.docker.internal as test env"]
    if os.getenv("CI"):
        linux_cmd = ["sed", "-i", "s/host.docker.internal/172.17.0.1/g", ".env.test"]

    runner: Container = (
        client.container()
        .from_("summerwind/actions-runner:ubuntu-22.04")
        .exec("apt", "install", "jq", "-y")

    )

    await runner.exit_code()
    return runner


async def publish(context: GLOBAL_CONTEXT, container: Container):

    client = context.dagger_client
    sops: Container = (
        client.container().from_("mozilla/sops:v3-alpine").file("/usr/local/bin/sops")
    )

    maintainers: Container = (
        client.container(platform="linux/amd64")
        .with_unix_socket(
            "/var/run/docker.sock", client.host().unix_socket("/var/run/docker.sock")
        )
        .from_("node:alpine")
        .with_directory("/opt/app", build_dir)
        .with_workdir("/opt/app")
        .with_file("/usr/local/bin/sops", sops)
        .with_default_args(["scripts/start.sh"])
        .publish(tag)
    )
    await maintainers
    return maintainers


if __name__ == "__main__":
    anyio.run(build)
