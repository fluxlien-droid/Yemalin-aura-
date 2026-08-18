// =====================================================
// YEMALIN AURA
// SERVICE WORKER — NOTIFICATIONS PUSH
// =====================================================

const CACHE_NAME =
    "yemalin-aura-v1";


// =====================================================
// INSTALLATION
// =====================================================

self.addEventListener(
    "install",
    event => {

        console.log(
            "Yemalin Aura Service Worker installé."
        );

        self.skipWaiting();

    }
);


// =====================================================
// ACTIVATION
// =====================================================

self.addEventListener(
    "activate",
    event => {

        event.waitUntil(
            self.clients.claim()
        );

    }
);


// =====================================================
// NOTIFICATION PUSH
// =====================================================

self.addEventListener(
    "push",
    event => {

        let data = {

            title:
                "Yemalin Aura",

            body:
                "Vous avez une nouvelle notification.",

            url:
                "/"

        };


        try {

            if (event.data) {

                const received =
                    event.data.json();

                data = {
                    ...data,
                    ...received
                };

            }

        } catch (error) {

            console.log(
                "Notification texte."
            );

            if (event.data) {

                data.body =
                    event.data.text();

            }

        }


        const options = {

            body:
                data.body,

            icon:
                data.icon
                || "/static/logo.png",

            badge:
                data.badge
                || "/static/logo.png",

            data: {

                url:
                    data.url || "/"

            },

            vibrate: [
                200,
                100,
                200
            ]

        };


        event.waitUntil(

            self.registration.showNotification(
                data.title,
                options
            )

        );

    }
);


// =====================================================
// CLIC SUR NOTIFICATION
// =====================================================

self.addEventListener(
    "notificationclick",
    event => {

        event.notification.close();


        const url =
            event.notification.data?.url
            || "/";


        event.waitUntil(

            clients.matchAll({

                type: "window",

                includeUncontrolled: true

            })

            .then(
                clientList => {

                    for (
                        const client
                        of clientList
                    ) {

                        if (
                            "focus"
                            in client
                        ) {

                            client.navigate(
                                url
                            );

                            return client.focus();

                        }

                    }


                    if (
                        clients.openWindow
                    ) {

                        return clients.openWindow(
                            url
                        );

                    }

                }
            )

        );

    }
);