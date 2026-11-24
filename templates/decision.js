const lab = document.querySelector(".decision-lab");
const cap = lab.querySelector("#default-limit");
const floor = lab.querySelector("#profit-limit");
const reset = lab.querySelector("#reset");
const scenario = lab.querySelector(".lab-result");
const controls = [cap, floor];
const upper = Number(lab.dataset.upper);
const lower = Number(lab.dataset.lower);

function renderDecision() {
  const checks = [cap.valueAsNumber >= upper, floor.valueAsNumber < lower];
  for (const [index, control] of controls.entries()) {
    const gate = control.closest(".gate");
    const [digits, unit] = index === 0 ? [2, "pp"] : [0, "₹/week"];
    const label = control.valueAsNumber.toLocaleString("en-IN", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }) + " " + unit;
    const result = gate.querySelector(".gate-result");
    gate.querySelector(".control-line strong").textContent = label;
    control.closest(".rail").style.setProperty(
      "--threshold", `${100 * control.valueAsNumber / Number(control.max)}%`,
    );
    result.querySelector("strong").textContent = checks[index] ? "PASS" : "FAIL";
    result.dataset.passing = checks[index];
    control.setAttribute("aria-valuetext", label);
  }

  const passes = checks.every(Boolean);
  scenario.dataset.passing = passes;
  scenario.querySelector("#joint-status").textContent = passes ? "Pilot PASS" : "Pilot FAIL";
  scenario.querySelector("#joint-detail").textContent =
    `Default ${checks[0] ? "passes" : "fails"} · Profit ${checks[1] ? "passes" : "fails"}`;
}

for (const control of controls) {
  control.hidden = false;
  control.addEventListener("input", renderDecision);
}

lab.querySelector("#slider-fallback").hidden = true;
reset.hidden = false;
reset.addEventListener("click", () => {
  for (const control of controls) control.value = control.defaultValue;
  renderDecision();
});
renderDecision();
