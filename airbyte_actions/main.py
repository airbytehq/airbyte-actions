import structlog
from aircmd.models import DeveloperPlugin
from clidantic import Parser

logger = structlog.get_logger()

class AirbyteActionsPlugin(DeveloperPlugin):
    actions = Parser(name="actions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "actions"

    @actions.command(help_message="build", config_param_name = "config")
    def build(self):
        logger.info("build")
        # Implementation of the "build" command

    @actions.command(help_message="test", config_param_name = "config")
    def test(self):
        logger.info("test")
        # Implementation of the "test" command

    @actions.command(help_message="publish", config_param_name = "config")
    def publish(self):
        logger.info("publish")
        # Implementation of the "publish" command

actions_plugin = AirbyteActionsPlugin(name="myplugin", plugin_type="application")
