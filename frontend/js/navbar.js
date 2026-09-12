document.addEventListener("DOMContentLoaded", function () {

    const menuButton =
        document.getElementById("mobileMenuBtn");

    const mobileMenu =
        document.getElementById("mobileMenu");

    if (!menuButton || !mobileMenu) return;

    menuButton.addEventListener("click", function () {

        mobileMenu.classList.toggle("active");

        const icon =
            menuButton.querySelector("i");

        if (mobileMenu.classList.contains("active")) {

            icon.className = "bi bi-x-lg";

        } else {

            icon.className = "bi bi-list";

        }

    });


    const mobileLinks =
        mobileMenu.querySelectorAll("a");

    mobileLinks.forEach(function (link) {

        link.addEventListener("click", function () {

            mobileMenu.classList.remove("active");

            const icon =
                menuButton.querySelector("i");

            icon.className = "bi bi-list";

        });

    });


    window.addEventListener("scroll", function () {

        const navbar =
            document.querySelector(".rekart-navbar");

        if (!navbar) return;

        if (window.scrollY > 50) {

            navbar.classList.add("navbar-scrolled");

        } else {

            navbar.classList.remove("navbar-scrolled");

        }

    });

});