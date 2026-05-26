# Flask version of the API

Endpoints:
- `GET /` — health check returning "API is running smoothly!"
- `POST /api/items` — accepts JSON body with `name`, `category`, `quantity`
- `GET /api/items` — returns all items

MongoDB connection: `mongodb://127.0.0.1:27017/internship_dummy_db`

Quick run (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
python app.py
```
