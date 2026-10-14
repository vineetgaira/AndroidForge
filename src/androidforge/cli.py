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
   All the methods are to be implemented.
    """
    typer.echo("To be Implemented")


@app.command()
def compatible():
    typer.echo("To be implemented")