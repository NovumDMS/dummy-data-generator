# Setup Jinja2 templates
from pathlib import Path
from fastapi.templating import Jinja2Templates


templates_path = Path(__file__).parent / "templates"
if templates_path.exists():
    templates = Jinja2Templates(directory=str(templates_path))