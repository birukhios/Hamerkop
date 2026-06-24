const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".site-nav");
const topbar = document.querySelector(".topbar");
const revealNodes = document.querySelectorAll(".reveal");

const closeNav = () => {
  if (!siteNav || !navToggle) return;
  siteNav.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
};

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = siteNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  siteNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeNav);
  });

  // Close the mobile menu with Escape, and on resize back to desktop.
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeNav();
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 760) closeNav();
  });
}

// Give the sticky header more presence once the page is scrolled.
if (topbar) {
  const onScroll = () => {
    topbar.classList.toggle("is-scrolled", window.scrollY > 8);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
}

// Hero email-capture card — open a pre-filled email (no backend).
const leadForm = document.getElementById("hero-lead-form");
if (leadForm) {
  leadForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const email = leadForm.querySelector("input")?.value.trim() || "";
    const body = encodeURIComponent(
      `Hello Hamerkop team,\n\nI'd like to talk about my systems roadmap.\nReach me at: ${email}`
    );
    window.location.href =
      `mailto:hello@hamerkop.systems?subject=${encodeURIComponent(
        "Consultation request"
      )}&body=${body}`;
  });
}

// Consultation form — compose a pre-filled email (no backend).
const consultForm = document.getElementById("consult-form");
if (consultForm) {
  consultForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const status = document.getElementById("consult-status");
    const get = (n) => (consultForm.elements[n]?.value || "").trim();
    if (!get("name") || !get("email") || !get("message")) {
      if (status) status.textContent = "Please add your name, email and a short brief.";
      return;
    }
    const lines = [
      `Name: ${get("name")}`,
      `Email: ${get("email")}`,
      `Organization: ${get("organization")}`,
      `Role: ${get("role")}`,
      `Sector: ${get("sector")}`,
      `Area of interest: ${get("interest")}`,
      `Timeline: ${get("timeline")}`,
      `Phone: ${get("phone")}`,
      "",
      "Brief:",
      get("message"),
    ];
    const subject = `Consultation request — ${get("organization") || get("name")}`;
    window.location.href =
      `mailto:hello@hamerkop.systems?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(lines.join("\n"))}`;
    if (status) status.textContent = "Opening your email app… if nothing happens, write to hello@hamerkop.systems.";
  });
}

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
