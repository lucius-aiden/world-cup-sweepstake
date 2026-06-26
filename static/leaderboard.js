for (const row of document.querySelectorAll(".participant-row")) {
  const summary = row.querySelector("summary");
  const expandShell = row.querySelector(".expand-shell");
  if (!summary || !expandShell) {
    continue;
  }

  let isAnimating = false;

  const finishAnimation = () => {
    isAnimating = false;
    row.classList.remove("is-opening", "is-closing");
  };

  const animateOpen = () => {
    isAnimating = true;
    row.open = true;
    row.classList.add("is-opening");
    expandShell.style.height = "0px";

    requestAnimationFrame(() => {
      expandShell.style.height = `${expandShell.scrollHeight}px`;
    });
  };

  const animateClose = () => {
    isAnimating = true;
    row.classList.add("is-closing");
    expandShell.style.height = `${expandShell.scrollHeight}px`;
    expandShell.getBoundingClientRect();

    requestAnimationFrame(() => {
      expandShell.style.height = "0px";
    });
  };

  expandShell.addEventListener("transitionend", (event) => {
    if (event.target !== expandShell || event.propertyName !== "height") {
      return;
    }

    if (row.classList.contains("is-opening")) {
      expandShell.style.height = "auto";
      finishAnimation();
      return;
    }

    if (row.classList.contains("is-closing")) {
      row.open = false;
      expandShell.style.height = "";
      finishAnimation();
    }
  });

  summary.addEventListener("click", (event) => {
    event.preventDefault();
    if (isAnimating) {
      return;
    }

    if (row.open) {
      animateClose();
      return;
    }

    animateOpen();
  });
}
