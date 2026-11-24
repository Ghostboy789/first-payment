const theme = document.querySelector("#theme");
theme.value = document.documentElement.dataset.theme || "system";
theme.closest("label").hidden = false;
theme.addEventListener("change", () => {
  document.documentElement.dataset.theme = theme.value;
  try {
    localStorage.setItem("theme", theme.value);
  } catch {
    // The selected theme still applies to this page.
  }
});

const navShell = document.querySelector(".nav-shell");
const menu = navShell.querySelector(".nav-menu");
function compactNav() {
  navShell.classList.toggle("compact", window.scrollY > 32);
}
window.addEventListener("scroll", compactNav, { passive: true });
compactNav();

document.addEventListener("click", (event) => {
  if (menu.open && !menu.contains(event.target)) menu.open = false;
});
menu.addEventListener("keydown", (event) => {
  if (menu.open && event.key === "Escape") {
    menu.open = false;
    menu.querySelector("summary").focus();
  }
});

document.documentElement.dataset.motion = "";
const motion = matchMedia("(prefers-reduced-motion: reduce)");

function settleNumber(number) {
  const start = Number(number.dataset.start);
  const end = Number(number.dataset.count);
  const digits = Number(number.dataset.digits);
  const format = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  const finalText = number.textContent.trim();
  const firstFrame = performance.now();

  function draw(now) {
    const progress = Math.min(1, Math.max(0, (now - firstFrame) / 900));
    if (motion.matches || progress === 1) {
      number.textContent = finalText;
      return;
    }
    const value = start + (end - start) * (1 - (1 - progress) ** 3);
    number.textContent = (value > 0 ? "+" : "") + format.format(value).replace("-", "−");
    requestAnimationFrame(draw);
  }

  draw(firstFrame);
}

if (!motion.matches && "IntersectionObserver" in window) {
  const scenes = [...document.querySelectorAll("[data-reveal]")];
  function reveal(scene) {
    observer.unobserve(scene);
    delete scene.dataset.awaiting;
    if (!motion.matches) scene.querySelectorAll("[data-count]").forEach(settleNumber);
  }
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) reveal(entry.target);
    }
  }, { rootMargin: "0px 0px -6% 0px" });

  for (const scene of scenes) {
    if (scene.getBoundingClientRect().top >= innerHeight) {
      scene.dataset.awaiting = "";
      observer.observe(scene);
      scene.addEventListener("focusin", () => {
        if ("awaiting" in scene.dataset) reveal(scene);
      }, { once: true });
    }
  }

  motion.addEventListener("change", () => {
    if (!motion.matches) return;
    observer.disconnect();
    for (const scene of scenes) delete scene.dataset.awaiting;
  });
}
