from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from db import get_db
from scrapers import scrape_universal

app = FastAPI()
templates = Jinja2Templates(directory=".")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    conn = get_db()
    items = conn.execute(
        "SELECT id, store, title, price, url FROM cart ORDER BY id DESC"
    ).fetchall()
    total = sum(item[3] for item in items) if items else 0

    return templates.TemplateResponse(
        "index.html", {"request": request, "items": items, "total": total}
    )


@app.post("/add")
def add_item(request: Request, url: str = Form(...)):
    try:
        title, price = scrape_universal(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store = urlparse(url).netloc
    conn = get_db()
    conn.execute(
        "INSERT INTO cart (store, title, price, url) VALUES (?, ?, ?, ?)",
        (store, title, price, url),
    )
    conn.commit()

    return RedirectResponse("/", status_code=303)


@app.get("/delete/{item_id}")
def delete_item(item_id: int):
    conn = get_db()
    conn.execute("DELETE FROM cart WHERE id = ?", (item_id,))
    conn.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health_check():
    return {"status": "ok"}
