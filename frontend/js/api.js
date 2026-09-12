/* =========================================================
   ECOLYY API LAYER
   FastAPI Backend Integration
   ========================================================= */

const API_CONFIG = {
    BASE_URL: "https://ecolyy.onrender.com/api/v1"
};


/* =========================================================
   API OBJECT
   ========================================================= */

const EcolyyAPI = {

    /* ---------------------------------------------------------
       MAIN REQUEST
    --------------------------------------------------------- */

    async request(endpoint, options = {}, retry = true) {

        const token =
            localStorage.getItem("ecolyy_access_token");

        const headers = {
            "Content-Type": "application/json",
            ...(options.headers || {})
        };

        if (token) {
            headers.Authorization =
                `Bearer ${token}`;
        }

        try {

            const response = await fetch(
                `${API_CONFIG.BASE_URL}${endpoint}`,
                {
                    ...options,
                    headers
                }
            );


            /* =================================================
               ACCESS TOKEN EXPIRED
            ================================================= */

            if (
                response.status === 401 &&
                retry &&
                localStorage.getItem("ecolyy_refresh_token")
            ) {

                const refreshed =
                    await this.refreshToken();

                if (refreshed) {

                    return this.request(
                        endpoint,
                        options,
                        false
                    );
                }
            }


            /* =================================================
               RESPONSE
            ================================================= */

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";


            let data = null;


            if (
                contentType.includes(
                    "application/json"
                )
            ) {

                data =
                    await response.json();

            } else {

                data =
                    await response.text();

            }


            /* =================================================
               ERROR
            ================================================= */

            if (!response.ok) {

                const message =
                    typeof data === "object"
                        ? (
                            data?.detail ||
                            data?.message ||
                            "API request failed"
                        )
                        : (
                            data ||
                            "API request failed"
                        );


                throw new Error(message);
            }


            return data;


        } catch (error) {

            console.error(
                "Ecolyy API Error:",
                {
                    endpoint,
                    error
                }
            );

            throw error;
        }
    },


    /* ---------------------------------------------------------
       GET
    --------------------------------------------------------- */

    get(endpoint) {

        return this.request(
            endpoint,
            {
                method: "GET"
            }
        );

    },


    /* ---------------------------------------------------------
       POST
    --------------------------------------------------------- */

    post(endpoint, body = {}) {

        return this.request(
            endpoint,
            {
                method: "POST",
                body: JSON.stringify(body)
            }
        );

    },


    /* ---------------------------------------------------------
       PUT
    --------------------------------------------------------- */

    put(endpoint, body = {}) {

        return this.request(
            endpoint,
            {
                method: "PUT",
                body: JSON.stringify(body)
            }
        );

    },


    /* ---------------------------------------------------------
       PATCH
    --------------------------------------------------------- */

    patch(endpoint, body = {}) {

        return this.request(
            endpoint,
            {
                method: "PATCH",
                body: JSON.stringify(body)
            }
        );

    },


    /* ---------------------------------------------------------
       DELETE
    --------------------------------------------------------- */

    delete(endpoint) {

        return this.request(
            endpoint,
            {
                method: "DELETE"
            }
        );

    },


    /* =========================================================
       AUTH REFRESH
    ========================================================= */

    async refreshToken() {

        const refreshToken =
            localStorage.getItem(
                "ecolyy_refresh_token"
            );


        if (!refreshToken) {

            return false;
        }


        try {

            const response =
                await fetch(
                    `${API_CONFIG.BASE_URL}/auth/refresh`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            refresh_token:
                                refreshToken
                        })
                    }
                );


            if (!response.ok) {

                return false;
            }


            const data =
                await response.json();


            if (
                !data?.access_token
            ) {

                return false;
            }


            localStorage.setItem(
                "ecolyy_access_token",
                data.access_token
            );


            if (
                data.refresh_token
            ) {

                localStorage.setItem(
                    "ecolyy_refresh_token",
                    data.refresh_token
                );

            }


            if (
                data.token_type
            ) {

                localStorage.setItem(
                    "ecolyy_token_type",
                    data.token_type
                );

            }


            if (
                data.role
            ) {

                localStorage.setItem(
                    "ecolyy_role",
                    data.role
                );

            }


            if (
                data.user
            ) {

                localStorage.setItem(
                    "ecolyy_user",
                    JSON.stringify(
                        data.user
                    )
                );

            }


            return true;


        } catch (error) {

            console.error(
                "Token refresh failed:",
                error
            );

            return false;
        }
    }

};


/* =========================================================
   AUTH HELPERS
   ========================================================= */

function getAuthToken() {

    return localStorage.getItem(
        "ecolyy_access_token"
    );
}


function saveAuthToken(token) {

    localStorage.setItem(
        "ecolyy_access_token",
        token
    );
}


function getRefreshToken() {

    return localStorage.getItem(
        "ecolyy_refresh_token"
    );
}


function saveRefreshToken(token) {

    localStorage.setItem(
        "ecolyy_refresh_token",
        token
    );
}


function getCurrentRole() {

    return (
        localStorage.getItem(
            "ecolyy_role"
        ) || ""
    ).toLowerCase();

}


function getCurrentUser() {

    try {

        return JSON.parse(
            localStorage.getItem(
                "ecolyy_user"
            )
        );

    } catch {

        return null;
    }
}


/* =========================================================
   LOGOUT
   ========================================================= */

function logout() {

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


    keys.forEach(
        key =>
            localStorage.removeItem(key)
    );


    window.location.href =
        "../pages/login.html";
}


/* =========================================================
   AUTH GUARD
   ========================================================= */

function requireAuth() {

    const token =
        getAuthToken();


    if (!token) {

        window.location.href =
            "../pages/login.html";

        return false;
    }


    return true;
}


/* =========================================================
   INSTITUTION GUARD
   ========================================================= */

function requireInstitution() {

    const token =
        getAuthToken();

    const role =
        getCurrentRole();


    if (
        !token ||
        role !== "institution"
    ) {

        logout();

        return false;
    }


    return true;
}

// =========================================================
// ADMIN PARTNERS
// =========================================================

    EcolyyAPI.getAdminPartners = function(skip = 0, limit = 50) {
    return this.get(`/admin/partners?skip=${skip}&limit=${limit}`);
};

    EcolyyAPI.verifyPartner = function(partnerId, verified = true) {
    return this.patch(`/admin/partners/${partnerId}/verify?verified=${verified}`);
};
