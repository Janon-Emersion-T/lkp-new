const drawer = document.getElementById("drawer");
const overlay = document.getElementById("drawerOverlay");
const openDrawerBtn = document.getElementById("openDrawer");
const closeDrawerBtn = document.getElementById("closeDrawer");

if (drawer && overlay && openDrawerBtn) {
  openDrawerBtn.onclick = () => {
  drawer.classList.remove("-translate-x-full");
  overlay.classList.remove("hidden");
  };
}

if (drawer && overlay && closeDrawerBtn) {
  closeDrawerBtn.onclick = () => {
  drawer.classList.add("-translate-x-full");
  overlay.classList.add("hidden");
  };
}

if (drawer && overlay) {
  overlay.onclick = () => {
    drawer.classList.add("-translate-x-full");
    overlay.classList.add("hidden");
  };
}

function toggleMenu(id) {
  const menu = document.getElementById(id);
  if (!menu) return;

  const menuItem = menu.closest("li");
  if (!menuItem) return;

  const button = menuItem.querySelector(":scope > button");
  if (!button) return;

  const chevron = button.querySelector("i");
  const isOpen = !menu.classList.contains("hidden");

  const siblingMenus = [];
  const siblingsContainer = menuItem.parentElement;
  if (siblingsContainer) {
    Array.from(siblingsContainer.children).forEach((child) => {
      if (child === menuItem) return;
      const siblingMenu = child.querySelector(":scope > ul[id$='Menu']");
      if (siblingMenu) siblingMenus.push(siblingMenu);
    });
  }

  siblingMenus.forEach((m) => {
    if (!m.classList.contains("hidden")) closeDropdown(m);
  });

  if (isOpen) {
    closeDropdown(menu, chevron);
    button.setAttribute("aria-expanded", "false");
  } else {
    openDropdown(menu, chevron);
    button.setAttribute("aria-expanded", "true");
  }
}

function openDropdown(menu, chevron) {
  menu.classList.remove("hidden");
  menu.style.maxHeight = "0px";

  setTimeout(() => {
    menu.style.maxHeight = menu.scrollHeight + "px";
  }, 10);

  if (chevron) chevron.style.transform = "rotate(180deg)";
}

function closeDropdown(menu, chevron) {
  menu.style.maxHeight = menu.scrollHeight + "px";

  setTimeout(() => {
    menu.style.maxHeight = "0px";
  }, 10);

  setTimeout(() => {
    menu.classList.add("hidden");
    if (chevron) chevron.style.transform = "rotate(0deg)";
  }, 300);
}

window.toggleMenu = toggleMenu;
window.openDropdown = openDropdown;
window.closeDropdown = closeDropdown;
