const theme = document.querySelector("#theme");

try {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") theme.value = saved;
} catch {
  // Local previews may have storage disabled.
}

document.documentElement.dataset.theme = theme.value;
theme.closest("label").hidden = false;
theme.addEventListener("change", () => {
  document.documentElement.dataset.theme = theme.value;
  try {
    localStorage.setItem("theme", theme.value);
  } catch {
    // The current page still changes theme.
  }
});
