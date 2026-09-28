

document.addEventListener("DOMContentLoaded", () => {
  const widget = document.getElementById("scrollWidget");
  const btn = document.getElementById("backToTop");
  const progressPath = document.getElementById("progressPath");
  if (!widget || !btn || !progressPath) return;

  const pathLength = 100;

  window.addEventListener("scroll", () => {
    const scrollTop = window.scrollY;
    const docHeight = document.body.scrollHeight - window.innerHeight;

    // Show widget after certain scroll (example: 250px)
    if (scrollTop > 300) {
      widget.classList.remove("opacity-0", "pointer-events-none");
    } else {
      widget.classList.add("opacity-0", "pointer-events-none");
    }

    // Update progress
    const progress = (scrollTop / docHeight) * 100;
    const offset = pathLength - (progress / 100) * pathLength;
    progressPath.style.strokeDashoffset = offset;
  });

  btn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
});
