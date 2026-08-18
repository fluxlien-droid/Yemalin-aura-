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

    if (!("PushManager" in window)) {
        console.log("Push non supporté.");
        return false;
    }

    try {

        // -------------------------------------------------
        // DEMANDER LA PERMISSION
        // -------------------------------------------------

        const permission =
            await Notification.requestPermission();

        if (permission !== "granted") {
            console.log("Permission refusée.");
            return false;
        }


        // -------------------------------------------------
        // SERVICE WORKER
        // -------------------------------------------------

        const registration =
            await navigator.serviceWorker.register(
                "/static/service-worker.js"
            );


        await navigator.serviceWorker.ready;


        // -------------------------------------------------
        // CLÉ VAPID
        // -------------------------------------------------

        const publicKey =
            window.VAPID_PUBLIC_KEY;

        if (!publicKey) {

            console.error(
                "VAPID_PUBLIC_KEY manquante."
            );

            return false;
        }


        // -------------------------------------------------
        // VÉRIFIER UNE SOUSCRIPTION EXISTANTE
        // -------------------------------------------------

        let subscription =
            await registration.pushManager.getSubscription();


        // -------------------------------------------------
        // CRÉER LA SOUSCRIPTION
        // -------------------------------------------------

        if (!subscription) {

            subscription =
                await registration.pushManager.subscribe({

                    userVisibleOnly: true,

                    applicationServerKey:
                        urlBase64ToUint8Array(
                            publicKey
                        )

                });

        }


        // -------------------------------------------------
        // ENVOYER AU SERVEUR FLASK
        // -------------------------------------------------

        const response =
            await fetch(
                "/api/push/subscribe",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials: "same-origin",

                    body: JSON.stringify({
                        subscription:
                            subscription.toJSON()
                    })
                }
            );


        if (!response.ok) {

            console.error(
                "Erreur serveur :",
                response.status
            );

            return false;
        }


        const result =
            await response.json();


        if (!result.ok) {

            console.error(
                result.message ||
                "Erreur d'abonnement."
            );

            return false;
        }


        console.log(
            "🔔 Notifications activées."
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
// CONVERSION CLÉ VAPID
// =====================================================

function urlBase64ToUint8Array(base64String) {

    const padding =
        "=".repeat(
            (4 - base64String.length % 4) % 4
        );

    const base64 =
        (
            base64String + padding
        )
        .replace(/-/g, "+")
        .replace(/_/g, "/");


    const rawData =
        window.atob(base64);


    return Uint8Array.from(
        [...rawData].map(
            char =>
                char.charCodeAt(0)
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

        if (
            typeof afficherNotification ===
            "function"
        ) {

            afficherNotification(
                "🔔 Notifications activées."
            );

        } else {

            alert(
                "🔔 Notifications activées."
            );

        }

    } else {

        if (
            typeof afficherNotification ===
            "function"
        ) {

            afficherNotification(
                "❌ Impossible d'activer les notifications."
            );

        }

    }
                    }
