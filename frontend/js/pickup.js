/* =========================================================
   ReKart Pickup Management
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const pickupForm =
            document.getElementById("pickupForm");

        if (!pickupForm) return;

        pickupForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                const button =
                    pickupForm.querySelector(
                        "button[type='submit']"
                    );

                const originalText =
                    button?.innerHTML;

                if (button) {
                    button.disabled = true;
                    button.innerHTML =
                        "Scheduling...";
                }

                const formData =
                    new FormData(pickupForm);

                const payload = {

                    waste_category:
                        formData.get(
                            "waste_category"
                        ),

                    quantity:
                        formData.get("quantity"),

                    pickup_date:
                        formData.get(
                            "pickup_date"
                        ),

                    pickup_time:
                        formData.get(
                            "pickup_time"
                        ),

                    address:
                        formData.get("address"),

                    notes:
                        formData.get("notes") || ""
                };

                try {

                    const response =
                        await RekartAPI.post(
                            "/pickups",
                            payload
                        );

                    console.log(
                        "Pickup created:",
                        response
                    );

                    alert(
                        "Pickup scheduled successfully!"
                    );

                    pickupForm.reset();

                    window.location.href =
                        "pickups.html";

                } catch (error) {

                    alert(
                        error.message ||
                        "Unable to schedule pickup."
                    );

                } finally {

                    if (button) {
                        button.disabled = false;
                        button.innerHTML =
                            originalText;
                    }
                }
            }
        );
    }
);