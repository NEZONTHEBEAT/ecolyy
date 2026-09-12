document.addEventListener("DOMContentLoaded", function () {

    if (typeof gsap === "undefined") {
        return;
    }

    gsap.registerPlugin(ScrollTrigger);


    /* Hero */

    const revealElements =
        document.querySelectorAll(".reveal");

    gsap.to(revealElements, {
        opacity: 1,
        y: 0,
        duration: 1,
        stagger: 0.12,
        ease: "power3.out"
    });


    /* Hero Visual */

    gsap.from(".hero-glass-card", {
        opacity: 0,
        scale: 0.88,
        y: 50,
        duration: 1.3,
        delay: 0.2,
        ease: "power3.out"
    });


    /* Problem Cards */

    gsap.utils.toArray(".problem-card").forEach(
        function (card, index) {

            gsap.from(card, {

                opacity: 0,
                y: 40,

                duration: 0.8,

                delay: index * 0.05,

                ease: "power3.out",

                scrollTrigger: {
                    trigger: card,
                    start: "top 85%",
                    once: true
                }

            });

        }
    );


    /* Steps */

    gsap.utils.toArray(".step-card").forEach(
        function (card, index) {

            gsap.from(card, {

                opacity: 0,
                y: 35,

                duration: 0.75,

                delay: index * 0.06,

                ease: "power3.out",

                scrollTrigger: {
                    trigger: card,
                    start: "top 85%",
                    once: true
                }

            });

        }
    );


    /* Category Cards */

    gsap.utils.toArray(".category-card").forEach(
        function (card, index) {

            gsap.from(card, {

                opacity: 0,
                y: 25,

                duration: 0.65,

                delay: index * 0.04,

                ease: "power3.out",

                scrollTrigger: {
                    trigger: card,
                    start: "top 88%",
                    once: true
                }

            });

        }
    );


    /* Impact */

    gsap.from(".impact-stat", {

        opacity: 0,
        y: 35,

        duration: 0.8,
        stagger: 0.1,

        ease: "power3.out",

        scrollTrigger: {
            trigger: ".impact-stats",
            start: "top 85%",
            once: true
        }

    });


    /* Institution */

    gsap.from(".institution-wrapper", {

        opacity: 0,
        y: 45,

        duration: 1,

        ease: "power3.out",

        scrollTrigger: {
            trigger: ".institution-wrapper",
            start: "top 85%",
            once: true
        }

    });


    /* Parallax */

    gsap.to(".hero-orb", {

        y: -70,

        ease: "none",

        scrollTrigger: {
            trigger: ".hero-section",
            start: "top top",
            end: "bottom top",
            scrub: true
        }

    });

});