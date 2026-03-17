document.addEventListener("DOMContentLoaded", () => {
    for (const button of document.querySelectorAll("[data-dismiss-flash]")) {
        button.addEventListener("click", () => {
            const flash = button.closest(".flash");
            if (flash) {
                flash.remove();
            }
        });
    }

    for (const form of document.querySelectorAll("[data-loading-form]")) {
        form.addEventListener("submit", () => {
            const submitButton = form.querySelector("button[type='submit']");
            if (!submitButton) {
                return;
            }
            submitButton.classList.add("is-loading");
            submitButton.setAttribute("disabled", "disabled");
        });
    }
});
