

window.addEventListener("load", () => {
  const preloader = document.getElementById("preloader");
  if (!preloader) return;
  preloader.classList.add("opacity-0");
  setTimeout(() => preloader.classList.add("hidden"), 300);
});
