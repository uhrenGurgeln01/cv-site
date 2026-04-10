const profileDataElement = document.getElementById("profile-data");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatProjectMeta(project) {
  const meta = [];

  if (project.language) {
    meta.push(project.language);
  }

  if (typeof project.stars === "number") {
    meta.push(`${project.stars} Sterne`);
  }

  if (project.featured) {
    meta.push("Featured");
  }

  if (project.updated_at) {
    const date = new Date(project.updated_at);
    if (!Number.isNaN(date.getTime())) {
      meta.push(
        `Aktualisiert ${new Intl.DateTimeFormat("de-AT", {
          month: "short",
          year: "numeric",
        }).format(date)}`,
      );
    }
  }

  return meta.join(" · ");
}

function renderProjects(projects) {
  const grid = document.getElementById("projects-grid");

  if (!grid) {
    return;
  }

  grid.innerHTML = projects
    .map((project) => {
      const tags = (project.tech || [])
        .map((tag) => `<li class="project-tag">${escapeHtml(tag)}</li>`)
        .join("");

      return `
        <article class="project-card">
          <div class="project-card__top">
            <p class="project-card__name">${escapeHtml(project.name)}</p>
            <a class="project-card__link" href="${escapeHtml(project.url)}" target="_blank" rel="noreferrer">GitHub</a>
          </div>
          <p class="project-card__description">${escapeHtml(project.description)}</p>
          <div class="project-card__meta">${escapeHtml(formatProjectMeta(project))}</div>
          <ul class="project-tags">${tags}</ul>
        </article>
      `;
    })
    .join("");
}

async function loadProjects() {
  const statusNode = document.getElementById("projects-status");

  try {
    const response = await fetch("/api/projects", {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const payload = await response.json();
    renderProjects(payload.projects || []);

    if (statusNode && payload.status) {
      statusNode.textContent = payload.status;
    }
  } catch (error) {
    if (statusNode) {
      statusNode.textContent =
        "Live-GitHub-Daten konnten nicht geladen werden. Die vorhandenen Karten bleiben sichtbar.";
    }
  }
}

function setupTabs() {
  const tabs = Array.from(document.querySelectorAll("[data-tab-target]"));
  const panels = Array.from(document.querySelectorAll("[data-tab-panel]"));

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tabTarget;

      tabs.forEach((entry) => {
        const isActive = entry === tab;
        entry.classList.toggle("is-active", isActive);
        entry.setAttribute("aria-selected", String(isActive));
      });

      panels.forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.tabPanel === target);
      });
    });
  });
}

function hydrateProfileContext() {
  if (!profileDataElement) {
    return null;
  }

  try {
    return JSON.parse(profileDataElement.textContent);
  } catch (error) {
    return null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  hydrateProfileContext();
  setupTabs();
  loadProjects();
});
