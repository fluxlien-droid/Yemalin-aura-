/* =========================================================
   YEMALIN AURA — SCRIPT PRINCIPAL
   VERSION CORRIGÉE — PARTIE 1/5
========================================================= */

"use strict";


/* =========================================================
   VARIABLES
========================================================= */

let panier = [];

let commandeActuelle = null;


/* =========================================================
   CHARGEMENT DU PANIER
========================================================= */

try {

    const panierSauvegarde =
        localStorage.getItem("yemalin_panier");

    panier =
        panierSauvegarde
            ? JSON.parse(panierSauvegarde)
            : [];

    if (!Array.isArray(panier)) {
        panier = [];
    }

} catch (error) {

    console.error(
        "Erreur chargement panier :",
        error
    );

    panier = [];

}


/* =========================================================
   OUTILS
========================================================= */

function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/* =========================================================
   NOTIFICATION
========================================================= */

function notify(message) {

    const box =
        document.getElementById(
            "notification"
        );


    if (!box) {

        alert(message);

        return;
    }


    box.textContent =
        String(message);


    box.classList.add("show");


    clearTimeout(
        window.yemalinNotificationTimer
    );


    window.yemalinNotificationTimer =
        setTimeout(
            function() {

                box.classList.remove(
                    "show"
                );

            },
            3000
        );
}


/* =========================================================
   SAUVEGARDER LE PANIER
========================================================= */

function sauvegarderPanier() {

    try {

        localStorage.setItem(
            "yemalin_panier",
            JSON.stringify(panier)
        );

    } catch (error) {

        console.error(
            "Erreur sauvegarde panier :",
            error
        );

    }
}


/* =========================================================
   NAVIGATION
========================================================= */

function ouvrirPage(pageId) {

    document
        .querySelectorAll(".page")
        .forEach(
            function(page) {

                page.classList.remove(
                    "active"
                );

            }
        );


    const page =
        document.getElementById(
            pageId
        );


    if (!page) {

        console.warn(
            "Page introuvable :",
            pageId
        );

        return;
    }


    page.classList.add(
        "active"
    );


    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });


    /* -----------------------------------------
       Actions selon la page
    ----------------------------------------- */

    if (
        pageId === "commandes"
    ) {

        chargerCommandesClient();

    }


    if (
        pageId === "panier"
    ) {

        afficherPanier();

    }


    if (
        pageId === "messages"
    ) {

        /*
         * Les messages généraux sont envoyés
         * directement à l'administration.
         *
         * Il n'est donc pas nécessaire de
         * charger une liste ici.
         */

    }


    if (
        pageId === "chat"
        &&
        commandeActuelle
    ) {

        chargerChatClient(
            commandeActuelle
        );

    }

}


/* =========================================================
   ALLER AUX PRODUITS
========================================================= */

function allerProduits() {

    const section =
        document.querySelector(
            ".products-section"
        );


    if (!section) {
        return;
    }


    section.scrollIntoView({

        behavior: "smooth",

        block: "start"

    });

}


/* =========================================================
   PANIER — AJOUTER
========================================================= */

function ajouterPanier(produit) {

    if (!produit) {

        notify(
            "❌ Produit invalide."
        );

        return;
    }


    const id =
        Number(produit.id);


    if (!id) {

        notify(
            "❌ Identifiant du produit invalide."
        );

        return;
    }


    const prix =
        Number(produit.prix || 0);


    const nom =
        String(
            produit.nom || "Produit"
        );


    const existant =
        panier.find(
            function(item) {

                return Number(item.id) === id;

            }
        );


    if (existant) {

        existant.quantite =
            Number(
                existant.quantite || 0
            ) + 1;

    } else {

        panier.push({

            id: id,

            nom: nom,

            prix: prix,

            quantite: 1

        });

    }


    sauvegarderPanier();

    afficherPanier();


    notify(
        "🛒 Produit ajouté au panier."
    );
}


/* =========================================================
   PANIER — RETIRER
========================================================= */

function retirerPanier(id) {

    panier =
        panier.filter(
            function(item) {

                return Number(item.id) !==
                    Number(id);

            }
        );


    sauvegarderPanier();

    afficherPanier();


    notify(
        "🗑️ Produit retiré du panier."
    );
}


/* =========================================================
   PANIER — MODIFIER QUANTITÉ
========================================================= */

function modifierQuantite(
    id,
    changement
) {

    const produit =
        panier.find(
            function(item) {

                return Number(item.id) ===
                    Number(id);

            }
        );


    if (!produit) {
        return;
    }


    produit.quantite =
        Number(
            produit.quantite || 0
        ) +
        Number(changement || 0);


    if (
        produit.quantite <= 0
    ) {

        retirerPanier(id);

        return;
    }


    sauvegarderPanier();

    afficherPanier();
}


/* =========================================================
   PANIER — VIDER
========================================================= */

function viderPanier() {

    panier = [];


    sauvegarderPanier();

    afficherPanier();


    notify(
        "🛒 Panier vidé."
    );
}


/* =========================================================
   PANIER — TOTAL
========================================================= */

function calculerTotal() {

    return panier.reduce(

        function(total, item) {

            return total +
                (
                    Number(item.prix || 0) *
                    Number(item.quantite || 0)
                );

        },

        0

    );
}


/* =========================================================
   PANIER — NOMBRE D'ARTICLES
========================================================= */

function nombreArticles() {

    return panier.reduce(

        function(total, item) {

            return total +
                Number(
                    item.quantite || 0
                );

        },

        0

    );
}


/* =========================================================
   PANIER — AFFICHAGE
========================================================= */

function afficherPanier() {

    const compteur =
        document.getElementById(
            "compteur"
        );


    const compteurRapide =
        document.getElementById(
            "compteur-rapide"
        );


    const contenu =
        document.getElementById(
            "contenu-panier"
        );


    const total =
        document.getElementById(
            "total"
        );


    const nombre =
        nombreArticles();


    if (compteur) {

        compteur.textContent =
            nombre;

    }


    if (compteurRapide) {

        compteurRapide.textContent =
            nombre;

    }


    if (total) {

        total.textContent =
            calculerTotal()
                .toLocaleString(
                    "fr-FR"
                );

    }


    if (!contenu) {
        return;
    }


    if (!panier.length) {

        contenu.innerHTML = `

            <div class="empty-state">

                <p>
                    🛒 Votre panier est vide.
                </p>

                <button
                    type="button"
                    class="btn"
                    onclick="
                        ouvrirPage('accueil')
                    "
                >
                    Découvrir les produits
                </button>

            </div>

        `;

        return;
    }


    contenu.innerHTML =
        panier.map(

            function(item) {

                const prix =
                    Number(
                        item.prix || 0
                    );


                const quantite =
                    Number(
                        item.quantite || 1
                    );


                const sousTotal =
                    prix * quantite;


                return `

                    <article
                        class="cart-item"
                    >

                        <div
                            class="cart-item-info"
                        >

                            <h3>
                                ${escapeHtml(
                                    item.nom
                                )}
                            </h3>

                            <p>
                                ${prix.toLocaleString(
                                    "fr-FR"
                                )}
                                FCFA / unité
                            </p>

                        </div>


                        <div
                            class="cart-quantity"
                        >

                            <button
                                type="button"
                                onclick="
                                    modifierQuantite(
                                        ${Number(item.id)},
                                        -1
                                    )
                                "
                            >
                                −
                            </button>


                            <strong>
                                ${quantite}
                            </strong>


                            <button
                                type="button"
                                onclick="
                                    modifierQuantite(
                                        ${Number(item.id)},
                                        1
                                    )
                                "
                            >
                                +
                            </button>

                        </div>


                        <strong
                            class="cart-subtotal"
                        >

                            ${sousTotal.toLocaleString(
                                "fr-FR"
                            )}

                            FCFA

                        </strong>


                        <button
                            type="button"
                            class="btn"
                            onclick="
                                retirerPanier(
                                    ${Number(item.id)}
                                )
                            "
                        >
                            🗑️
                        </button>

                    </article>

                `;

            }

        ).join("");


    contenu.innerHTML += `

        <button
            type="button"
            class="btn"
            onclick="viderPanier()"
        >
            🗑️ Vider le panier
        </button>

    `;
}


/* =========================================================
   OUVRIR LE PANIER
========================================================= */

function ouvrirPanier() {

    ouvrirPage(
        "panier"
    );

    afficherPanier();
}
/* =========================================================
   PASSER UNE COMMANDE
========================================================= */

async function passerCommande() {

    if (!panier.length) {

        notify(
            "🛒 Votre panier est vide."
        );

        return;
    }


    const nom =
        document
            .getElementById("client-nom")
            ?.value
            .trim();


    const telephone =
        document
            .getElementById("telephone")
            ?.value
            .trim();


    const adresse =
        document
            .getElementById("adresse")
            ?.value
            .trim();


    if (!nom) {

        notify(
            "Veuillez entrer votre nom."
        );

        return;
    }


    if (!telephone) {

        notify(
            "Veuillez entrer votre numéro de téléphone."
        );

        return;
    }


    if (!adresse) {

        notify(
            "Veuillez entrer votre lieu de livraison."
        );

        return;
    }


    const bouton =
        document.querySelector(
            "#panier .card .btn"
        );


    if (bouton) {

        bouton.disabled = true;

        bouton.textContent =
            "⏳ Envoi...";

    }


    try {

        const produits =
            panier.map(
                function(item) {

                    return {

                        id:
                            Number(item.id),

                        quantite:
                            Number(
                                item.quantite
                            )

                    };

                }
            );


        const response =
            await fetch(
                "/api/commande",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            client_nom:
                                nom,

                            telephone:
                                telephone,

                            adresse:
                                adresse,

                            produits:
                                produits

                        })

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "Réponse invalide du serveur."
            );

        }


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "Impossible d'enregistrer la commande."
            );

        }


        /*
         * Flask renvoie commande_id.
         */

        commandeActuelle =
            data.commande_id
            ? Number(
                data.commande_id
            )
            : null;


        panier = [];


        sauvegarderPanier();

        afficherPanier();


        /*
         * Vider les champs.
         */

        const champNom =
            document.getElementById(
                "client-nom"
            );


        const champTelephone =
            document.getElementById(
                "telephone"
            );


        const champAdresse =
            document.getElementById(
                "adresse"
            );


        if (champNom) {
            champNom.value = "";
        }


        if (champTelephone) {
            champTelephone.value = "";
        }


        if (champAdresse) {
            champAdresse.value = "";
        }


        notify(
            "✅ Commande envoyée avec succès."
        );


        ouvrirPage(
            "commandes"
        );


        chargerCommandesClient();


    } catch (error) {

        console.error(
            "Erreur commande :",
            error
        );


        notify(
            "❌ " +
            (
                error.message ||
                "Erreur de connexion."
            )
        );


    } finally {

        if (bouton) {

            bouton.disabled =
                false;

            bouton.textContent =
                "✅ Passer la commande";

        }

    }
}


/* =========================================================
   COMMANDES DU CLIENT
========================================================= */

async function chargerCommandesClient() {

    const container =
        document.getElementById(
            "liste-commandes"
        );


    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="loading">
            Chargement des commandes...
        </div>

    `;


    try {

        const response =
            await fetch(
                "/api/mes-commandes",
                {

                    method: "GET",

                    credentials:
                        "same-origin",

                    cache: "no-store"

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "Réponse invalide du serveur."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Impossible de charger les commandes."
            );

        }


        const commandes =
            Array.isArray(data)
                ? data
                : (
                    Array.isArray(
                        data.commandes
                    )
                    ? data.commandes
                    : []
                );


        if (!commandes.length) {

            container.innerHTML = `

                <div
                    class="empty-state"
                >

                    <div>
                        📦
                    </div>

                    <h3>
                        Aucune commande
                    </h3>

                    <p>
                        Vous n'avez encore
                        aucune commande.
                    </p>

                </div>

            `;

            return;
        }


        container.innerHTML =
            commandes.map(

                function(commande) {

                    const id =
                        Number(
                            commande.id || 0
                        );


                    const total =
                        Number(
                            commande.total || 0
                        );


                    const statut =
                        escapeHtml(
                            commande.statut ||
                            "Nouvelle"
                        );


                    const date =
                        escapeHtml(
                            commande.date ||
                            ""
                        );


                    return `

                        <article
                            class="order-card"
                        >

                            <h3>
                                📦 Commande #${id}
                            </h3>


                            <p>

                                <strong>
                                    Total :
                                </strong>

                                ${total.toLocaleString(
                                    "fr-FR"
                                )}

                                FCFA

                            </p>


                            <p>

                                <strong>
                                    Statut :
                                </strong>

                                ${statut}

                            </p>


                            <p>

                                <small>
                                    ${date}
                                </small>

                            </p>


                            <button
                                type="button"
                                class="btn"
                                onclick="
                                    ouvrirChatClient(
                                        ${id}
                                    )
                                "
                            >
                                💬 Ouvrir le chat
                            </button>

                        </article>

                    `;

                }

            ).join("");


    } catch (error) {

        console.error(
            "Erreur commandes :",
            error
        );


        container.innerHTML = `

            <div class="error">

                ❌ Impossible de charger
                vos commandes.

                <br><br>

                ${escapeHtml(
                    error.message ||
                    "Erreur inconnue."
                )}

            </div>

        `;

    }
}


/* =========================================================
   OUVRIR LE CHAT D'UNE COMMANDE
========================================================= */

async function ouvrirChatClient(
    commandeId
) {

    const id =
        Number(commandeId);


    if (!id) {

        notify(
            "❌ Commande invalide."
        );

        return;
    }


    commandeActuelle =
        id;


    ouvrirPage(
        "chat"
    );


    await chargerChatClient(
        id
    );
}


/* =========================================================
   CHARGER LE CHAT CLIENT
========================================================= */

async function chargerChatClient(
    commandeId
) {

    const id =
        Number(commandeId);


    const messagesContainer =
        document.getElementById(
            "chat-messages"
        );


    const info =
        document.getElementById(
            "chat-info"
        );


    if (!messagesContainer) {
        return;
    }


    messagesContainer.innerHTML = `

        <div class="loading">
            Chargement du chat...
        </div>

    `;


    try {

        const response =
            await fetch(
                `/api/chat/${id}`,
                {

                    method: "GET",

                    credentials:
                        "same-origin",

                    cache: "no-store"

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "Réponse invalide du serveur."
            );

        }


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "Chat indisponible."
            );

        }


        if (info) {

            info.innerHTML = `

                <strong>
                    💬 Chat de la commande #${id}
                </strong>

            `;

        }


        const messages =
            Array.isArray(
                data.messages
            )
            ? data.messages
            : [];


        if (!messages.length) {

            messagesContainer.innerHTML = `

                <div
                    class="empty-state"
                >

                    <div>
                        💬
                    </div>

                    <p>
                        Aucun message pour le moment.
                    </p>

                    <small>
                        Écrivez votre message
                        ci-dessous.
                    </small>

                </div>

            `;

            return;
        }


        messagesContainer.innerHTML =
            messages.map(

                function(message) {

                    const estAdmin =
                        String(
                            message.auteur || ""
                        ).toLowerCase()
                        === "admin";


                    const auteur =
                        estAdmin
                            ? "👨‍💼 Administration"
                            : "👤 Vous";


                    return `

                        <div
                            class="
                                message-bubble
                                ${
                                    estAdmin
                                    ? "message-admin"
                                    : "message-client"
                                }
                            "
                        >

                            <strong>
                                ${auteur}
                            </strong>


                            <p>
                                ${escapeHtml(
                                    message.message
                                )}
                            </p>


                            <small>
                                ${escapeHtml(
                                    message.date ||
                                    ""
                                )}
                            </small>

                        </div>

                    `;

                }

            ).join("");


        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;


    } catch (error) {

        console.error(
            "Erreur chat :",
            error
        );


        messagesContainer.innerHTML = `

            <div class="error">

                ❌ ${escapeHtml(
                    error.message ||
                    "Erreur de chargement du chat."
                )}

            </div>

        `;

    }
}


/* =========================================================
   ENVOYER UN MESSAGE DANS LE CHAT
========================================================= */

async function envoyerChat() {

    if (!commandeActuelle) {

        notify(
            "Aucune commande sélectionnée."
        );

        return;
    }


    const input =
        document.getElementById(
            "chat-message"
        );


    if (!input) {

        notify(
            "Champ de message introuvable."
        );

        return;
    }


    const message =
        input.value.trim();


    if (!message) {

        notify(
            "Écrivez un message."
        );

        input.focus();

        return;
    }


    if (message.length > 2000) {

        notify(
            "Le message est trop long."
        );

        return;
    }


    input.disabled = true;


    try {

        const response =
            await fetch(
                `/api/chat/${Number(
                    commandeActuelle
                )}`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            message:
                                message

                        })

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "Réponse invalide du serveur."
            );

        }


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "Message non envoyé."
            );

        }


        input.value = "";


        notify(
            "✅ Message envoyé."
        );


        await chargerChatClient(
            commandeActuelle
        );


    } catch (error) {

        console.error(
            "Erreur envoi chat :",
            error
        );


        notify(
            "❌ " +
            (
                error.message ||
                "Erreur d'envoi."
            )
        );


    } finally {

        input.disabled = false;

        input.focus();

    }
                           }
/* =========================================================
   YEMALIN AURA — SCRIPT PRINCIPAL
   PARTIE 3/5
   MESSAGES GÉNÉRAUX + NOTIFICATIONS
========================================================= */


/* =========================================================
   ENVOYER UN MESSAGE GÉNÉRAL
========================================================= */

async function envoyerMessageGeneral() {

    const champNom =
        document.getElementById(
            "message-nom"
        );


    const champMessage =
        document.getElementById(
            "message-general"
        );


    if (!champNom || !champMessage) {

        notify(
            "❌ Formulaire de message introuvable."
        );

        return;
    }


    const nom =
        champNom.value.trim();


    const message =
        champMessage.value.trim();


    if (!nom) {

        notify(
            "Veuillez entrer votre nom."
        );

        champNom.focus();

        return;
    }


    if (!message) {

        notify(
            "Veuillez écrire votre message."
        );

        champMessage.focus();

        return;
    }


    if (message.length > 3000) {

        notify(
            "❌ Votre message est trop long."
        );

        return;
    }


    const bouton =
        document.querySelector(
            "#messages .btn"
        );


    if (bouton) {

        bouton.disabled = true;

        bouton.textContent =
            "⏳ Envoi...";

    }


    try {

        /*
         * IMPORTANT :
         *
         * Cette URL correspond exactement
         * à la route Flask :
         *
         * @app.route(
         *     "/api/messages-general",
         *     methods=["POST"]
         * )
         */

        const response =
            await fetch(
                "/api/messages-general",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({

                            nom:
                                nom,

                            message:
                                message

                        })

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "Réponse invalide du serveur."
            );

        }


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "Impossible d'envoyer le message."
            );

        }


        /*
         * Nettoyer uniquement le message.
         */

        champMessage.value = "";


        notify(
            "✅ Message envoyé à l'administration."
        );


    } catch (error) {

        console.error(
            "Erreur message général :",
            error
        );


        notify(
            "❌ " +
            (
                error.message ||
                "Erreur de connexion."
            )
        );


    } finally {

        if (bouton) {

            bouton.disabled =
                false;

            bouton.textContent =
                "Envoyer le message";

        }

    }
}


/* =========================================================
   VÉRIFIER LES NOTIFICATIONS
========================================================= */

async function demanderNotifications() {

    /*
     * Vérifier si le navigateur supporte
     * les notifications.
     */

    if (
        !("Notification" in window)
    ) {

        notify(
            "❌ Les notifications ne sont pas supportées par ce navigateur."
        );

        return;
    }


    /*
     * Vérifier si HTTPS est utilisé.
     *
     * localhost est également autorisé
     * par les navigateurs.
     */

    const securise =
        window.isSecureContext ||
        location.hostname === "localhost" ||
        location.hostname === "127.0.0.1";


    if (!securise) {

        notify(
            "❌ Les notifications nécessitent une connexion HTTPS."
        );

        return;
    }


    try {

        /*
         * Demander l'autorisation.
         */

        let permission =
            Notification.permission;


        if (
            permission === "default"
        ) {

            permission =
                await Notification.requestPermission();

        }


        if (
            permission !== "granted"
        ) {

            if (
                permission === "denied"
            ) {

                notify(
                    "🔕 Les notifications sont bloquées dans votre navigateur."
                );

            } else {

                notify(
                    "🔕 Les notifications n'ont pas été autorisées."
                );

            }

            return;
        }


        /*
         * Si push.js existe, lui laisser
         * gérer l'abonnement Push.
         */

        if (
            typeof window.abonnerNotifications ===
            "function"
        ) {

            try {

                await window.abonnerNotifications();

                notify(
                    "🔔 Notifications activées."
                );

                return;

            } catch (pushError) {

                console.error(
                    "Erreur abonnement Push :",
                    pushError
                );

            }
        }


        /*
         * Si aucune fonction Push n'est disponible,
         * on vérifie simplement que l'autorisation
         * navigateur est active.
         */

        notify(
            "🔔 Notifications autorisées sur cet appareil."
        );


    } catch (error) {

        console.error(
            "Erreur notifications :",
            error
        );


        notify(
            "❌ Impossible d'activer les notifications."
        );

    }
}


/* =========================================================
   TESTER UNE NOTIFICATION LOCALE
========================================================= */

function testerNotification() {

    if (
        !("Notification" in window)
    ) {

        notify(
            "❌ Notifications non supportées."
        );

        return;
    }


    if (
        Notification.permission !==
        "granted"
    ) {

        notify(
            "🔔 Activez d'abord les notifications."
        );

        return;
    }


    try {

        new Notification(
            "Yemalin Aura",
            {

                body:
                    "Les notifications fonctionnent correctement.",

                icon:
                    "/static/logo.png"

            }
        );

    } catch (error) {

        console.error(
            "Erreur notification test :",
            error
        );

        notify(
            "❌ Impossible d'afficher la notification."
        );

    }
}


/* =========================================================
   RETOUR À L'ACCUEIL
========================================================= */

function retourAccueil() {

    ouvrirPage(
        "accueil"
    );

}


/* =========================================================
   FERMER LE CHAT
========================================================= */

function fermerChat() {

    commandeActuelle =
        null;


    ouvrirPage(
        "commandes"
    );

}


/* =========================================================
   ACTUALISER LES COMMANDES
========================================================= */

async function actualiserCommandes() {

    await chargerCommandesClient();

}


/* =========================================================
   ACTUALISER LE CHAT
========================================================= */

async function actualiserChat() {

    if (
        !commandeActuelle
    ) {
        return;
    }


    await chargerChatClient(
        commandeActuelle
    );

}


/* =========================================================
   PROTECTION CONTRE LES ERREURS JAVASCRIPT
========================================================= */

window.addEventListener(
    "error",
    function(event) {

        console.error(
            "Erreur JavaScript :",
            event.error ||
            event.message
        );

    }
);


/* =========================================================
   ERREURS DES PROMESSES
========================================================= */

window.addEventListener(
    "unhandledrejection",
    function(event) {

        console.error(
            "Promise non gérée :",
            event.reason
        );

    }
);
/* =========================================================
   YEMALIN AURA — SCRIPT PRINCIPAL
   PARTIE 4/5
   ACTUALISATION + INITIALISATION
========================================================= */


/* =========================================================
   ACTUALISATION AUTOMATIQUE DU CHAT
========================================================= */

let intervalChat = null;


function demarrerActualisationChat() {

    /*
     * Éviter de créer plusieurs intervalles.
     */

    if (intervalChat) {
        clearInterval(intervalChat);
    }


    intervalChat = setInterval(
        async function() {

            /*
             * Vérifier qu'une commande est
             * actuellement ouverte.
             */

            if (!commandeActuelle) {
                return;
            }


            /*
             * Vérifier que la page Chat
             * est actuellement affichée.
             */

            const pageChat =
                document.getElementById(
                    "chat"
                );


            if (
                !pageChat ||
                !pageChat.classList.contains(
                    "active"
                )
            ) {

                return;
            }


            try {

                await chargerChatClient(
                    commandeActuelle
                );

            } catch (error) {

                console.error(
                    "Actualisation chat :",
                    error
                );

            }

        },
        5000
    );
}


/* =========================================================
   ARRÊTER L'ACTUALISATION DU CHAT
========================================================= */

function arreterActualisationChat() {

    if (intervalChat) {

        clearInterval(
            intervalChat
        );

        intervalChat = null;

    }
}


/* =========================================================
   ACTUALISATION DES COMMANDES
========================================================= */

let intervalCommandes = null;


function demarrerActualisationCommandes() {

    if (intervalCommandes) {

        clearInterval(
            intervalCommandes
        );

    }


    intervalCommandes =
        setInterval(
            async function() {

                const pageCommandes =
                    document.getElementById(
                        "commandes"
                    );


                /*
                 * Ne pas faire de requête
                 * si la page n'est pas visible.
                 */

                if (
                    !pageCommandes ||
                    !pageCommandes.classList.contains(
                        "active"
                    )
                ) {

                    return;
                }


                try {

                    await chargerCommandesClient();

                } catch (error) {

                    console.error(
                        "Actualisation commandes :",
                        error
                    );

                }

            },
            15000
        );
}


/* =========================================================
   ARRÊTER ACTUALISATION COMMANDES
========================================================= */

function arreterActualisationCommandes() {

    if (intervalCommandes) {

        clearInterval(
            intervalCommandes
        );

        intervalCommandes = null;

    }
}


/* =========================================================
   VÉRIFIER L'ÉTAT DE LA CONNEXION
========================================================= */

async function verifierConnexion() {

    try {

        const response =
            await fetch(
                "/api/status",
                {
                    method: "GET",
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            console.warn(
                "API status indisponible."
            );

            return false;
        }


        return true;


    } catch (error) {

        console.error(
            "Connexion serveur :",
            error
        );

        return false;
    }
}


/* =========================================================
   CHARGEMENT INITIAL DES DONNÉES
========================================================= */

async function chargerDonneesInitiales() {

    /*
     * Toujours afficher le panier
     * même si l'API n'est pas disponible.
     */

    try {

        afficherPanier();

    } catch (error) {

        console.error(
            "Panier :",
            error
        );

    }


    /*
     * Charger les commandes uniquement
     * si le conteneur existe.
     */

    try {

        const listeCommandes =
            document.getElementById(
                "liste-commandes"
            );


        if (listeCommandes) {

            await chargerCommandesClient();

        }

    } catch (error) {

        console.error(
            "Commandes initiales :",
            error
        );

    }


    /*
     * Démarrer les actualisations.
     */

    demarrerActualisationChat();

    demarrerActualisationCommandes();

}


/* =========================================================
   GESTION DU FORMULAIRE DE MESSAGE
========================================================= */

function initialiserFormulaireMessage() {

    const formulaire =
        document.getElementById(
            "form-message-general"
        );


    if (!formulaire) {
        return;
    }


    /*
     * Éviter de connecter deux fois
     * le même formulaire.
     */

    if (
        formulaire.dataset.initialise ===
        "true"
    ) {

        return;

    }


    formulaire.dataset.initialise =
        "true";


    formulaire.addEventListener(
        "submit",
        function(event) {

            event.preventDefault();

            envoyerMessageGeneral();

        }
    );

}


/* =========================================================
   BOUTON ENVOYER MESSAGE
========================================================= */

function initialiserBoutonMessage() {

    const bouton =
        document.getElementById(
            "btn-envoyer-message"
        );


    if (!bouton) {
        return;
    }


    if (
        bouton.dataset.initialise ===
        "true"
    ) {

        return;

    }


    bouton.dataset.initialise =
        "true";


    bouton.addEventListener(
        "click",
        function(event) {

            event.preventDefault();

            envoyerMessageGeneral();

        }
    );

}


/* =========================================================
   BOUTON NOTIFICATIONS
========================================================= */

function initialiserBoutonNotifications() {

    const bouton =
        document.getElementById(
            "btn-notifications"
        );


    if (!bouton) {
        return;
    }


    if (
        bouton.dataset.initialise ===
        "true"
    ) {

        return;

    }


    bouton.dataset.initialise =
        "true";


    bouton.addEventListener(
        "click",
        function(event) {

            event.preventDefault();

            demanderNotifications();

        }
    );

}


/* =========================================================
   ENTRÉE CLAVIER POUR LE CHAT
========================================================= */

function initialiserChatClavier() {

    const input =
        document.getElementById(
            "chat-message"
        );


    if (!input) {
        return;
    }


    if (
        input.dataset.initialise ===
        "true"
    ) {

        return;

    }


    input.dataset.initialise =
        "true";


    input.addEventListener(
        "keydown",
        function(event) {

            /*
             * Entrée = envoyer
             *
             * Shift + Entrée =
             * nouvelle ligne.
             */

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                envoyerChat();

            }

        }
    );

}


/* =========================================================
   BOUTON ENVOYER CHAT
========================================================= */

function initialiserBoutonChat() {

    const bouton =
        document.getElementById(
            "btn-envoyer-chat"
        );


    if (!bouton) {
        return;
    }


    if (
        bouton.dataset.initialise ===
        "true"
    ) {

        return;

    }


    bouton.dataset.initialise =
        "true";


    bouton.addEventListener(
        "click",
        function(event) {

            event.preventDefault();

            envoyerChat();

        }
    );

}


/* =========================================================
   FORMULAIRE COMMANDE
========================================================= */

function initialiserFormulaireCommande() {

    const formulaire =
        document.getElementById(
            "form-commande"
        );


    if (!formulaire) {
        return;
    }


    if (
        formulaire.dataset.initialise ===
        "true"
    ) {

        return;

    }


    formulaire.dataset.initialise =
        "true";


    formulaire.addEventListener(
        "submit",
        function(event) {

            event.preventDefault();

            passerCommande();

        }
    );

}


/* =========================================================
   INITIALISER TOUS LES ÉVÉNEMENTS
========================================================= */

function initialiserEvenements() {

    initialiserFormulaireMessage();

    initialiserBoutonMessage();

    initialiserBoutonNotifications();

    initialiserChatClavier();

    initialiserBoutonChat();

    initialiserFormulaireCommande();

}


/* =========================================================
   DOM READY
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    async function() {

        console.log(
            "✅ Yemalin Aura : script chargé."
        );


        /*
         * Initialiser les boutons
         * et formulaires.
         */

        initialiserEvenements();


        /*
         * Charger les données.
         */

        await chargerDonneesInitiales();


        /*
         * Vérifier le panier une dernière fois.
         */

        try {

            afficherPanier();

        } catch (error) {

            console.error(
                "Initialisation panier :",
                error
            );

        }

    }
);


/* =========================================================
   PAGE VISIBILITY
========================================================= */

document.addEventListener(
    "visibilitychange",
    function() {

        if (
            document.hidden
        ) {

            /*
             * Quand l'utilisateur quitte
             * l'onglet, on réduit les requêtes.
             */

            return;

        }


        /*
         * Quand il revient sur le site,
         * actualiser immédiatement.
         */

        if (commandeActuelle) {

            chargerChatClient(
                commandeActuelle
            );

        }


        const pageCommandes =
            document.getElementById(
                "commandes"
            );


        if (
            pageCommandes &&
            pageCommandes.classList.contains(
                "active"
            )
        ) {

            chargerCommandesClient();

        }

    }
);


/* =========================================================
   AVANT DE QUITTER LA PAGE
========================================================= */

window.addEventListener(
    "beforeunload",
    function() {

        arreterActualisationChat();

        arreterActualisationCommandes();

    }
);


/* =========================================================
   EXPORT DES FONCTIONS
   Pour les boutons onclick="" du HTML
========================================================= */

window.ouvrirPage =
    ouvrirPage;

window.ajouterPanier =
    ajouterPanier;

window.retirerPanier =
    retirerPanier;

window.modifierQuantite =
    modifierQuantite;

window.viderPanier =
    viderPanier;

window.afficherPanier =
    afficherPanier;

window.ouvrirPanier =
    ouvrirPanier;

window.passerCommande =
    passerCommande;

window.chargerCommandesClient =
    chargerCommandesClient;

window.ouvrirChatClient =
    ouvrirChatClient;

window.chargerChatClient =
    chargerChatClient;

window.envoyerChat =
    envoyerChat;

window.envoyerMessageGeneral =
    envoyerMessageGeneral;

window.chargerMessagesGeneraux =
    chargerMessagesGeneraux;

window.demanderNotifications =
    demanderNotifications;

window.testerNotification =
    testerNotification;

window.retourAccueil =
    retourAccueil;

window.fermerChat =
    fermerChat;

window.actualiserCommandes =
    actualiserCommandes;

window.actualiserChat =
    actualiserChat;


/* =========================================================
   FIN PARTIE 4/5
========================================================= */
/* =========================================================
   YEMALIN AURA
   SCRIPT PRINCIPAL — PARTIE 5/5
   SÉCURITÉ + UTILITAIRES + FIN DU FICHIER
========================================================= */


/* =========================================================
   CHARGER LES MESSAGES GÉNÉRAUX
   CÔTÉ CLIENT
========================================================= */

async function chargerMessagesGenerauxClient() {

    const container =
        document.getElementById(
            "liste-messages-generaux"
        );


    /*
     * Si cette zone n'existe pas dans index.html,
     * on ne fait rien.
     */

    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="loading">
            Chargement des messages...
        </div>

    `;


    try {

        const response =
            await fetch(
                "/api/messages-generaux",
                {

                    method: "GET",

                    credentials:
                        "same-origin",

                    cache:
                        "no-store"

                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (error) {

            throw new Error(
                "Réponse invalide du serveur."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Impossible de charger les messages."
            );

        }


        const messages =
            Array.isArray(data)
                ? data
                : (
                    Array.isArray(
                        data.messages
                    )
                    ? data.messages
                    : []
                );


        if (!messages.length) {

            container.innerHTML = `

                <div class="empty-state">

                    <div>
                        💬
                    </div>

                    <h3>
                        Aucun message
                    </h3>

                    <p>
                        Vous n'avez encore
                        envoyé aucun message.
                    </p>

                </div>

            `;

            return;
        }


        container.innerHTML =
            messages.map(
                function(message) {

                    const texte =
                        escapeHtml(
                            message.message ||
                            ""
                        );


                    const date =
                        escapeHtml(
                            message.date ||
                            ""
                        );


                    const reponse =
                        message.reponse
                        ? escapeHtml(
                            message.reponse
                        )
                        : "";


                    return `

                        <article
                            class="general-message"
                        >

                            <div>

                                <strong>
                                    💬 Votre message
                                </strong>

                                <small>
                                    ${date}
                                </small>

                            </div>


                            <p>
                                ${texte}
                            </p>


                            ${
                                reponse
                                ?
                                `
                                <div
                                    class="admin-response"
                                >

                                    <strong>
                                        ✅ Réponse de
                                        l'administration
                                    </strong>

                                    <p>
                                        ${reponse}
                                    </p>

                                </div>
                                `
                                :
                                `
                                <small>
                                    ⏳ En attente
                                    de réponse...
                                </small>
                                `
                            }

                        </article>

                    `;

                }
            ).join("");


    } catch (error) {

        console.error(
            "Messages généraux client :",
            error
        );


        container.innerHTML = `

            <div class="error">

                ❌ Impossible de charger
                les messages.

            </div>

        `;

    }
}


/* =========================================================
   ÉCOUTER LE RETOUR DE LA PAGE
========================================================= */

window.addEventListener(
    "pageshow",
    function() {

        try {

            afficherPanier();

        } catch (error) {

            console.error(
                "Pageshow panier :",
                error
            );

        }

    }
);


/* =========================================================
   SAUVEGARDE AUTOMATIQUE DU PANIER
========================================================= */

window.addEventListener(
    "storage",
    function(event) {

        if (
            event.key !==
            "yemalin_panier"
        ) {

            return;
        }


        try {

            panier =
                JSON.parse(
                    event.newValue ||
                    "[]"
                );


            if (
                !Array.isArray(panier)
            ) {

                panier = [];

            }


            afficherPanier();


        } catch (error) {

            console.error(
                "Erreur synchronisation panier :",
                error
            );

        }

    }
);


/* =========================================================
   NETTOYAGE DU PANIER
========================================================= */

function nettoyerPanier() {

    if (
        !Array.isArray(panier)
    ) {

        panier = [];

    }


    panier =
        panier
            .filter(
                function(item) {

                    if (!item) {
                        return false;
                    }


                    const id =
                        Number(item.id);


                    const prix =
                        Number(item.prix);


                    const quantite =
                        Number(
                            item.quantite
                        );


                    return (
                        Number.isFinite(id) &&
                        id > 0 &&
                        Number.isFinite(prix) &&
                        prix >= 0 &&
                        Number.isFinite(quantite) &&
                        quantite > 0
                    );

                }
            )
            .map(
                function(item) {

                    return {

                        id:
                            Number(item.id),

                        nom:
                            String(
                                item.nom || ""
                            ),

                        prix:
                            Number(item.prix),

                        quantite:
                            Number(
                                item.quantite
                            )

                    };

                }
            );


    sauvegarderPanier();

    afficherPanier();

}


/* =========================================================
   INITIALISER LE PANIER
========================================================= */

try {

    nettoyerPanier();

} catch (error) {

    console.error(
        "Nettoyage panier initial :",
        error
    );

}


/* =========================================================
   FERMER UNE NOTIFICATION
========================================================= */

function fermerNotification() {

    const box =
        document.getElementById(
            "notification"
        );


    if (!box) {
        return;
    }


    box.classList.remove(
        "show"
    );

}


/* =========================================================
   FERMER LES MENUS / PAGES AVEC ESC
========================================================= */

document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key !==
            "Escape"
        ) {

            return;
        }


        const notification =
            document.getElementById(
                "notification"
            );


        if (notification) {

            notification.classList.remove(
                "show"
            );

        }

    }
);


/* =========================================================
   FONCTIONS ACCESSIBLES DEPUIS LE HTML
========================================================= */

window.fermerNotification =
    fermerNotification;


window.nettoyerPanier =
    nettoyerPanier;


window.chargerMessagesGenerauxClient =
    chargerMessagesGenerauxClient;


/* =========================================================
   LOG DE FIN DE CHARGEMENT
========================================================= */

console.log(
    "✅ Yemalin Aura — script principal chargé."
);

console.log(
    "🛒 Panier : OK"
);

console.log(
    "📦 Commandes : OK"
);

console.log(
    "💬 Chat : OK"
);

console.log(
    "📨 Messages généraux : OK"
);

console.log(;
    "🔔 Notifications : OK"
);


/* =========================================================
   FIN DU SCRIPT
========================================================= */
