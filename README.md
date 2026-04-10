# CV Website

Schlanke, moderne CV-Website in Python ohne externe Abhaengigkeiten.

## Start

```bash
cd /Users/denishenic/Downloads/thesis-agent-sandbox/cv-site
python3 server.py
```

Danach ist die Seite unter `http://127.0.0.1:8080` erreichbar.

## Anpassen

- Profilinhalte liegen in `profile_data.py`
- Layout und Farben liegen in `static/styles.css`
- Reiter-Logik und GitHub-Projekt-Refresh liegen in `static/app.js`

## GitHub-Projekte

Die Projektliste wird ueber die GitHub-API fuer `uhrenGurgeln01` geladen.
Wenn GitHub nicht erreichbar ist, wird automatisch auf kuratierte Projekte zurueckgefallen.
