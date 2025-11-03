from rich import print
from typer import Typer

app = Typer()


@app.command()
def run():
    print('✨ [cyan]Hello from python-habit-tracker![/cyan] 🚀')


if __name__ == '__main__':
    app()
