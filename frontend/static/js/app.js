(() => {
    "use strict";

    const initializeTooltips = () => {
        if (!window.bootstrap) return;
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((element) => {
            bootstrap.Tooltip.getOrCreateInstance(element, { trigger: "hover focus" });
        });
    };

    const initializeDeleteConfirmation = () => {
        const modalElement = document.getElementById("deleteConfirmModal");
        if (!modalElement || !window.bootstrap) return;

        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        const datasetName = document.getElementById("deleteDatasetName");
        const continueButton = document.getElementById("continueDelete");

        document.querySelectorAll("[data-bs-modal='delete-confirmation']").forEach((trigger) => {
            trigger.addEventListener("click", (event) => {
                if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
                event.preventDefault();
                if (datasetName) datasetName.textContent = trigger.dataset.datasetName || "";
                if (continueButton) continueButton.href = trigger.dataset.deleteUrl || trigger.href;
                modal.show();
            });
        });
    };

    const initializeSubmitFeedback = () => {
        document.querySelectorAll("form[data-submit-loading]").forEach((form) => {
            form.addEventListener("submit", (event) => {
                if (!form.checkValidity()) return;
                if (form.dataset.submitting === "true") {
                    event.preventDefault();
                    return;
                }

                form.dataset.submitting = "true";
                const submitButton = form.querySelector('button[type="submit"]');
                if (!submitButton) return;

                submitButton.disabled = true;
                submitButton.setAttribute("aria-busy", "true");
                const label = submitButton.querySelector(".button-label");
                const loading = submitButton.querySelector(".button-loading");
                if (label) label.classList.add("d-none");
                if (loading) loading.classList.remove("d-none");
            });
        });
    };

    const initializeFlashMessages = () => {
        document.querySelectorAll(".flash-toast[data-flash-category='success']").forEach((alert) => {
            window.setTimeout(() => {
                if (!alert.isConnected) return;
                if (window.bootstrap) {
                    bootstrap.Alert.getOrCreateInstance(alert).close();
                } else {
                    alert.remove();
                }
            }, 4700);
        });
    };

    const initializeScrollToTop = () => {
        const button = document.querySelector(".scroll-top");
        if (!button) return;

        const updateVisibility = () => {
            button.classList.toggle("is-visible", window.scrollY > 320);
        };
        window.addEventListener("scroll", updateVisibility, { passive: true });
        updateVisibility();
        button.addEventListener("click", () => {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    };

    document.addEventListener("DOMContentLoaded", () => {
        initializeTooltips();
        initializeDeleteConfirmation();
        initializeSubmitFeedback();
        initializeFlashMessages();
        initializeScrollToTop();
    });
})();
