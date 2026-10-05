const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".site-nav");
const topbar = document.querySelector(".topbar");
const revealNodes = document.querySelectorAll(".reveal");
const subToggles = document.querySelectorAll(".nav-sub-toggle");

const closeMenus = (except) => {
  subToggles.forEach((button) => {
    if (button === except) return;
    button.setAttribute("aria-expanded", "false");
    button.parentElement.classList.remove("is-open");
  });
};

const closeNav = () => {
  closeMenus();
  if (!siteNav || !navToggle) return;
  siteNav.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
};

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = siteNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
    if (!isOpen) closeMenus();
  });

  siteNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeNav);
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 1180) closeNav();
  });
}

// Dropdown menus: the chevron button opens a submenu (hover also opens it on desktop).
subToggles.forEach((button) => {
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    const open = button.getAttribute("aria-expanded") !== "true";
    closeMenus(button);
    button.setAttribute("aria-expanded", String(open));
    button.parentElement.classList.toggle("is-open", open);
  });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".nav-item")) closeMenus();
});

// Escape closes an open submenu first, then the mobile menu.
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const open = document.querySelector(".nav-item.is-open .nav-sub-toggle");
  if (open) {
    closeMenus();
    open.focus();
  } else if (siteNav?.classList.contains("is-open")) {
    closeNav();
    navToggle.focus();
  }
});

// Give the sticky header more presence once the page is scrolled.
if (topbar) {
  const onScroll = () => {
    topbar.classList.toggle("is-scrolled", window.scrollY > 8);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
}

// Consultation form: pre-fill from the link, validate, then send.
// Sends to data-endpoint (a form service) when configured, otherwise opens the visitor's email app.
const consultForm = document.getElementById("consult-form");
if (consultForm) {
  const field = (name) => consultForm.elements[name];
  const value = (name) => (field(name)?.value || "").trim();
  const status = document.getElementById("consult-status");
  const inbox = consultForm.dataset.email;
  const routes = JSON.parse(consultForm.dataset.routes || "{}");

  // Pre-select options passed by "Request a Demo" / "Request a Consultation" links.
  const params = new URLSearchParams(window.location.search);
  const preselect = (name) => {
    const wanted = params.get(name);
    const select = field(name);
    if (!wanted || !select) return;
    const option = [...select.options].find((o) => (o.value || o.text) === wanted);
    if (option) select.value = option.value || option.text;
  };
  ["type", "interest", "industry"].forEach(preselect);
  const product = params.get("product");
  if (product) {
    field("product").value = product;
    const context = document.getElementById("form-context");
    context.textContent = `${value("type") === "demo" ? "Demo request" : "Enquiry"} for ${product}`;
    context.hidden = false;
  }
  const title = document.getElementById("form-title");
  const syncTitle = () => {
    title.textContent = value("type") === "demo" ? "Request a Demo" : "Request a Consultation";
  };
  syncTitle();
  field("type").addEventListener("change", syncTitle);

  const rules = {
    name: () => (value("name") ? "" : "Please enter your full name."),
    email: () =>
      !value("email")
        ? "Please enter your work email."
        : /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value("email"))
          ? ""
          : "Please enter a valid email address, e.g. name@organization.com.",
    phone: () =>
      !value("phone") || /^[+\d][\d\s()-]{6,}$/.test(value("phone"))
        ? ""
        : "Please enter a valid phone number, e.g. +251 911 000 000.",
    message: () => (value("message") ? "" : "Please describe the project or requirement."),
  };

  const check = (name) => {
    const message = rules[name]();
    field(name).setAttribute("aria-invalid", String(Boolean(message)));
    document.getElementById(`${name}-error`).textContent = message;
    return !message;
  };

  // Re-check a field as soon as the visitor corrects it.
  Object.keys(rules).forEach((name) => {
    field(name).addEventListener("input", () => {
      if (field(name).getAttribute("aria-invalid") === "true") check(name);
    });
  });

  const showSuccess = (text) => {
    consultForm.hidden = true;
    const success = document.getElementById("consult-success");
    if (text) document.getElementById("consult-success-text").textContent = text;
    success.hidden = false;
    success.focus();
  };

  consultForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const invalid = Object.keys(rules).filter((name) => !check(name));
    if (invalid.length) {
      status.textContent = "Please correct the highlighted fields.";
      field(invalid[0]).focus();
      return;
    }
    status.textContent = "";

    const kind = value("type") === "demo" ? "Demo request" : "Consultation request";
    const area = value("interest");
    const subject = `[${area || "General"}] ${kind}${value("product") ? ` — ${value("product")}` : ""} — ${value("organization") || value("name")}`;
    const to = routes[area] || routes.default || inbox;
    const details = {
      "Request type": kind,
      Product: value("product"),
      Name: value("name"),
      Email: value("email"),
      Organization: value("organization"),
      Role: value("role"),
      Phone: value("phone"),
      Industry: value("industry"),
      "Area of interest": area,
      "Project / requirement summary": value("message"),
    };

    const endpoint = consultForm.dataset.endpoint;
    if (endpoint) {
      const button = consultForm.querySelector("button[type=submit]");
      button.disabled = true;
      status.textContent = "Sending…";
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ _subject: subject, _replyto: value("email"), route_to: to, ...details }),
        });
        if (!response.ok) throw new Error(String(response.status));
        showSuccess();
      } catch {
        status.textContent = `Sorry, the request could not be sent. Please try again or email ${inbox}.`;
        button.disabled = false;
      }
      return;
    }

    const body = Object.entries(details)
      .filter(([, v]) => v)
      .map(([k, v]) => (k === "Project / requirement summary" ? `\n${k}:\n${v}` : `${k}: ${v}`))
      .join("\n");
    window.location.href = `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    showSuccess(
      `Your email app should now open with the request ready to send to ${to}. If it did not open, please email us directly at ${inbox}.`
    );
  });
}

// Photo lightbox for the Odoo partnership gallery.
const galleryItems = document.querySelectorAll("[data-lightbox]");
if (galleryItems.length && typeof HTMLDialogElement === "function") {
  const dialog = document.createElement("dialog");
  dialog.className = "lightbox";
  dialog.innerHTML =
    '<button type="button" class="lightbox-close" aria-label="Close">&times;</button><img alt="" /><p></p>';
  document.body.appendChild(dialog);
  const image = dialog.querySelector("img");
  const caption = dialog.querySelector("p");

  dialog.querySelector(".lightbox-close").addEventListener("click", () => dialog.close());
  // Clicking the backdrop (outside the content) closes it too.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  galleryItems.forEach((item) => {
    item.addEventListener("click", () => {
      const source = item.querySelector("img");
      image.src = source.src;
      image.alt = source.alt;
      caption.textContent = item.dataset.caption || "";
      dialog.showModal();
    });
  });
}

// Light/dark theme toggle, remembered per visitor.
const themeToggle = document.querySelector(".theme-toggle");
if (themeToggle) {
  const root = document.documentElement;
  const sync = () => {
    const dark = root.dataset.theme === "dark";
    themeToggle.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#15120d" : "#f5efe4");
  };
  sync();
  themeToggle.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      /* storage unavailable: the choice lasts for this page only */
    }
    sync();
  });
}

// Product showcase: hovering or focusing a row swaps the photo.
document.querySelectorAll(".showcase").forEach((showcase) => {
  const media = showcase.querySelector(".showcase-media");
  const image = media.querySelector("img");
  const rows = showcase.querySelectorAll(".showcase-row");
  const activate = (row) => {
    if (row.classList.contains("is-active")) return;
    rows.forEach((r) => r.classList.toggle("is-active", r === row));
    media.classList.add("is-swapping");
    const next = new Image();
    next.onload = next.onerror = () => {
      image.src = row.dataset.image;
      media.classList.remove("is-swapping");
    };
    next.src = row.dataset.image;
  };
  rows.forEach((row) => {
    row.addEventListener("mouseenter", () => activate(row));
    row.addEventListener("focus", () => activate(row));
  });
});

// Horizontal scrollers (industries): previous/next buttons.
document.querySelectorAll("[data-scroller]").forEach((scroller) => {
  const track = scroller.querySelector(".scroller-track");
  const buttons = scroller.querySelectorAll("[data-scroll]");
  const update = () => {
    const max = track.scrollWidth - track.clientWidth - 2;
    buttons[0].disabled = track.scrollLeft <= 2;
    buttons[1].disabled = track.scrollLeft >= max;
  };
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const card = track.firstElementChild;
      const step = card ? card.getBoundingClientRect().width + 18 : track.clientWidth;
      track.scrollBy({ left: Number(button.dataset.scroll) * step, behavior: "smooth" });
    });
  });
  track.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
});

// ---------------------------------------------------------------- motion library
// Opt-in effects used by the design directions. Everything is skipped when the
// visitor prefers reduced motion, leaving the content in its final state.
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const clamp01 = (v) => Math.min(1, Math.max(0, v));

// Wrap each word (and optionally each character) in spans, keeping inline markup such as <em>.
const splitText = (el, chars) => {
  const units = [];
  const walk = (node) => {
    [...node.childNodes].forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) {
        const frag = document.createDocumentFragment();
        child.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) {
            frag.append(" ");
            return;
          }
          const word = document.createElement("span");
          word.className = "w";
          if (chars) {
            [...part].forEach((c) => {
              const ch = document.createElement("span");
              ch.className = "c";
              ch.textContent = c;
              word.append(ch);
              units.push(ch);
            });
          } else {
            word.textContent = part;
            units.push(word);
          }
          frag.append(word);
        });
        child.replaceWith(frag);
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        walk(child);
      }
    });
  };
  walk(el);
  return units;
};

const onVisible = (el, fn, threshold = 0.2) => {
  if (!("IntersectionObserver" in window)) return fn();
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        fn();
        io.disconnect();
      }
    });
  }, { threshold });
  io.observe(el);
};

if (!reduceMotion) {
  document.documentElement.classList.add("motion");

  // Words blur and rise into place, one after another.
  document.querySelectorAll('[data-anim="blur-in"]').forEach((el) => {
    splitText(el, false).forEach((w, i) => w.style.setProperty("--i", i));
    onVisible(el, () => el.classList.add("is-in"), 0.1);
  });

  // Children appear one after another.
  document.querySelectorAll("[data-stagger]").forEach((el) => {
    [...el.children].forEach((child, i) => child.style.setProperty("--i", i));
    onVisible(el, () => el.classList.add("is-in"), 0.15);
  });

  // Scroll-scrubbed text: words fade in (data-scrub="fade") or characters un-blur (data-scrub="blur").
  const scrubs = [...document.querySelectorAll("[data-scrub]")].map((el) => ({
    el,
    mode: el.dataset.scrub,
    units: splitText(el, el.dataset.scrub === "blur"),
  }));

  // Cards that stack while scrolling: earlier cards shrink back as the next one arrives.
  const stacks = [...document.querySelectorAll(".stack")].map((s) => [...s.querySelectorAll(".stack-card")]);

  // Gentle parallax for hero images.
  const parallax = [...document.querySelectorAll("[data-parallax]")];

  let ticking = false;
  const frame = () => {
    ticking = false;
    const vh = window.innerHeight;
    scrubs.forEach(({ el, mode, units }) => {
      const r = el.getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) return;
      const progress = clamp01((vh * 0.88 - r.top) / (r.height + vh * 0.42));
      const n = units.length;
      units.forEach((u, i) => {
        const v = clamp01((progress * (n + 6) - i) / 6);
        if (mode === "blur") {
          u.style.filter = v >= 1 ? "none" : `blur(${((1 - v) * 7).toFixed(2)}px)`;
          u.style.opacity = (0.35 + v * 0.65).toFixed(3);
        } else {
          u.style.opacity = (0.12 + v * 0.88).toFixed(3);
        }
      });
    });
    stacks.forEach((cards) => {
      cards.forEach((card, i) => {
        const next = cards[i + 1];
        if (!next) return;
        const gap = next.getBoundingClientRect().top - card.getBoundingClientRect().top;
        const p = clamp01(1 - gap / card.offsetHeight);
        card.style.transform = `scale(${(1 - p * 0.08).toFixed(4)})`;
        card.style.setProperty("--dim", (p * 0.55).toFixed(3));
      });
    });
    parallax.forEach((el) => {
      const r = el.parentElement.getBoundingClientRect();
      if (r.bottom < 0 || r.top > vh) return;
      el.style.transform = `translate3d(0, ${(-r.top * Number(el.dataset.parallax || 0.2)).toFixed(1)}px, 0) scale(1.08)`;
    });
  };
  const request = () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(frame);
    }
  };
  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", request);
  frame();
}

// Numbers count up when they come into view.
document.querySelectorAll("[data-count]").forEach((el) => {
  const target = Number(el.dataset.count);
  if (reduceMotion || !target) return;
  el.textContent = "0";
  onVisible(el, () => {
    const start = performance.now();
    const step = (now) => {
      const t = clamp01((now - start) / 1400);
      el.textContent = String(Math.round(target * (1 - Math.pow(1 - t, 3))));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, 0.6);
});

// Tabs (Serene "one platform" section).
document.querySelectorAll("[data-tabs]").forEach((tabs) => {
  const buttons = [...tabs.querySelectorAll('[role="tab"]')];
  const select = (button) => {
    buttons.forEach((b) => {
      const on = b === button;
      b.setAttribute("aria-selected", String(on));
      b.tabIndex = on ? 0 : -1;
      document.getElementById(b.getAttribute("aria-controls")).hidden = !on;
    });
  };
  buttons.forEach((button, i) => {
    button.addEventListener("click", () => select(button));
    button.addEventListener("keydown", (event) => {
      const dir = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      if (!dir) return;
      const next = buttons[(i + dir + buttons.length) % buttons.length];
      next.focus();
      select(next);
    });
  });
});

// Reveal-on-scroll, with graceful fallbacks.
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;

const revealAll = () => {
  revealNodes.forEach((node) => node.classList.add("is-visible"));
};

if (prefersReducedMotion || !("IntersectionObserver" in window)) {
  revealAll();
} else {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.15 }
  );

  revealNodes.forEach((node) => observer.observe(node));
}
