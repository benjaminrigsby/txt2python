from fastapi import FastAPI, Request, Form, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv, io, json
from typing import List, Dict, Any

PREFIX = "/txt2python"

app = FastAPI(title="txt2python")

# static files under prefix
app.mount(f"{PREFIX}/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def parse_csv(text: str, has_header: bool = True) -> Dict[str, Any]:
    content = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    reader = csv.reader(io.StringIO(content), skipinitialspace=True)
    rows: List[List[str]] = [list(map(lambda s: s.strip(), r)) for r in reader if any(c.strip() for c in r)]
    if not rows:
        return {"headers": [], "rows": []}
    if has_header:
        headers = rows[0]; data_rows = rows[1:]
        width = max(len(headers), *(len(r) for r in data_rows)) if data_rows else len(headers)
        headers = headers + [f"col_{i+1}" for i in range(len(headers), width)]
        fixed_rows = [r + [""] * (width - len(r)) for r in data_rows]
        return {"headers": headers, "rows": fixed_rows}
    else:
        width = max(len(r) for r in rows)
        headers = [f"col_{i+1}" for i in range(width)]
        fixed_rows = [r + [""] * (width - len(r)) for r in rows]
        return {"headers": headers, "rows": fixed_rows}

def to_list_of_dicts(headers: List[str], rows: List[List[str]]) -> List[Dict[str, Any]]:
    return [dict(zip(headers, r)) for r in rows]

def generate_code(headers: List[str], rows: List[List[str]], mode: str) -> str:
    lod = to_list_of_dicts(headers, rows)
    if mode == "listdict":
        return "data = " + json.dumps(lod, indent=2, ensure_ascii=False)
    if mode == "dict":
        if not headers: return "data = {}  # No data"
        key = headers[0]
        body = {str(r.get(key, "")): {k: v for k, v in r.items() if k != key} for r in lod}
        return "data = " + json.dumps(body, indent=2, ensure_ascii=False)
    literal = json.dumps(lod, indent=2, ensure_ascii=False)
    return (
        "import pandas as pd\n"
        f"rows = {literal}\n"
        "df = pd.DataFrame(rows)\n"
        "print(df)\n"
    )

router = APIRouter(prefix=PREFIX)

@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "input_text": "",
            "output_code": None,
            "mode": "pandas",
            "has_header": True,
            "sample": "Name, Age, City\nAlice, 31, Tampa\nBob, 29, Austin\nCharlie, 35, Denver",
        },
    )

@router.post("/convert", response_class=HTMLResponse, name="convert")
async def convert(
    request: Request,
    input_text: str = Form(...),
    mode: str = Form("pandas"),
    has_header: bool = Form(False),
):
    parsed = parse_csv(input_text, has_header=has_header)
    code = generate_code(parsed["headers"], parsed["rows"], mode)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "input_text": input_text,
            "output_code": code,
            "mode": mode,
            "has_header": has_header,
            "sample": "Name, Age, City\nAlice, 31, Tampa\nBob, 29, Austin\nCharlie, 35, Denver",
        },
    )

# Root health endpoint for probes
@app.get("/", response_class=HTMLResponse)
async def health_root():
    return "ok"

app.include_router(router)
