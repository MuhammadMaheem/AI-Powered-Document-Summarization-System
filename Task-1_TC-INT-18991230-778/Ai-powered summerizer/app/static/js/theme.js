/**
 * Dark / light theme toggle.
 *
 * Reads the preferred theme from localStorage on page load.
 * Falls back to the OS preference if no stored value exists.
 * Persists the user's choice for future visits.
 */

(function () {
  const STORAGE_KEY = "teyzix-theme";
  const root = document.documentElement;

  function getInitialTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "light") return stored;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  applyTheme(getInitialTheme());

  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("themeToggle");
    if (!btn) return;

    btn.addEventListener("click", function () {
      const current = root.getAttribute("data-theme");
      applyTheme(current === "dark" ? "light" : "dark");
    });
  });
})();
