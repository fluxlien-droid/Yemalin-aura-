"use strict";

/* =========================================================
   YEMALIN AURA — SERVICE WORKER
   Notifications Push
========================================================= */


/* =========================================================
   INSTALLATION
========================================================= */

self.addEventListener(
    "install",
    function(event) {

        self.skipWaiting();

    }
);


/* =========================================================
   ACTIVATION
========================================================= */

self.addEventListener(
    "activate",
    function(event) {

        event.waitUntil(
            self.clients.claim()
        );

    }
);


/* =========================================================
   RÉCEPTION D'UNE NOTIFICATION PUSH
========================================================= */

self.addEventListener(
    "push",
    function(event) {

        let data = {};

        try {

            if (event.data) {

                data =
                    event.data.json();

            }

        } catch (error) {

            console.error(
                "Erreur données Push:",
                error
            );

            data = {
                title: "Yemalin Aura",
                body: "Vous avez une nouvelle notification."
            };
        }


        const title =
            data.title ||
            "Yemalin Aura";


        const options = {

            body:
                data.body ||
                "Vous avez une nouvelle notification.",

            icon:
                data.icon ||
                "/static/logo.png",

            badge:
                data.badge ||
                "/static/logo.png",

            data: {
                url:
                    data.url ||
                    "/"
            },

            vibrate: [
                200,
                100,
                200
            ],

            tag:
                data.tag ||
                "yemalin-aura"
        };


        event.waitUntil(

            self.registration.showNotification(
                title,
                options
            )

        );

    }
);


/* =========================================================
   CLIC SUR LA NOTIFICATION
========================================================= */

self.addEventListener(
    "notificationclick",
    function(event) {

        event.notification.close();


        const url =
            event.notification.data?.url ||
            "/";


        event.waitUntil(

            clients.matchAll({
                type: "window",
                includeUncontrolled: true
            })
            .then(function(clientList) {

                for (
                    const client
                    of clientList
                ) {

                    if (
                        "focus" in client
                    ) {

                        client.navigate(url);

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

            })

        );

    }
);
