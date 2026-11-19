const lab = document.querySelector(".decision-lab");
const cap = document.querySelector("#default-limit");
const floor = document.querySelector("#profit-limit");
const reset = document.querySelector("#reset");
const controls = [cap, floor];
const thresholds = [Number(lab.dataset.upper), Number(lab.dataset.lower)];

function renderDecision() {
  const checks = [cap.valueAsNumber >= thresholds[0], floor.valueAsNumber < thresholds[1]];
  for (const [index, control] of controls.entries()) {
    const gate = control.closest(".gate");
    const [digits, unit] = index === 0 ? [2, "pp"] : [0, "₹/week"];
    const label = control.valueAsNumber.toLocaleString("en-IN", {
      minimumFractionDigits: digits, maximumFractionDigits: digits,
    }) + " " + unit;
    gate.querySelector(".control-line span:last-child").textContent = label;
    gate.querySelector(".band").style.setProperty(
      "--threshold", `${100 * control.valueAsNumber / Number(control.max)}%`,
    );
    gate.querySelector(".gate-result strong").textContent = checks[index] ? "PASS" : "FAIL";
    gate.dataset.passing = checks[index];
    control.setAttribute("aria-valuetext", label);
  }
  const passes = checks.every(Boolean);
  document.querySelector("#joint-status").textContent = passes ? "Pilot PASS" : "Pilot FAIL";
  document.querySelector("#joint-detail").textContent =
    `Default ${checks[0] ? "passes" : "fails"} · Profit ${checks[1] ? "passes" : "fails"}`;
}

for (const control of controls) {
  control.hidden = false;
  control.closest(".gate").querySelector(".control-line").hidden = false;
  control.addEventListener("input", renderDecision);
}

document.querySelector("#slider-fallback").hidden = true;
reset.hidden = false;
reset.addEventListener("click", () => {
  for (const control of controls) control.value = control.defaultValue;
  renderDecision();
});
renderDecision();
