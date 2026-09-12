/* =========================================================
   ReKart Admin Dashboard
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        if (
            document.body.dataset.role !==
            "admin"
        ) {
            return;
        }

        loadAdminDashboard();
    }
);


async function loadAdminDashboard() {

    try {

        const data =
            await RekartAPI.get(
                "/admin/dashboard"
            );

        setAdminStat(
            "adminUsers",
            data.total_users
        );

        setAdminStat(
            "adminPartners",
            data.total_partners
        );

        setAdminStat(
            "adminInstitutions",
            data.total_institutions
        );

        setAdminStat(
            "adminPickups",
            data.total_pickups
        );

    } catch (error) {

        console.warn(
            "Admin API unavailable."
        );
    }
}


function setAdminStat(
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


/* ================= ADMIN ACTIONS ================= */

async function deleteUser(userId) {

    if (
        !confirm(
            "Are you sure you want to delete this user?"
        )
    ) {
        return;
    }

    try {

        await RekartAPI.delete(
            `/admin/users/${userId}`
        );

        alert(
            "User deleted successfully."
        );

        location.reload();

    } catch (error) {

        alert(
            error.message ||
            "Unable to delete user."
        );
    }
}


async function updateUserStatus(
    userId,
    status
) {

    try {

        await RekartAPI.patch(
            `/admin/users/${userId}/status`,
            {
                status
            }
        );

        location.reload();

    } catch (error) {

        alert(
            error.message ||
            "Unable to update user."
        );
    }
}