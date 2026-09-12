/* =========================================================
   ReKart User Dashboard
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const user =
            getCurrentUser();

        if (!user) return;

        document
            .querySelectorAll(
                "[data-user-name]"
            )
            .forEach(element => {

                element.textContent =
                    user.name ||
                    user.full_name ||
                    "ReKart User";
            });

        document
            .querySelectorAll(
                "[data-user-email]"
            )
            .forEach(element => {

                element.textContent =
                    user.email || "";
            });

        loadUserDashboard();
    }
);


async function loadUserDashboard() {

    const statPickups =
        document.getElementById(
            "statPickups"
        );

    if (!statPickups) return;

    try {

        const data =
            await RekartAPI.get(
                "/users/me/dashboard"
            );

        if (data.total_pickups !== undefined) {
            statPickups.textContent =
                data.total_pickups;
        }

        const reward =
            document.getElementById(
                "statRewards"
            );

        if (
            reward &&
            data.reward_points !== undefined
        ) {
            reward.textContent =
                data.reward_points;
        }

    } catch (error) {

        console.warn(
            "Dashboard data unavailable."
        );
    }
}