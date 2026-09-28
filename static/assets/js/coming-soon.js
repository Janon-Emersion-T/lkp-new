
// Only run countdown if the container exists on this page
const countdownContainer = document.querySelector(".countdown-item");

if (countdownContainer) {
  // Set the date we're counting down to (10 days from now for demo)
  // BUYER NOTE: Change this to your launch date (example): new Date("Dec 31, 2026 23:59:59")
  const countDownDate = new Date();
  countDownDate.setDate(countDownDate.getDate() + 10);

  // Update the count down every 1 second
  const timer = setInterval(function () {
    const now = new Date().getTime();
    const distance = countDownDate - now;

    // Time calculations
    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor(
      (distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
    );
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    // Safe update: check if each element exists before modifying
    const daysEl = document.getElementById("days");
    const hoursEl = document.getElementById("hours");
    const minutesEl = document.getElementById("minutes");
    const secondsEl = document.getElementById("seconds");

    if (daysEl) daysEl.innerHTML = days < 10 ? "0" + days : days;
    if (hoursEl) hoursEl.innerHTML = hours < 10 ? "0" + hours : hours;
    if (minutesEl) minutesEl.innerHTML = minutes < 10 ? "0" + minutes : minutes;
    if (secondsEl) secondsEl.innerHTML = seconds < 10 ? "0" + seconds : seconds;

    // If count down is finished
    if (distance < 0) {
      clearInterval(timer);
      if (countdownContainer) {
        countdownContainer.innerHTML = "WE ARE LIVE!";
      }
    }
  }, 1000);
}

// Auto-update year - safely
const yearEl = document.getElementById("year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}
