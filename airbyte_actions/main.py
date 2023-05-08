from clidantic import Parser

actions = Parser(name="actions")
@actions.command(help_message="command 1 help message", config_param_name = "config")
def command1():
    print("Command 1 executed")

@actions.command(help_message="command 2 help message", config_param_name = "config")
def command2():
    print("Command 2 executed")
    
if __name__ == '__main__':
    actions()


from my_application.models import DeveloperPlugin
from clidantic import Parser

class MyPlugin(DeveloperPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = Parser(name="myplugin")

    def build(self):
        # Implementation of the "build" command

    def test(self):
        # Implementation of the "test" command

    def publish(self):
        # Implementation of the "publish" command
