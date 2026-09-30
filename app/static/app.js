document.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-tab]");
  if (tab) {
    const group = tab.dataset.tabGroup;
    document.querySelectorAll(`[data-tab-group="${group}"]`).forEach((el) => {
      if (el.hasAttribute("data-tab")) {
        el.classList.toggle("active", el === tab);
      } else if (el.hasAttribute("data-tab-panel")) {
        el.classList.toggle("hidden", el.dataset.tabPanel !== tab.dataset.tab);
      }
    });
    return;
  }

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

// Ported from a PHP `time` class's timeAgo() method (see app/timeago.py
// for the Python side and why the original's fixed 4.5-hour offset was
// dropped). Kept in sync with that port bucket-for-bucket.
function timeAgo(isoString) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(isoString).getTime()) / 1000));

  if (seconds <= 60) return seconds === 1 ? "Just now" : `${seconds} secs`;

  const minutes = Math.round(seconds / 60);
  if (seconds < 3600) return minutes === 1 ? "1 min" : `${minutes} mins`;

  const hours = Math.round(seconds / 3600);
  if (seconds < 86400) return hours === 1 ? "1 hour" : `${hours} hours`;

  const days = Math.round(seconds / 86400);
  if (seconds < 604800) return days === 1 ? "1 day" : `${days} days`;

  const weeks = Math.round(seconds / 604800);
  if (seconds < 2600640) return weeks === 1 ? "1 week" : `${weeks} weeks`;

  const months = Math.round(seconds / 2600640);
  if (seconds < 31207680) return months === 1 ? "1 month" : `${months} months`;

  const years = Math.round(seconds / 31207680);
  return years === 1 ? "1 year" : `${years} years`;
}

function refreshTimeAgoElements() {
  document.querySelectorAll("[data-timeago]").forEach((el) => {
    el.textContent = timeAgo(el.dataset.timeago);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  refreshTimeAgoElements();
  setInterval(refreshTimeAgoElements, 30000);
});

document.addEventListener("change", (event) => {
  const input = event.target.closest("[data-file-name-target]");
  if (!input) return;
  const target = document.getElementById(input.dataset.fileNameTarget);
  if (target) target.textContent = input.files.length ? input.files[0].name : "";
});

// --- Create-post modal -----------------------------------------------------

document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-open-modal]");
  if (opener) {
    const dialog = document.getElementById(opener.dataset.openModal);
    if (dialog && !dialog.open) dialog.showModal();
    return;
  }

  const closer = event.target.closest("[data-close-modal]");
  if (closer) {
    closer.closest("dialog")?.close();
    return;
  }

  // A click that lands on the <dialog> itself (not its card) is the backdrop.
  if (event.target instanceof HTMLDialogElement) event.target.close();
});

// --- Drop zone (the native file input is never shown) ----------------------

const showDropzonePreview = (zone, file) => {
  const preview = zone.querySelector("[data-dropzone-preview]");
  const empty = zone.querySelector("[data-dropzone-empty]");
  if (!preview || !empty) return;

  preview.querySelectorAll("img, video").forEach((el) => URL.revokeObjectURL(el.src));
  preview.replaceChildren();

  if (!file) {
    preview.hidden = true;
    empty.hidden = false;
    return;
  }

  const media = document.createElement(file.type.startsWith("video/") ? "video" : "img");
  media.src = URL.createObjectURL(file);
  if (media.tagName === "VIDEO") {
    media.muted = true;
    media.controls = true;
  }
  preview.append(media);
  preview.hidden = false;
  empty.hidden = true;
};

document.addEventListener("click", (event) => {
  const pick = event.target.closest("[data-dropzone-pick]");
  if (!pick) return;
  pick.closest("[data-dropzone]")?.querySelector('input[type="file"]')?.click();
});

document.addEventListener("change", (event) => {
  const zone = event.target.closest("[data-dropzone]");
  if (!zone || event.target.type !== "file") return;
  showDropzonePreview(zone, event.target.files[0]);
});

["dragenter", "dragover"].forEach((type) => {
  document.addEventListener(type, (event) => {
    const zone = event.target.closest?.("[data-dropzone]");
    if (!zone) return;
    event.preventDefault();
    zone.classList.add("is-dragging");
  });
});

document.addEventListener("dragleave", (event) => {
  const zone = event.target.closest?.("[data-dropzone]");
  if (zone && !zone.contains(event.relatedTarget)) zone.classList.remove("is-dragging");
});

document.addEventListener("drop", (event) => {
  const zone = event.target.closest?.("[data-dropzone]");
  if (!zone) return;
  event.preventDefault();
  zone.classList.remove("is-dragging");

  const input = zone.querySelector('input[type="file"]');
  if (!input || !event.dataTransfer.files.length) return;
  input.files = event.dataTransfer.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
});

// Reset the composer whenever the modal closes without posting.
document.querySelectorAll("dialog.modal").forEach((dialog) => {
  dialog.addEventListener("close", () => {
    const form = dialog.querySelector("form");
    const zone = dialog.querySelector("[data-dropzone]");
    if (!form || !zone) return;
    form.reset();
    showDropzonePreview(zone, null);
    const fileName = document.getElementById("composer-file-name");
    if (fileName) fileName.textContent = "";
  });
});

// --- Feed comments -----------------------------------------------------------

document.addEventListener("click", (event) => {
  const trigger = event.target.closest("[data-focus]");
  if (!trigger) return;
  document.getElementById(trigger.dataset.focus)?.querySelector("textarea")?.focus();
});

const syncCommentField = (textarea) => {
  const form = textarea.closest(".feed-comment-form");
  if (!form) return;
  form.classList.toggle("has-text", textarea.value.trim().length > 0);
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight}px`;
};

document.addEventListener("input", (event) => {
  if (event.target.matches(".feed-comment-form textarea")) syncCommentField(event.target);
});

document.addEventListener("keydown", (event) => {
  const textarea = event.target;
  if (!textarea.matches?.(".feed-comment-form textarea")) return;
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  if (textarea.value.trim()) textarea.form.requestSubmit();
});
