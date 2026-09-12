document.addEventListener("DOMContentLoaded", function () {

    console.log(
        "%cEcolyy%c — Recycling,Simplified.",
        "color:#0B4F3A;font-weight:800;font-size:18px;",
        "color:#69B532;font-weight:600;"
    );


    /* Smooth anchor scrolling */

    document.querySelectorAll(
        'a[href^="#"]'
    ).forEach(function (link) {

        link.addEventListener("click", function (event) {

            const targetId =
                this.getAttribute("href");

            if (
                !targetId ||
                targetId === "#"
            ) {
                return;
            }

            const target =
                document.querySelector(targetId);

            if (!target) return;

            event.preventDefault();

            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });

    });


    /* Prevent demo links */

    document.querySelectorAll(
        'a[href="#"]'
    ).forEach(function (link) {

        link.addEventListener("click", function (event) {
            event.preventDefault();
        });

    });

});