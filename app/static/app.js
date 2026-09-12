document.addEventListener("click", (event) => {
  const trigger = event.target.closest("[data-toggle]");

  if (trigger) {
    const target = document.getElementById(trigger.dataset.toggle);
    if (!target) return;

    const wasHidden = target.classList.contains("hidden");

    document.querySelectorAll("[data-toggle-target]").forEach((el) => {
      if (el !== target) el.classList.add("hidden");
    });

    target.classList.toggle("hidden", !wasHidden);
    if (wasHidden) {
      const textarea = target.querySelector("textarea");
      if (textarea) textarea.focus();
    }
    return;
  }

  document.querySelectorAll("[data-toggle-target]:not(.hidden)").forEach((target) => {
    if (!target.contains(event.target)) target.classList.add("hidden");
  });
});
