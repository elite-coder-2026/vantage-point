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
