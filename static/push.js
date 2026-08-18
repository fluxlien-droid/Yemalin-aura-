// =====================================================
// YEMALIN AURA — NOTIFICATIONS PUSH
// =====================================================

async function activerNotifications() {

    if (!("Notification" in window)) {
        console.log("Notifications non supportées.");
        return false;
    }

    if (!("serviceWorker" in navigator)) {
        console.log("Service Worker non supporté.");
        return false;
    }

    try {

        const permission =
            await Notification.requestPermission();

        if (permission !== "granted") {
            console.log("Permission refusée.");
            return false;
        }

        const registration =
            await navigator.serviceWorker.register(
                "/static/service-worker.js"
            );

        const publicKey =
            window.VAPID_PUBLIC_KEY;

        if (!publicKey) {
            console.error(
                "VAPID_PUBLIC_KEY manquante."
            );
            return false;
        }

        const subscription =
            await registration.pushManager.subscribe({

                userVisibleOnly: true,

                applicationServerKey:
                    urlBase64ToUint8Array(
                        publicKey
                    )

            });

        const response =
            await fetch(
                "/api/push/subscribe",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        subscription:
                            subscription.toJSON()
                    })
                }
            );

        const result =
            await response.json();

        if (!result.ok) {
            console.error(result.message);
            return false;
        }

        console.log(
            "Notifications activées."
        );

        return true;

    } catch (error) {

        console.error(
            "Erreur notifications :",
            error
        );

        return false;
    }
}


// =====================================================
// CONVERSION VAPID
// =====================================================

function urlBase64ToUint8Array(base64String) {

    const padding =
        "=".repeat(
            (4 - base64String.length % 4) % 4
        );

    const base64 =
        (
            base64String
            + padding
        )
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const rawData =
        window.atob(base64);

    return Uint8Array.from(
        [...rawData].map(
            char => char.charCodeAt(0)
        )
    );
}


// =====================================================
// BOUTON NOTIFICATIONS
// =====================================================

async function demanderNotifications() {

    const active =
        await activerNotifications();

    if (active) {

        if (typeof afficherNotification === "function") {

            afficherNotification(
                "🔔 Notifications activées."
            );

        } else {

            alert(
                "🔔 Notifications activées."
            );

        }

    }

}


// =====================================================
// INITIALISATION
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        if (
            "serviceWorker"
            in navigator
        ) {

            navigator.serviceWorker.register(
                "/static/service-worker.js"
            )
            .catch(error => {

                console.error(
                    "Service Worker :",
                    error
                );

            });

        }

    }
);