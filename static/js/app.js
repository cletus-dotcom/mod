const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const topnav = document.querySelector(".topnav");
if (topnav) {
  const markNav = () => topnav.classList.toggle("is-scrolled", window.scrollY > 8);
  markNav();
  window.addEventListener("scroll", markNav, { passive: true });
}

const hero = document.querySelector(".hero");
if (hero && !reducedMotion) {
  const hold = document.createElement("div");
  hold.className = "hero-hold";
  hero.before(hold);
  hold.appendChild(hero);

  const photo = hero.querySelector(".hero-photo");
  let target = 0;
  let current = 0;
  let frame = 0;

  const paint = () => {
    frame = 0;
    current += (target - current) * 0.08;
    if (Math.abs(target - current) < 0.4) current = target;
    if (photo) photo.style.transform = `translate3d(0, ${(current * 0.38).toFixed(2)}px, 0)`;
    if (current !== target) frame = requestAnimationFrame(paint);
  };

  const measure = () => {
    const range = Math.max(hold.offsetHeight - window.innerHeight, 1);
    const traveled = Math.min(Math.max(window.scrollY - hold.offsetTop, 0), range);
    target = traveled;
    if (!frame) frame = requestAnimationFrame(paint);
  };

  window.addEventListener("scroll", measure, { passive: true });
  window.addEventListener("resize", measure);
  measure();
}

const sidebar = document.getElementById("sidebar");
const navToggle = document.querySelector(".nav-toggle");
const backdrop = document.getElementById("backdrop");
const sidebarClose = document.querySelector(".sidebar-close");

function setMenu(open) {
  if (!sidebar || !navToggle) return;
  sidebar.classList.toggle("is-open", open);
  navToggle.setAttribute("aria-expanded", String(open));
  navToggle.querySelector(".sr-only").textContent = open ? "Close menu" : "Open menu";
  if (backdrop) backdrop.hidden = !open;
  document.body.classList.toggle("menu-open", open);
  if (open) sidebar.querySelector(".side-link")?.focus();
}

if (navToggle && sidebar) {
  navToggle.addEventListener("click", () => setMenu(!sidebar.classList.contains("is-open")));
  sidebarClose?.addEventListener("click", () => {
    setMenu(false);
    navToggle.focus();
  });
  backdrop?.addEventListener("click", () => {
    setMenu(false);
    navToggle.focus();
  });
  sidebar.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 960) setMenu(false);
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && sidebar.classList.contains("is-open")) {
      setMenu(false);
      navToggle.focus();
    }
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 960) setMenu(false);
  });
}

const filters = document.getElementById("filters");
const results = document.getElementById("results");
if (filters && results) {
  let requestId = 0;
  let timer = 0;

  const syncForm = (url) => {
    const params = new URL(url, window.location.origin).searchParams;
    [...filters.elements].forEach((element) => {
      if (!element.name || element.type === "submit") return;
      element.value = params.get(element.name) || "";
    });
  };

  const visit = async (url, push) => {
    const clean = new URL(url, window.location.origin);
    clean.searchParams.delete("partial");
    syncForm(clean);
    if (push) history.pushState({}, "", clean);
    const fetchUrl = new URL(clean);
    fetchUrl.searchParams.set("partial", "1");
    const id = ++requestId;
    results.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(fetchUrl, { headers: { "X-Requested-With": "fetch" } });
      if (!response.ok) throw new Error("Search failed");
      const html = await response.text();
      if (id !== requestId) return;
      results.innerHTML = html;
    } catch (_error) {
      if (id === requestId) window.location.assign(clean);
    } finally {
      if (id === requestId) results.removeAttribute("aria-busy");
    }
  };

  filters.addEventListener("submit", (event) => {
    event.preventDefault();
    const url = new URL(filters.action, window.location.origin);
    const data = new FormData(filters);
    for (const [key, value] of data.entries()) {
      const text = String(value).trim();
      if (text) url.searchParams.set(key, text);
    }
    visit(url, true);
  });

  filters.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", () => filters.requestSubmit());
  });

  const search = filters.querySelector('input[name="q"]');
  search?.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => filters.requestSubmit(), 220);
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest("#results a.js-nav, .filters a.js-nav");
    if (!link) return;
    event.preventDefault();
    visit(link.href, true);
  });

  window.addEventListener("popstate", () => visit(window.location.href, false));

  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
      event.preventDefault();
      search?.focus();
    }
  });
}

const confirmDialog = document.getElementById("confirm-dialog");
document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  const message = form.getAttribute("data-confirm");
  if (!message || form.dataset.confirmed === "1") return;
  event.preventDefault();
  if (!confirmDialog || typeof confirmDialog.showModal !== "function") {
    if (window.confirm(message)) {
      form.dataset.confirmed = "1";
      form.submit();
    }
    return;
  }
  confirmDialog.querySelector("p").textContent = message;
  const onClose = () => {
    confirmDialog.removeEventListener("close", onClose);
    if (confirmDialog.returnValue === "confirm") {
      form.dataset.confirmed = "1";
      form.requestSubmit();
    }
  };
  confirmDialog.addEventListener("close", onClose);
  confirmDialog.showModal();
});
