from rich import print
from typer import Typer

from src.core.config import app_settings

app = Typer()


@app.command()
def run():
    print(
        f'✨ [cyan]Hello from {app_settings.PROJECT_NAME}! v{app_settings.PROJECT_VERSION}[/cyan] 🚀'
    )


if __name__ == '__main__':
    app()
