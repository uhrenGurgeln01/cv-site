from __future__ import annotations

import json
import mimetypes
import os
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from profile_data import CURATED_PROJECTS, PROFILE


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"
HOST = os.environ.get("CV_HOST", "127.0.0.1")
PORT = int(os.environ.get("CV_PORT", "8080"))


def render_focus_points() -> str:
    return "".join(
        f'<span class="hero-pill">{escape(point)}</span>'
        for point in PROFILE["focus_points"]
    )


def render_highlights() -> str:
    blocks = []
    for item in PROFILE["highlights"]:
        blocks.append(
            """
            <article class="highlight-card" data-reveal>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
            """.format(
                title=escape(item["title"]),
                text=escape(item["text"]),
            ).strip()
        )
    return "".join(blocks)


def render_life_path() -> str:
    items = []
    for position, step in enumerate(PROFILE["life_path"], start=1):
        items.append(
            """
            <article class="timeline-item" data-reveal>
              <div class="timeline-item__marker">{position:02d}</div>
              <div class="timeline-item__content">
                <p class="timeline-item__phase">{phase}</p>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </article>
            """.format(
                position=position,
                phase=escape(step["phase"]),
                title=escape(step["title"]),
                text=escape(step["text"]),
            ).strip()
        )
    return "".join(items)


def render_skills() -> str:
    groups = []
    for group in PROFILE["skills"]:
        items = "".join(
            f'<li class="skill-chip">{escape(skill)}</li>' for skill in group["items"]
        )
        groups.append(
            """
            <section class="skill-group" data-reveal>
              <div class="skill-group__header">
                <p>{group_name}</p>
              </div>
              <ul class="skill-list">{items}</ul>
            </section>
            """.format(
                group_name=escape(group["group"]),
                items=items,
            ).strip()
        )
    return "".join(groups)


def render_contact_items() -> str:
    rows = []
    for item in PROFILE["contact_items"]:
        value = escape(item["value"])
        if item.get("href"):
            value_html = (
                f'<a class="detail-row__value detail-row__value--link" '
                f'href="{escape(item["href"])}" target="_blank" rel="noreferrer">{value}</a>'
            )
        else:
            value_html = f'<span class="detail-row__value">{value}</span>'

        rows.append(
            """
            <article class="detail-row" data-reveal>
              <p class="detail-row__label">{label}</p>
              {value_html}
            </article>
            """.format(
                label=escape(item["label"]),
                value_html=value_html,
            ).strip()
        )
    return "".join(rows)


def render_imprint_items() -> str:
    rows = []
    for item in PROFILE["imprint_items"]:
        rows.append(
            """
            <article class="detail-row" data-reveal>
              <p class="detail-row__label">{label}</p>
              <span class="detail-row__value">{value}</span>
            </article>
            """.format(
                label=escape(item["label"]),
                value=escape(item["value"]),
            ).strip()
        )
    return "".join(rows)


def merge_project_data(projects: list[dict]) -> list[dict]:
    merged: list[dict] = []
    curated_by_name = {item["name"].lower(): item for item in CURATED_PROJECTS}

    for curated in CURATED_PROJECTS:
        merged.append(curated.copy())

    for project in projects:
        name_key = project["name"].lower()
        if name_key in curated_by_name:
            curated = curated_by_name[name_key].copy()
            curated.update(
                {
                    "description": project["description"] or curated["description"],
                    "stars": project["stars"],
                    "updated_at": project["updated_at"],
                    "language": project["language"] or curated["language"],
                    "url": project["url"],
                    "tech": project["tech"] or curated["tech"],
                }
            )
            index = next(
                (
                    position
                    for position, existing in enumerate(merged)
                    if existing["name"].lower() == name_key
                ),
                None,
            )
            if index is not None:
                merged[index] = curated
            continue

        merged.append(project)

    return merged[:6]


def fetch_github_projects() -> list[dict]:
    username = PROFILE["github_username"]
    endpoint = (
        f"https://api.github.com/users/{username}/repos"
        "?sort=updated&per_page=6&type=owner"
    )
    request = Request(
        endpoint,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{username}-cv-site",
        },
    )

    with urlopen(request, timeout=4) as response:
        payload = json.load(response)

    if not isinstance(payload, list):
        raise ValueError("GitHub response did not return a repository list.")

    projects: list[dict] = []
    for repo in payload:
        if repo.get("fork"):
            continue

        tech = []
        if repo.get("language"):
            tech.append(repo["language"])
        if repo.get("visibility"):
            tech.append(repo["visibility"])

        projects.append(
            {
                "name": repo.get("name", "Unbenanntes Repository"),
                "description": repo.get("description") or "Kurze Projektbeschreibung folgt.",
                "url": repo.get("html_url") or PROFILE["github_url"],
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "updated_at": repo.get("pushed_at"),
                "tech": tech,
                "featured": False,
            }
        )

    return merge_project_data(projects)


def get_projects_with_fallback() -> tuple[list[dict], str]:
    try:
        projects = fetch_github_projects()
        return projects, "Live aus GitHub geladen."
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return CURATED_PROJECTS, "GitHub-Daten aktuell nicht erreichbar. Kuratierte Projekte werden angezeigt."


def render_projects(projects: list[dict]) -> str:
    cards = []
    for project in projects:
        tags = "".join(
            f'<li class="project-tag">{escape(tag)}</li>' for tag in project.get("tech", [])
        )
        meta = []
        if project.get("language"):
            meta.append(project["language"])
        if project.get("stars") is not None:
            meta.append(f'{project["stars"]} Sterne')
        if project.get("featured"):
            meta.append("Featured")

        cards.append(
            """
            <article class="project-card" data-reveal>
              <div class="project-card__top">
                <div>
                  <p class="project-card__name">{name}</p>
                  <div class="project-card__meta">{meta}</div>
                </div>
                <a class="project-card__link" href="{url}" target="_blank" rel="noreferrer">GitHub</a>
              </div>
              <p class="project-card__description">{description}</p>
              <ul class="project-tags">{tags}</ul>
            </article>
            """.format(
                name=escape(project["name"]),
                url=escape(project["url"]),
                description=escape(project["description"]),
                meta=" · ".join(escape(item) for item in meta),
                tags=tags,
            ).strip()
        )
    return "".join(cards)


def render_index() -> bytes:
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))

    html = template.safe_substitute(
        page_title=escape(f'{PROFILE["name"]} | CV Website'),
        meta_description=escape(PROFILE["summary"]),
        hero_name=escape(PROFILE["name"]),
        hero_headline=escape(PROFILE["headline"]),
        hero_summary=escape(PROFILE["summary"]),
        github_url=PROFILE["github_url"],
        github_handle=escape(PROFILE["github_username"]),
        location=escape(PROFILE["location"]),
        availability=escape(PROFILE["availability"]),
        profile_image_src=escape(PROFILE["profile_image"]["src"]),
        profile_image_alt=escape(PROFILE["profile_image"]["alt"]),
        profile_image_caption=escape(PROFILE["profile_image"]["caption"]),
        focus_points_html=render_focus_points(),
        highlights_html=render_highlights(),
        life_path_html=render_life_path(),
        skills_html=render_skills(),
        projects_html=render_projects(CURATED_PROJECTS),
        projects_status="Kuratierter Projekt-Auszug. Live-Daten werden im Hintergrund nachgeladen.",
        contact_html=render_contact_items(),
        imprint_html=render_imprint_items(),
        imprint_note=escape(PROFILE["imprint_note"]),
    )
    return html.encode("utf-8")


class CVRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed_url = urlparse(self.path)
        route = parsed_url.path

        if route in {"/", "/index.html"}:
            self.respond(render_index(), "text/html; charset=utf-8")
            return

        if route == "/api/profile":
            self.respond_json(PROFILE)
            return

        if route == "/api/projects":
            projects, status = get_projects_with_fallback()
            self.respond_json({"projects": projects, "status": status})
            return

        if route.startswith("/static/"):
            relative_path = route.removeprefix("/static/")
            file_path = STATIC_DIR / relative_path
            self.serve_static(file_path)
            return

        if route == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Pfad nicht gefunden.")

    def serve_static(self, file_path: Path) -> None:
        try:
            resolved = file_path.resolve(strict=True)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "Datei nicht gefunden.")
            return

        if STATIC_DIR not in resolved.parents:
            self.send_error(HTTPStatus.FORBIDDEN, "Zugriff verweigert.")
            return

        mime_type, _ = mimetypes.guess_type(resolved.name)
        self.respond(resolved.read_bytes(), mime_type or "application/octet-stream")

    def respond(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.respond(body, "application/json; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        return


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), CVRequestHandler)
    print(f"CV-Website laeuft auf http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
