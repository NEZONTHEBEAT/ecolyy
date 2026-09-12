/* =========================================================
   ECOLYY INSTITUTION PANEL
   Backend API Integration
   ========================================================= */

document.addEventListener("DOMContentLoaded", async () => {

    /* =====================================================
       AUTH
    ===================================================== */

    const token = localStorage.getItem("ecolyy_access_token");
    const role = (
        localStorage.getItem("ecolyy_role") || ""
    ).toLowerCase();

    const rawUser = localStorage.getItem("ecolyy_user");

    if (!token || !rawUser || role !== "institution") {
        clearAuth();
        window.location.replace("../pages/login.html");
        return;
    }


    let currentUser = {};

    try {
        currentUser = JSON.parse(rawUser) || {};
    } catch {
        currentUser = {};
    }


    /* =====================================================
       AUTH CLEAR
    ===================================================== */

    function clearAuth() {

        const keys = [
            "ecolyy_access_token",
            "ecolyy_refresh_token",
            "ecolyy_token_type",
            "ecolyy_role",
            "ecolyy_user",
            "ecolyy_user_name",
            "ecolyy_user_email",
            "ecolyy_admin_name",
            "ecolyy_admin_email",
            "ecolyy_partner_name",
            "ecolyy_partner_email",
            "ecolyy_institute_name",
            "ecolyy_institute_email"
        ];

        keys.forEach(key => {
            localStorage.removeItem(key);
        });
    }


    /* =====================================================
       HELPERS
    ===================================================== */

    function setText(id, value) {

        const element = document.getElementById(id);

        if (element) {
            element.textContent = value ?? "";
        }
    }


    function setValue(id, value) {

        const element = document.getElementById(id);

        if (element) {
            element.value = value ?? "";
        }
    }


    function getInitials(name) {

        const result = String(name || "Ecolyy Institute")
            .trim()
            .split(/\s+/)
            .filter(Boolean)
            .map(word => word.charAt(0))
            .join("")
            .slice(0, 2)
            .toUpperCase();

        return result || "EI";
    }


    function escapeHtml(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    function formatDate(value) {

        if (!value) {
            return "-";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    }


    function formatWeight(value) {

        if (
            value === null ||
            value === undefined ||
            value === ""
        ) {
            return "-";
        }

        const number = Number(value);

        if (Number.isNaN(number)) {
            return `${value} KG`;
        }

        return `${number.toFixed(number % 1 === 0 ? 0 : 2)} KG`;
    }


    function formatStatus(status) {

        if (!status) {
            return "Pending";
        }

        switch (status) {

            case "in_progress":
                return "In Progress";

            case "assigned":
                return "Assigned";

            case "completed":
                return "Completed";

            case "cancelled":
                return "Cancelled";

            case "disputed":
                return "Disputed";

            case "pending":
            default:
                return "Pending";
        }
    }


    function getStatusClass(status) {

        switch (status) {

            case "completed":
                return "completed";

            case "assigned":
                return "assigned";

            case "in_progress":
                return "progress";

            case "cancelled":
                return "cancelled";

            case "disputed":
                return "pending";

            case "pending":
            default:
                return "pending";
        }
    }


    function getPartnerName(pickup) {

        if (!pickup) {
            return "Not assigned";
        }

        if (pickup.partner_name) {
            return pickup.partner_name;
        }

        if (pickup.partner) {

            if (typeof pickup.partner === "string") {
                return pickup.partner;
            }

            if (pickup.partner.name) {
                return pickup.partner.name;
            }

            if (pickup.partner.email) {
                return pickup.partner.email;
            }
        }

        if (pickup.partner_id) {
            return "Assigned Partner";
        }

        return "Not assigned";
    }


    function getPickupId(pickup) {

        const id =
            pickup?._id ||
            pickup?.id ||
            pickup?.pickup_id ||
            "";

        return String(id)
            .replace(/^#/, "")
            .slice(-12);
    }


    /* =====================================================
       USER UI
    ===================================================== */

    function updateUserUI(user = currentUser) {

        const displayName =
            user.name ||
            user.institution_name ||
            user.organization_name ||
            "Ecolyy Institute";

        const email =
            user.email || "";

        const displayRole =
            user.display_role ||
            user.role ||
            "Institute";

        const initials =
            user.initials ||
            getInitials(displayName);


        setText(
            "sidebarUserAvatar",
            initials
        );

        setText(
            "sidebarUserName",
            displayName
        );

        setText(
            "sidebarUserRole",
            displayRole
        );

        setText(
            "topbarUserAvatar",
            initials
        );


        /* PROFILE */

        setText(
            "profileAvatar",
            initials
        );

        setText(
            "profileName",
            displayName
        );

        setText(
            "profileEmail",
            email
        );


        setValue(
            "profileNameInput",
            displayName
        );

        setValue(
            "profileEmailInput",
            email
        );

        setValue(
            "profileRoleInput",
            displayRole
        );

        setValue(
            "profilePhoneInput",
            user.phone ||
            user.mobile ||
            "Not provided"
        );
    }


    /* =====================================================
       GET INSTITUTION PROFILE
       GET /api/v1/institutions/me
    ===================================================== */

    async function loadInstitutionProfile() {

        try {

            const result =
                await EcolyyAPI.get(
                    "/institutions/me"
                );

            if (!result) {
                return null;
            }

            console.log(
                "Institution Profile:",
                result
            );


            const institution =
                result;


            currentUser = {
                ...currentUser,
                ...institution
            };


            localStorage.setItem(
                "ecolyy_user",
                JSON.stringify(currentUser)
            );


            updateUserUI(
                currentUser
            );


            return institution;


        } catch (error) {

            console.error(
                "Institution profile error:",
                error
            );

            return null;
        }
    }


    /* =====================================================
       GET INSTITUTION PICKUPS
       GET /api/v1/institutions/me/pickups
    ===================================================== */

    async function loadInstitutionPickups() {

        const tableBody =
            document.getElementById(
                "pickupsTableBody"
            );

        if (!tableBody) {
            return [];
        }


        try {

            tableBody.innerHTML = `
                <tr>
                    <td
                        colspan="6"
                        style="
                            text-align:center;
                            padding:2rem;
                            color:#888;
                        "
                    >

                        <div
                            class="spinner-border spinner-border-sm"
                        ></div>

                        <div style="margin-top:.5rem;">
                            Loading pickups...
                        </div>

                    </td>
                </tr>
            `;


            const result =
                await EcolyyAPI.get(
                    "/institutions/me/pickups"
                );


            console.log(
                "Institution Pickups:",
                result
            );


            const pickups =
                Array.isArray(result)
                    ? result
                    : (
                        result?.data ||
                        result?.pickups ||
                        []
                    );


            if (!pickups.length) {

                renderEmptyPickups(
                    tableBody
                );

                updateDashboardStats([]);

                return [];
            }


            renderPickupTable(
                tableBody,
                pickups
            );


            updateDashboardStats(
                pickups
            );


            return pickups;


        } catch (error) {

            console.error(
                "Institution pickups error:",
                error
            );


            tableBody.innerHTML = `
                <tr>

                    <td
                        colspan="6"
                        style="
                            text-align:center;
                            padding:2rem;
                            color:#e74c3c;
                        "
                    >

                        <i
                            class="bi bi-exclamation-circle"
                            style="
                                display:block;
                                font-size:1.5rem;
                                margin-bottom:.5rem;
                            "
                        ></i>

                        Failed to load pickup requests.

                        <div style="
                            font-size:.7rem;
                            margin-top:.35rem;
                        ">
                            ${escapeHtml(
                                error.message
                            )}
                        </div>

                    </td>

                </tr>
            `;


            return [];
        }
    }


    /* =====================================================
       RENDER PICKUP TABLE
    ===================================================== */

    function renderPickupTable(
        tableBody,
        pickups
    ) {

        const isDashboard =
            tableBody.closest(
                ".dashboard-panel"
            ) &&
            tableBody.closest(
                ".dashboard-main"
            ) &&
            !document.querySelector(
                "#locationsGrid"
            );


        /* =============================================
           DASHBOARD TABLE

           Pickup
           Partner
           Date
           Status
           Action
        ============================================= */

        if (
            isDashboard &&
            !document.querySelector(
                ".pickup-page-table"
            )
        ) {

            tableBody.innerHTML =
                pickups
                    .slice(0, 5)
                    .map(
                        pickup => {

                            const id =
                                getPickupId(
                                    pickup
                                );

                            const partner =
                                getPartnerName(
                                    pickup
                                );

                            const date =
                                pickup.scheduled_date ||
                                pickup.created_at ||
                                "-";

                            const status =
                                String(
                                    pickup.status ||
                                    "pending"
                                ).toLowerCase();


                            return `
                                <tr>

                                    <td>

                                        <span class="pickup-id">
                                            #${escapeHtml(id)}
                                        </span>

                                    </td>


                                    <td>
                                        ${escapeHtml(
                                            partner
                                        )}
                                    </td>


                                    <td>
                                        ${formatDate(
                                            date
                                        )}
                                    </td>


                                    <td>

                                        <span
                                            class="status ${getStatusClass(
                                                status
                                            )}"
                                        >
                                            ${escapeHtml(
                                                formatStatus(
                                                    status
                                                )
                                            )}
                                        </span>

                                    </td>


                                    <td>

                                        <a
                                            href="pickups.html"
                                            class="table-action"
                                        >
                                            Details
                                        </a>

                                    </td>

                                </tr>
                            `;
                        }
                    )
                    .join("");


            return;
        }


        /* =============================================
           PICKUP PAGE TABLE

           Pickup
           Partner
           Date
           Material
           Weight
           Status
        ============================================= */

        tableBody.innerHTML =
            pickups
                .map(
                    pickup => {

                        const id =
                            getPickupId(
                                pickup
                            );

                        const partner =
                            getPartnerName(
                                pickup
                            );

                        const date =
                            pickup.scheduled_date ||
                            pickup.created_at ||
                            "-";

                        const material =
                            pickup.waste_category ||
                            "-";

                        const weight =
                            pickup.actual_weight_kg ??
                            pickup.estimated_weight_kg ??
                            null;

                        const status =
                            String(
                                pickup.status ||
                                "pending"
                            ).toLowerCase();


                        return `
                            <tr>

                                <td>

                                    <span class="pickup-id">
                                        #${escapeHtml(id)}
                                    </span>

                                </td>


                                <td>
                                    ${escapeHtml(
                                        partner
                                    )}
                                </td>


                                <td>
                                    ${formatDate(
                                        date
                                    )}
                                </td>


                                <td>
                                    ${escapeHtml(
                                        material
                                    )}
                                </td>


                                <td>
                                    ${escapeHtml(
                                        formatWeight(
                                            weight
                                        )
                                    )}
                                </td>


                                <td>

                                    <span
                                        class="status ${getStatusClass(
                                            status
                                        )}"
                                    >
                                        ${escapeHtml(
                                            formatStatus(
                                                status
                                            )
                                        )}
                                    </span>

                                </td>

                            </tr>
                        `;
                    }
                )
                .join("");
    }


    /* =====================================================
       EMPTY PICKUPS
    ===================================================== */

    function renderEmptyPickups(
        tableBody
    ) {

        const isDashboard =
            tableBody
                .closest(
                    ".dashboard-panel"
                )
                ?.querySelector(
                    ".panel-header"
                );


        const colspan =
            isDashboard
                ? 5
                : 6;


        tableBody.innerHTML = `
            <tr>

                <td
                    colspan="${colspan}"
                    style="
                        text-align:center;
                        padding:2rem;
                        color:#888;
                    "
                >

                    <i
                        class="bi bi-inbox"
                        style="
                            display:block;
                            font-size:1.5rem;
                            margin-bottom:.5rem;
                            opacity:.45;
                        "
                    ></i>

                    No pickup requests yet.

                </td>

            </tr>
        `;
    }


    /* =====================================================
       DASHBOARD STATS
    ===================================================== */

    function updateDashboardStats(
        pickups
    ) {

        const statCards =
            document.querySelectorAll(
                ".stat-card"
            );


        if (!statCards.length) {
            return;
        }


        const total =
            pickups.length;


        const completed =
            pickups.filter(
                pickup =>
                    String(
                        pickup.status || ""
                    ).toLowerCase() ===
                    "completed"
            ).length;


        const pending =
            pickups.filter(
                pickup => {

                    const status =
                        String(
                            pickup.status ||
                            ""
                        ).toLowerCase();


                    return [
                        "pending",
                        "assigned",
                        "in_progress",
                        "scheduled"
                    ].includes(
                        status
                    );
                }
            ).length;


        const values =
            document.querySelectorAll(
                ".stat-card strong"
            );


        /*
           Dashboard has:
           156
           142
           14
           3.2T
        */

        if (values[0]) {

            values[0].textContent =
                total;
        }


        if (values[1]) {

            values[1].textContent =
                completed;
        }


        if (values[2]) {

            values[2].textContent =
                pending;
        }


        /*
           Recycled value is calculated
           from actual completed weight.
        */

        if (values[3]) {

            const recycledKg =
                pickups
                    .filter(
                        pickup =>
                            String(
                                pickup.status ||
                                ""
                            ).toLowerCase() ===
                            "completed"
                    )
                    .reduce(
                        (
                            totalWeight,
                            pickup
                        ) =>
                            totalWeight +
                            Number(
                                pickup.actual_weight_kg ||
                                0
                            ),
                        0
                    );


            if (recycledKg > 0) {

                values[3].textContent =
                    recycledKg >= 1000
                        ? `${(
                            recycledKg / 1000
                        ).toFixed(1)}T`
                        : `${Math.round(
                            recycledKg
                        )} KG`;

            }
        }
    }


    /* =====================================================
       GET REPORT
       GET /api/v1/institutions/me/reports
    ===================================================== */

    async function loadInstitutionReport() {

        try {

            const result =
                await EcolyyAPI.get(
                    "/institutions/me/reports"
                );


            console.log(
                "Institution Report:",
                result
            );


            const report =
                result;


            const statValues =
                document.querySelectorAll(
                    ".stat-card strong"
                );


            /* Total weight */

            if (
                report.total_weight_kg !==
                undefined
            ) {

                if (statValues[0]) {

                    const kg =
                        Number(
                            report.total_weight_kg
                        ) || 0;


                    statValues[0].textContent =
                        kg >= 1000
                            ? `${(
                                kg / 1000
                            ).toFixed(1)}T`
                            : `${Math.round(
                                kg
                            )} KG`;
                }
            }


            /* Total pickups */

            if (
                report.total_pickups !==
                undefined
            ) {

                /*
                   On reports page the second
                   stat is Pickups.
                */

                if (statValues[1]) {

                    statValues[1].textContent =
                        report.total_pickups;
                }
            }


            return report;


        } catch (error) {

            console.error(
                "Institution report error:",
                error
            );


            return null;
        }
    }


    /* =====================================================
       REPORT BREAKDOWN
    ===================================================== */

    function renderReportBreakdown(
        report
    ) {

        if (!report) {
            return;
        }


        const breakdown =
            report.by_category || [];


        const bars =
            document.querySelectorAll(
                ".analytics-bars > div"
            );


        if (
            !breakdown.length ||
            !bars.length
        ) {

            return;
        }


        const maxWeight =
            Math.max(
                ...breakdown.map(
                    item =>
                        Number(
                            item.total_weight_kg ||
                            0
                        )
                ),
                1
            );


        bars.forEach(
            bar => {

                const label =
                    bar.querySelector(
                        "span"
                    );


                const progress =
                    bar.querySelector(
                        ".bar i"
                    );


                const value =
                    bar.querySelector(
                        "strong"
                    );


                if (
                    !label ||
                    !progress ||
                    !value
                ) {

                    return;
                }


                const category =
                    label.textContent
                        .trim()
                        .toLowerCase();


                const found =
                    breakdown.find(
                        item =>
                            String(
                                item._id || ""
                            )
                                .trim()
                                .toLowerCase() ===
                            category
                    );


                if (!found) {
                    return;
                }


                const weight =
                    Number(
                        found.total_weight_kg ||
                        0
                    );


                const percentage =
                    Math.min(
                        100,
                        (
                            weight /
                            maxWeight
                        ) * 100
                    );


                progress.style.width =
                    `${percentage}%`;


                value.textContent =
                    weight >= 1000
                        ? `${(
                            weight / 1000
                        ).toFixed(1)}T`
                        : `${Math.round(
                            weight
                        )} KG`;
            }
        );
    }


    /* =====================================================
       LOCATIONS
       GET /api/v1/institutions/me
    ===================================================== */

    async function loadLocations() {

        const grid =
            document.getElementById(
                "locationsGrid"
            );


        if (!grid) {
            return [];
        }


        try {

            grid.innerHTML = `
                <div class="empty-state">

                    <i class="bi bi-hourglass-split"></i>

                    <h3>
                        Loading Locations
                    </h3>

                    <p>
                        Please wait...
                    </p>

                </div>
            `;


            /*
               We already know that
               GET /institutions/me
               returns the institution
               document containing locations.
            */

            const result =
                await EcolyyAPI.get(
                    "/institutions/me"
                );


            const institution =
                result;


            const locations =
                Array.isArray(
                    institution?.locations
                )
                    ? institution.locations
                    : [];


            if (!locations.length) {

                grid.innerHTML = `
                    <div class="empty-state">

                        <i
                            class="bi bi-geo-alt"
                        ></i>

                        <h3>
                            No Locations Added
                        </h3>

                        <p>
                            Add your first pickup location to get started.
                        </p>

                    </div>
                `;


                return [];
            }


            grid.innerHTML =
                locations
                    .map(
                        (location, index) => {

                            const label =
                                location.label ||
                                `Location ${
                                    index + 1
                                }`;


                            const address =
                                location.address ||
                                "Address not provided";


                            const lat =
                                location.lat;


                            const lng =
                                location.lng;


                            return `
                                <div class="address-card">

                                    <div class="address-header">

                                        <span class="address-type">

                                            <i
                                                class="bi bi-geo-alt"
                                            ></i>

                                            Pickup Location

                                        </span>


                                        ${
                                            index === 0
                                                ? `
                                                    <span class="default-badge">
                                                        Primary
                                                    </span>
                                                  `
                                                : ""
                                        }

                                    </div>


                                    <h3>
                                        ${escapeHtml(
                                            label
                                        )}
                                    </h3>


                                    <p>

                                        ${escapeHtml(
                                            address
                                        )}

                                        ${
                                            lat !==
                                                undefined &&
                                            lng !==
                                                undefined
                                                ? `
                                                    <br>
                                                    Coordinates:
                                                    ${escapeHtml(
                                                        String(lat)
                                                    )},
                                                    ${escapeHtml(
                                                        String(lng)
                                                    )}
                                                  `
                                                : ""
                                        }

                                    </p>


                                    <div class="address-actions">

                                        <button
                                            type="button"
                                            onclick="manageLocation(${index})"
                                        >
                                            Manage
                                        </button>

                                    </div>

                                </div>
                            `;

                        }
                    )
                    .join("");


            return locations;


        } catch (error) {

            console.error(
                "Locations error:",
                error
            );


            grid.innerHTML = `
                <div class="empty-state">

                    <i
                        class="bi bi-exclamation-circle"
                    ></i>

                    <h3>
                        Failed to Load Locations
                    </h3>

                    <p>
                        ${escapeHtml(
                            error.message
                        )}
                    </p>

                </div>
            `;


            return [];
        }
    }


    /* =====================================================
       ADD LOCATION
    ===================================================== */

    async function addLocation(
        payload
    ) {

        try {

            const result =
                await EcolyyAPI.post(
                    "/institutions/me/locations",
                    payload
                );


            console.log(
                "Location added:",
                result
            );


            await loadLocations();


            return result;


        } catch (error) {

            console.error(
                "Add location error:",
                error
            );


            alert(
                error.message ||
                "Failed to add location."
            );


            return null;
        }
    }


    /* =====================================================
       LOCATION ACTIONS
    ===================================================== */

    window.editLocation =
        function (id) {

            alert(
                `Location ${id} editing is not available yet.`
            );

        };


    window.manageLocation =
        function (id) {

            alert(
                `Location ${id} selected.`
            );

        };


    window.deleteLocation =
        function () {

            /*
               Current backend has no
               DELETE /institutions/me/locations/{id}
               endpoint.
            */

            alert(
                "Delete Location API is not available in the backend yet."
            );

        };


    /* =====================================================
       ADD LOCATION BUTTON
    ===================================================== */

    const addLocationBtn =
        document.getElementById(
            "addLocationBtn"
        );


    addLocationBtn?.addEventListener(
        "click",
        async () => {

            /*
               Current backend expects exactly:

               {
                   label,
                   address,
                   lat,
                   lng
               }

               This temporary prompt-based version
               is only for testing the API.
            */

            const label =
                window.prompt(
                    "Location name:"
                );


            if (!label) {
                return;
            }


            const address =
                window.prompt(
                    "Location address:"
                );


            if (!address) {
                return;
            }


            const latInput =
                window.prompt(
                    "Latitude (optional):"
                );


            const lngInput =
                window.prompt(
                    "Longitude (optional):"
                );


            const payload = {

                label:
                    label.trim(),

                address:
                    address.trim(),

                lat:
                    latInput
                        ? Number(latInput)
                        : null,

                lng:
                    lngInput
                        ? Number(lngInput)
                        : null
            };


            await addLocation(
                payload
            );

        }
    );


    /* =====================================================
       MOBILE SIDEBAR
    ===================================================== */

    const sidebar =
        document.getElementById(
            "dashboardSidebar"
        );


    const toggle =
        document.getElementById(
            "sidebarToggle"
        );


    const overlay =
        document.getElementById(
            "sidebarOverlay"
        );


    function openSidebar() {

        sidebar?.classList.add(
            "open"
        );

        overlay?.classList.add(
            "active"
        );

        document.body.style.overflow =
            "hidden";
    }


    function closeSidebar() {

        sidebar?.classList.remove(
            "open"
        );

        overlay?.classList.remove(
            "active"
        );

        document.body.style.overflow =
            "";
    }


    toggle?.addEventListener(
        "click",
        openSidebar
    );


    overlay?.addEventListener(
        "click",
        closeSidebar
    );


    document
        .querySelectorAll(
            ".sidebar-link"
        )
        .forEach(
            link => {

                link.addEventListener(
                    "click",
                    () => {

                        if (
                            window.innerWidth <=
                            900
                        ) {

                            closeSidebar();

                        }

                    }
                );

            }
        );


    /* =====================================================
       LOGOUT
    ===================================================== */

    document
        .getElementById(
            "sidebarLogout"
        )
        ?.addEventListener(
            "click",
            () => {

                if (
                    !confirm(
                        "Are you sure you want to logout?"
                    )
                ) {

                    return;
                }


                clearAuth();


                window.location.replace(
                    "../pages/login.html"
                );

            }
        );


    /* =====================================================
       CURRENT PAGE
    ===================================================== */

    const currentPage =
        window.location.pathname
            .split("/")
            .pop()
            .toLowerCase();


    /* =====================================================
       INITIAL USER UI
    ===================================================== */

    updateUserUI();


    /* =====================================================
       PAGE API LOADING
    ===================================================== */

    if (
        currentPage ===
        "dashboard.html"
    ) {

        await loadInstitutionProfile();

        await loadInstitutionPickups();

    }


    if (
        currentPage ===
        "certificates.html"
    ) {

        await loadInstitutionProfile();

    }


    if (
        currentPage ===
        "pickups.html"
    ) {

        await loadInstitutionProfile();

        await loadInstitutionPickups();

    }


    if (
        currentPage ===
        "locations.html"
    ) {

        await loadInstitutionProfile();

        await loadLocations();

    }


    if (
        currentPage ===
        "schedule.html"
    ) {

        await loadInstitutionProfile();

    }


    if (
        currentPage ===
        "reports.html"
    ) {

        await loadInstitutionProfile();

        const report =
            await loadInstitutionReport();

        renderReportBreakdown(
            report
        );

    }


    if (
        currentPage ===
        "profile.html"
    ) {

        await loadInstitutionProfile();

    }


    console.log(
        "Ecolyy Institution Panel API integration loaded."
    );

});