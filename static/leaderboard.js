const CLOSE_DURATION_MS = 320;

for (const row of document.querySelectorAll(".participant-row")) {
  const summary = row.querySelector("summary");
  if (!summary) {
    continue;
  }

  summary.addEventListener("click", (event) => {
    if (!row.open || row.classList.contains("is-closing")) {
      return;
    }

    event.preventDefault();
    row.classList.add("is-closing");

    window.setTimeout(() => {
      row.open = false;
      row.classList.remove("is-closing");
    }, CLOSE_DURATION_MS);
  });
}
