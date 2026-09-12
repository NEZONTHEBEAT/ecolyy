/**
 * =========================================================
 * ECOLYY AUTHENTICATION
 * =========================================================
 *
 * Supports:
 * - Email / Password Login
 * - Google Login
 * - JWT storage
 * - Logout
 * - Access token
 * - Refresh token
 *
 * Backend:
 * http://127.0.0.1:8000
 */

"use strict";


/* =========================================================
   CONFIG
========================================================= */

const API_BASE_URL = "http://127.0.0.1:8000";


/*
 * IMPORTANT:
 * Replace this with your REAL Google Client ID.
 */

const GOOGLE_CLIENT_ID =
    "243474168990-90ci2ll2bpcn85lu9dd4lpipprhqbpr3.apps.googleusercontent.com";


/* =========================================================
   DOM ELEMENTS
========================================================= */

const loginForm =
    document.getElementById("loginForm");

const emailInput =
    document.getElementById("email");

const passwordInput =
    document.getElementById("password");

const googleLoginBtn =
    document.getElementById("googleLoginBtn");

const loginSubmitBtn =
    document.getElementById("loginSubmitBtn");


/* =========================================================
   API HELPER
========================================================= */

async function apiRequest(
    endpoint,
    options = {}
) {

    const response =
        await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                ...options,

                headers: {
                    "Content-Type":
                        "application/json",

                    ...(options.headers || {})
                }
            }
        );


    let data = {};

    try {

        data =
            await response.json();

    } catch {

        data = {};

    }


    if (!response.ok) {

        throw new Error(
            data.detail ||
            data.message ||
            "Request failed."
        );
    }


    return data;
}


/* =========================================================
   SAVE AUTH DATA
========================================================= */

function saveAuthData(data) {

    if (!data) {
        return;
    }


    if (data.access_token) {

        localStorage.setItem(
            "ecolyy_access_token",
            data.access_token
        );

    }


    if (data.refresh_token) {

        localStorage.setItem(
            "ecolyy_refresh_token",
            data.refresh_token
        );

    }


    if (data.token_type) {

        localStorage.setItem(
            "ecolyy_token_type",
            data.token_type
        );

    }


    if (data.role) {

        localStorage.setItem(
            "ecolyy_role",
            data.role
        );

    }


    if (data.user) {

        localStorage.setItem(
            "ecolyy_user",
            JSON.stringify(data.user)
        );

    }

}


/* =========================================================
   EMAIL / PASSWORD LOGIN
========================================================= */

if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const email =
                emailInput
                    ? emailInput.value.trim()
                    : "";


            const password =
                passwordInput
                    ? passwordInput.value
                    : "";


            if (!email || !password) {

                alert(
                    "Please enter your email and password."
                );

                return;
            }


            try {

                if (loginSubmitBtn) {

                    loginSubmitBtn.disabled =
                        true;

                    loginSubmitBtn.innerHTML =
                        "Logging in...";

                }


                const data =
                    await apiRequest(
                        "/api/v1/auth/login",
                        {
                            method: "POST",

                            body:
                                JSON.stringify({
                                    email,
                                    password,
                                    role: "user"
                                })
                        }
                    );


                console.log(
                    "Ecolyy Login:",
                    data
                );


                saveAuthData(data);


                if (data.role === "admin") {
                    window.location.href = "../admin/dashboard.html";
                } else {
                    window.location.href = "../user/dashboard.html";
                }


            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                alert(
                    error.message ||
                    "Login failed."
                );


                if (loginSubmitBtn) {

                    loginSubmitBtn.disabled =
                        false;

                    loginSubmitBtn.innerHTML =
                        'Login <i class="bi bi-arrow-right"></i>';

                }

            }

        }
    );

}


/* =========================================================
   GOOGLE LOGIN CALLBACK
========================================================= */

async function handleGoogleCredential(
    response
) {

    console.log(
        "Google credential received."
    );


    if (
        !response ||
        !response.credential
    ) {

        alert(
            "Google authentication failed."
        );

        return;
    }


    try {

        if (googleLoginBtn) {

            googleLoginBtn.disabled =
                true;

            googleLoginBtn.innerHTML =
                '<i class="bi bi-hourglass-split"></i> Signing in...';

        }


        /*
         * Send Google ID Token
         * to FastAPI.
         */

        const data =
            await apiRequest(
                "/api/v1/auth/google",
                {
                    method: "POST",

                    body:
                        JSON.stringify({

                            id_token:
                                response.credential,

                            role:
                                "user"

                        })
                }
            );


        console.log(
            "Ecolyy Google Login:",
            data
        );


        /*
         * Store Ecolyy JWT.
         */

        saveAuthData(data);


        /* =========================================================
        ROLE BASED REDIRECT
        ========================================================= */

        if (data.role === "admin") {

            window.location.href =
                "../admin/dashboard.html";

        } else {

            window.location.href =
                "../user/dashboard.html";

        }


    } catch (error) {

        console.error(
            "Google Login Error:",
            error
        );


        alert(
            error.message ||
            "Google login failed."
        );


        if (googleLoginBtn) {

            googleLoginBtn.disabled =
                false;

            googleLoginBtn.innerHTML =
                '<i class="bi bi-google"></i> Continue with Google';

        }

    }

}


/* =========================================================
   INITIALIZE GOOGLE IDENTITY SERVICES
========================================================= */

function initializeGoogleAuth() {

    if (
        typeof google === "undefined" ||
        !google.accounts ||
        !google.accounts.id
    ) {

        console.error(
            "Google Identity Services not loaded."
        );

        return;
    }


    /*
     * Initialize GIS.
     */

    google.accounts.id.initialize({

        client_id:
            GOOGLE_CLIENT_ID,

        callback:
            handleGoogleCredential,

        ux_mode:
            "popup",

        auto_select:
            false

    });


    console.log(
        "Google Identity Services initialized."
    );

}


/* =========================================================
   GOOGLE BUTTON
========================================================= */

if (googleLoginBtn) {

    googleLoginBtn.addEventListener(
        "click",
        function () {

            if (
                typeof google === "undefined" ||
                !google.accounts ||
                !google.accounts.id
            ) {

                alert(
                    "Google Sign-In is still loading. Please try again."
                );

                return;
            }


            /*
             * IMPORTANT:
             *
             * NEVER do:
             *
             * window.location.href =
             * "http://127.0.0.1:8000/api/v1/auth/google";
             *
             * That would send GET request.
             *
             * Our backend requires POST.
             */


            google.accounts.id.prompt();

        }
    );

}


/* =========================================================
   GET ACCESS TOKEN
========================================================= */

function getAccessToken() {

    return localStorage.getItem(
        "ecolyy_access_token"
    );

}


/* =========================================================
   GET REFRESH TOKEN
========================================================= */

function getRefreshToken() {

    return localStorage.getItem(
        "ecolyy_refresh_token"
    );

}


/* =========================================================
   GET CURRENT USER
========================================================= */

function getCurrentUser() {

    const user =
        localStorage.getItem(
            "ecolyy_user"
        );


    if (!user) {

        return null;

    }


    try {

        return JSON.parse(user);

    } catch {

        return null;

    }

}


/* =========================================================
   GET CURRENT ROLE
========================================================= */

function getCurrentRole() {

    return localStorage.getItem(
        "ecolyy_role"
    );

}


/* =========================================================
   CHECK AUTH
========================================================= */

function isLoggedIn() {

    return Boolean(
        getAccessToken()
    );

}


/* =========================================================
   AUTHENTICATED API REQUEST
========================================================= */

async function authenticatedFetch(
    endpoint,
    options = {}
) {

    const token =
        getAccessToken();


    if (!token) {

        window.location.href =
            "login.html";

        return;

    }


    const response =
        await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                ...options,

                headers: {

                    "Content-Type":
                        "application/json",

                    "Authorization":
                        `Bearer ${token}`,

                    ...(options.headers || {})

                }
            }
        );


    /*
     * Access token expired.
     */

    if (response.status === 401) {

        const refreshed =
            await refreshAccessToken();


        if (refreshed) {

            return authenticatedFetch(
                endpoint,
                options
            );

        }


        logout();

        return;

    }


    return response;

}


/* =========================================================
   REFRESH ACCESS TOKEN
========================================================= */

async function refreshAccessToken() {

    const refreshToken =
        getRefreshToken();


    if (!refreshToken) {

        return false;

    }


    try {

        const data =
            await apiRequest(
                "/api/v1/auth/refresh",
                {
                    method: "POST",

                    body:
                        JSON.stringify({
                            refresh_token:
                                refreshToken
                        })
                }
            );


        if (
            data &&
            data.access_token
        ) {

            localStorage.setItem(
                "ecolyy_access_token",
                data.access_token
            );


            return true;

        }


        return false;


    } catch (error) {

        console.error(
            "Token refresh failed:",
            error
        );


        return false;

    }

}


/* =========================================================
   LOGOUT
========================================================= */

function logout() {

    localStorage.removeItem(
        "ecolyy_access_token"
    );

    localStorage.removeItem(
        "ecolyy_refresh_token"
    );

    localStorage.removeItem(
        "ecolyy_token_type"
    );

    localStorage.removeItem(
        "ecolyy_role"
    );

    localStorage.removeItem(
        "ecolyy_user"
    );


    /*
     * Disable Google auto-select.
     */

    if (
        typeof google !== "undefined" &&
        google.accounts &&
        google.accounts.id
    ) {

        google.accounts.id.disableAutoSelect();

    }


    window.location.href =
        "login.html";

}


/* =========================================================
   INITIALIZE ON PAGE LOAD
========================================================= */

window.addEventListener(
    "load",
    function () {

        initializeGoogleAuth();

    }
);