"use strict";

/*
=========================================================
 YEMALIN AURA — NOTIFICATIONS PUSH
=========================================================
*/


/* =====================================================
   CONVERTIR LA CLÉ VAPID
===================================================== */

function base64ToUint8Array(base64String) {

    const padding =
        "=".repeat(
            (4 - base64String.length % 4) % 4
        );

    const base64 =
        (
            base64String +
            padding
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


/* =====================================================
   ENREGISTRER LE SERVICE WORKER
===================================================== */

async function enregistrerServiceWorker() {

    if (!("serviceWorker" in navigator)) {

        throw new Error(
            "Les Service Workers ne sont pas supportés."
        );
    }


    return await navigator.serviceWorker.register(
        "/static/service-worker.js"
    );
}


/* =====================================================
   OBTENIR LA SOUSCRIPTION
===================================================== */

async function obtenirSubscription(
    registration
) {

    if (!("PushManager" in window)) {

        throw new Error(
            "Les notifications Push ne sont pas supportées."
        );
    }


    const vapidKey =
        window.VAPID_PUBLIC_KEY;


    if (!vapidKey) {

        throw new Error(
            "Clé VAPID publique absente."
        );
    }


    let subscription =
        await registration.pushManager
            .getSubscription();


    if (subscription) {

        return subscription;
    }


    subscription =
        await registration.pushManager.subscribe({

            userVisibleOnly: true,

            applicationServerKey:
                base64ToUint8Array(
                    vapidKey
                )
        });


    return subscription;
}


/* =====================================================
   ENVOYER LA SOUSCRIPTION AU SERVEUR
===================================================== */

async function envoyerSubscription(
    subscription
) {

    const response =
        await fetch(
            "/api/push/abonner",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                credentials:
                    "same-origin",

                body: JSON.stringify(
                    subscription
                )
            }
        );


    const data =
        await response.json();


    if (!response.ok || !data.ok) {

        throw new Error(
            data.message ||
            "Impossible d'enregistrer les notifications."
        );
    }


    return data;
}


/* =====================================================
   ACTIVER LES NOTIFICATIONS
===================================================== */

async function activerPush(
    registration = null
) {

    try {

        if (
            !("Notification" in window)
        ) {

            throw new Error(
                "Les notifications ne sont pas disponibles."
            );
        }


        if (
            Notification.permission !==
            "granted"
        ) {

            const permission =
                await Notification.requestPermission();


            if (
                permission !==
                "granted"
            ) {

                throw new Error(
                    "Permission de notification refusée."
                );
            }
        }


        if (!registration) {

            registration =
                await enregistrerServiceWorker();
        }


        const subscription =
            await obtenirSubscription(
                registration
            );


        await envoyerSubscription(
            subscription
        );


        if (
            typeof notify ===
            "function"
        ) {

            notify(
                "🔔 Notifications activées avec succès."
            );
        }


        return true;


    } catch (error) {

        console.error(
            "Push:",
            error
        );


        if (
            typeof notify ===
            "function"
        ) {

            notify(
                "❌ " +
                (
                    error.message ||
                    "Impossible d'activer les notifications."
                )
            );
        }


        return false;
    }
}


/* =====================================================
   EXPOSER LA FONCTION
===================================================== */

window.activerPush =
    activerPush;


/* =====================================================
   INITIALISATION
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    async function() {

        if (
            !("serviceWorker" in navigator) ||
            !("PushManager" in window)
        ) {

            return;
        }


        try {

            await enregistrerServiceWorker();

        } catch (error) {

            console.error(
                "Service Worker:",
                error
            );
        }

    }
);
