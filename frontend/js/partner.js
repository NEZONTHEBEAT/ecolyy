/* =========================================================
   ReKart Partner Dashboard
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        if (
            document.body.dataset.role !==
            "partner"
        ) {
            return;
        }

        loadPartnerDashboard();
    }
);


async function loadPartnerDashboard() {

    try {

        const data =
            await RekartAPI.get(
                "/partners/me/dashboard"
            );

        updateElement(
            "partnerPickups",
            data.total_pickups
        );

        updateElement(
            "partnerCompleted",
            data.completed_pickups
        );

        updateElement(
            "partnerEarnings",
            data.total_earnings
        );

    } catch (error) {

        console.warn(
            "Partner dashboard API unavailable."
        );
    }
}


async function acceptPickup(
    pickupId
) {

    if (!pickupId) return;

    try {

        await RekartAPI.patch(
            `/pickups/${pickupId}/accept`,
            {}
        );

        alert(
            "Pickup accepted successfully."
        );

        location.reload();

    } catch (error) {

        alert(
            error.message ||
            "Unable to accept pickup."
        );
    }
}


async function updatePickupStatus(
    pickupId,
    status
) {

    try {

        await RekartAPI.patch(
            `/pickups/${pickupId}/status`,
            {
                status
            }
        );

        alert(
            "Pickup status updated."
        );

        location.reload();

    } catch (error) {

        alert(
            error.message ||
            "Unable to update status."
        );
    }
}


function updateElement(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (
        element &&
        value !== undefined
    ) {
        element.textContent =
            value;
    }
}