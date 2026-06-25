for (const row of document.querySelectorAll(".participant-row")) {
  const summary = row.querySelector("summary");
  const expandShell = row.querySelector(".expand-shell");
  if (!summary) {
    continue;
  }

  summary.addEventListener("click", (event) => {
    if (!row.open || row.classList.contains("is-closing")) {
      return;
    }

    event.preventDefault();
    row.classList.add("is-closing");

    if (!expandShell) {
      row.open = false;
      row.classList.remove("is-closing");
      return;
    }

    const finishClosing = (transitionEvent) => {
      if (
        transitionEvent.target !== expandShell ||
        transitionEvent.propertyName !== "grid-template-rows"
      ) {
        return;
      }
      expandShell.removeEventListener("transitionend", finishClosing);
      row.open = false;
      row.classList.remove("is-closing");
    };

    expandShell.addEventListener("transitionend", finishClosing);
  });
}
