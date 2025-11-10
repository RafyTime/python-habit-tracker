from rich import print
from typer import Typer
from src.core.config import settings


app = Typer()


@app.command()
def run():
    print(f'✨ [cyan]Hello from {settings.PROJECT_NAME}![/cyan] 🚀')
    print(f'Version: {settings.PROJECT_VERSION}')
    print(f'Default Message: {settings.DEFAULT_MESSAGE}')


if __name__ == '__main__':
    app()
