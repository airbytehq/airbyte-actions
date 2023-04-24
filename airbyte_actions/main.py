import click


@click.group()
def actions():
    pass

@actions.command()
def command1():
    click.echo("Command 1 executed")

if __name__ == '__main__':
    actions()  
