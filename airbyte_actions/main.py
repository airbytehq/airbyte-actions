import sys

import anyio
import click
import dagger


async def build():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        runner = (
            client.container(platform = dagger.Platform("linux/amd64"))
            # pull container
            .from_("summerwind/actions-runner:v2.303.0-ubuntu-20.04-3417c5a@sha256:202c64d20e5a35511eb541df7e6d72fd7e415d712c669a4783f48bd39c70fc68")

            # will need a cachebuster here when running in CI because we always want to check for updates
            .with_exec(["sudo apt-get update"])
            .with_exec("sudo apt-get upgrade -y")
            # install apt dependencies
            .with_exec(['''sudo apt-get install -y jq libasound2 libgbm-dev libgconf-2-4 libgtk-3-0 libnotify-dev libnss3 libxss1 libxtst6 xauth xvfb postgresql postgresql-contrib unzip'''])
            # install kubectl
            .with_exec(["sudo curl -LO 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl'"])
            .with_exec(["sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl"])
            # install helm
            .with_exec(["curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null"])
            .with_exec(["sudo apt-get install apt-transport-https -y"])
            .with_exec(["echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main' | sudo tee /etc/apt/sources.list.d/helm.list > /dev/null"])
            .with_exec(["sudo apt-get update"])
            .with_exec(["sudo apt-get install helm -y"])
            # install aws cli
            .with_exec(["sudo curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"])
            .with_exec(["sudo unzip -q awscliv2.zip"])
            .with_exec(["sudo ./aws/install"])
        )

        # execute
        await runner.stdout()
        await runner.publish("hub.docker.com/airbyte/actions-runner:latest")
        return runner



class RunnerBuild(click.Command):
    def __init__(self, **kwargs):
        super().__init__(
            "build",
            callback=self.command1_callback,
            help="Build an Airbyte Actions runner image",
            **kwargs
        )

    def command1_callback(self):
        runner_image=anyio.run(build)
        anyio.run(publish, runner_image)

    def invoke(self, ctx):
        click.echo("Build command received context: {}".format(ctx.obj))
        super().invoke(ctx)


@click.group(name='actions')
def actions():
    """Airbyte actions plugin."""
    pass

@actions.group('runner')
def actions_runner():
    pass


actions_runner.add_command(RunnerBuild())

def register_plugin():
    print("Registering airbyte_actions plugin")
    return actions
