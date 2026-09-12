(function () {

    const themeToggle =
        document.getElementById("themeToggle");

    if (!themeToggle) return;

    const icon =
        themeToggle.querySelector("i");

    const savedTheme =
        localStorage.getItem("rekart-theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");

        if (icon) {
            icon.className = "bi bi-sun";
        }
    }

    themeToggle.addEventListener("click", function () {

        document.body.classList.toggle("dark-mode");

        const isDark =
            document.body.classList.contains("dark-mode");

        localStorage.setItem(
            "rekart-theme",
            isDark ? "dark" : "light"
        );

        if (icon) {
            icon.className = isDark
                ? "bi bi-sun"
                : "bi bi-moon-stars";
        }

    });

})();