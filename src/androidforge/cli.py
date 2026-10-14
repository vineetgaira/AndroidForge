import typer

app = typer.Typer()


@app.callback()
def callback():
    """
    Welcome to android forge
    """


@app.command()
def devices():
    """
    This tells about devices that are connected
    """
    typer.echo("To be Implemented")


@app.command()
def inspect():
    """
    Gives details about the device
    """
    typer.echo("To be implemented")

@app.command()
def capabilities():
    """
    Gives us device capabilities
    """
    typer.echo("To be implemented")