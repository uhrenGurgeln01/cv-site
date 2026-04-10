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
        <article class="project-card" data-reveal>
          <div class="project-card__top">
            <div>
              <p class="project-card__name">${escapeHtml(project.name)}</p>
              <div class="project-card__meta">${escapeHtml(formatProjectMeta(project))}</div>
            </div>
            <a class="project-card__link" href="${escapeHtml(project.url)}" target="_blank" rel="noreferrer">GitHub</a>
          </div>
          <p class="project-card__description">${escapeHtml(project.description)}</p>
          <ul class="project-tags">${tags}</ul>
        </article>
      `;
    })
    .join("");
}

function revealElement(element, delay) {
  element.style.setProperty("--reveal-delay", `${delay}ms`);
  element.classList.add("is-visible");
}

function setupRevealAnimations() {
  const items = Array.from(document.querySelectorAll("[data-reveal]"));

  if (!items.length) {
    return;
  }

  document.body.classList.add("motion-ready");

  if (!("IntersectionObserver" in window)) {
    items.forEach((item, index) => revealElement(item, Math.min(index * 45, 240)));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        const siblings = Array.from(
          entry.target.parentElement?.querySelectorAll("[data-reveal]") || [],
        );
        const index = Math.max(0, siblings.indexOf(entry.target));
        revealElement(entry.target, Math.min(index * 70, 280));
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.16,
      rootMargin: "0px 0px -10% 0px",
    },
  );

  items.forEach((item) => observer.observe(item));
}

function updateScrollProgress() {
  const progressNode = document.getElementById("scroll-progress");

  if (!progressNode) {
    return;
  }

  const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
  const ratio = scrollHeight > 0 ? window.scrollY / scrollHeight : 0;
  progressNode.style.width = `${Math.min(Math.max(ratio, 0), 1) * 100}%`;
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

    setupRevealAnimations();
  } catch (error) {
    if (statusNode) {
      statusNode.textContent =
        "Live-GitHub-Daten konnten nicht geladen werden. Die vorhandenen Karten bleiben sichtbar.";
    }
  }
}

function setCurrentYear() {
  const yearNode = document.getElementById("current-year");

  if (yearNode) {
    yearNode.textContent = String(new Date().getFullYear());
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setCurrentYear();
  updateScrollProgress();
  setupRevealAnimations();
  loadProjects();

  window.addEventListener("scroll", updateScrollProgress, { passive: true });
  window.addEventListener("resize", updateScrollProgress);
});
