/* =========================================================
   YEMALIN AURA — SCRIPT PRINCIPAL
   Version corrigée
========================================================= */

"use strict";

/* =========================================================
   VARIABLES
========================================================= */

let panier = JSON.parse(
    localStorage.getItem("yemalin_panier") || "[]"
);

let commandeActuelle = null;


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


function notify(message) {

    const box =
        document.getElementById("notification");

    if (!box) {
        alert(message);
        return;
    }

    box.textContent = message;

    box.classList.add("show");

    setTimeout(() => {
        box.classList.remove("show");
    }, 3000);
}


function sauvegarderPanier() {

    localStorage.setItem(
        "yemalin_panier",
        JSON.stringify(panier)
    );
}


/* =========================================================
   NAVIGATION
========================================================= */

function ouvrirPage(pageId) {

    document
        .querySelectorAll(".page")
        .forEach(page => {

            page.classList.remove("active");

        });


    const page =
        document.getElementById(pageId);


    if (page) {

        page.classList.add("active");

    }


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });


    if (pageId === "commandes") {

        chargerCommandesClient();

    }


    if (pageId === "messages") {

        // Aucun chargement nécessaire ici.
        // Les messages généraux sont envoyés
        // vers l'administration.

    }


    if (pageId === "panier") {

        afficherPanier();

    }
}


/* =========================================================
   PRODUITS / PANIER
========================================================= */

function ajouterPanier(produit) {

    const existant =
        panier.find(
            item =>
                Number(item.id) ===
                Number(produit.id)
        );


    if (existant) {

        existant.quantite += 1;

    } else {

        panier.push({

            id: Number(produit.id),

            nom: String(produit.nom || ""),

            prix: Number(produit.prix || 0),

            quantite: 1

        });

    }


    sauvegarderPanier();

    afficherPanier();

    notify(
        "🛒 Produit ajouté au panier."
    );
}


function retirerPanier(id) {

    panier =
        panier.filter(
            item =>
                Number(item.id) !==
                Number(id)
        );


    sauvegarderPanier();

    afficherPanier();
}


function modifierQuantite(
    id,
    changement
) {

    const produit =
        panier.find(
            item =>
                Number(item.id) ===
                Number(id)
        );


    if (!produit) {
        return;
    }


    produit.quantite +=
        Number(changement);


    if (produit.quantite <= 0) {

        retirerPanier(id);

        return;
    }


    sauvegarderPanier();

    afficherPanier();
}


function viderPanier() {

    panier = [];

    sauvegarderPanier();

    afficherPanier();

    notify(
        "🛒 Panier vidé."
    );
}


function calculerTotal() {

    return panier.reduce(
        (total, item) => {

            return total +
                Number(item.prix) *
                Number(item.quantite);

        },
        0
    );
}


function nombreArticles() {

    return panier.reduce(
        (total, item) => {

            return total +
                Number(item.quantite);

        },
        0
    );
}


/* =========================================================
   AFFICHER LE PANIER
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
                .toLocaleString("fr-FR");

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
                    onclick="ouvrirPage('accueil')"
                >
                    Découvrir les produits
                </button>

            </div>

        `;

        return;
    }


    contenu.innerHTML =
        panier.map(item => {

            const sousTotal =
                Number(item.prix) *
                Number(item.quantite);


            return `

                <article class="cart-item">

                    <div class="cart-item-info">

                        <h3>
                            ${escapeHtml(
                                item.nom
                            )}
                        </h3>

                        <p>
                            ${Number(
                                item.prix
                            ).toLocaleString(
                                "fr-FR"
                            )}
                            FCFA / unité
                        </p>

                    </div>


                    <div class="cart-quantity">

                        <button
                            type="button"
                            onclick="
                                modifierQuantite(
                                    ${item.id},
                                    -1
                                )
                            "
                        >
                            −
                        </button>


                        <strong>
                            ${item.quantite}
                        </strong>


                        <button
                            type="button"
                            onclick="
                                modifierQuantite(
                                    ${item.id},
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
                                ${item.id}
                            )
                        "
                    >
                        🗑️
                    </button>

                </article>

            `;

        }).join("");


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


function ouvrirPanier() {

    ouvrirPage("panier");

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
            ?.value.trim();


    const telephone =
        document
            .getElementById("telephone")
            ?.value.trim();


    const adresse =
        document
            .getElementById("adresse")
            ?.value.trim();


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

                    body: JSON.stringify({

                        client_nom: nom,

                        telephone:
                            telephone,

                        adresse:
                            adresse,

                        produits:
                            panier.map(
                                item => ({

                                    id:
                                        Number(
                                            item.id
                                        ),

                                    quantite:
                                        Number(
                                            item.quantite
                                        )

                                })
                            )

                    })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "Impossible de passer la commande."
            );

        }


        commandeActuelle =
            data.commande_id ||
            null;


        panier = [];

        sauvegarderPanier();

        afficherPanier();


        notify(
            "✅ Commande envoyée avec succès."
        );


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


        ouvrirPage("commandes");

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

            bouton.disabled = false;

            bouton.textContent =
                "✅ Passer la commande";

        }

    }
}


/* =========================================================
   COMMANDES CLIENT
========================================================= */

async function chargerCommandesClient() {

    const container =
        document.getElementById(
            "liste-commandes"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        "<p>Chargement...</p>";


    try {

        const response =
            await fetch(
                "/api/mes-commandes",
                {
                    credentials:
                        "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Erreur de chargement."
            );

        }


        const commandes =
            Array.isArray(data)
                ? data
                : (
                    data.commandes ||
                    []
                );


        if (!commandes.length) {

            container.innerHTML = `

                <div class="empty-state">

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
                commande => `

                    <article
                        class="order-card"
                    >

                        <h3>
                            📦 Commande
                            #${commande.id}
                        </h3>


                        <p>

                            <strong>
                                Total :
                            </strong>

                            ${Number(
                                commande.total || 0
                            ).toLocaleString(
                                "fr-FR"
                            )}

                            FCFA

                        </p>


                        <p>

                            <strong>
                                Statut :
                            </strong>

                            ${escapeHtml(
                                commande.statut ||
                                "Nouvelle"
                            )}

                        </p>


                        <p>

                            <small>
                                ${escapeHtml(
                                    commande.date ||
                                    ""
                                )}
                            </small>

                        </p>


                        <button
                            type="button"
                            class="btn"
                            onclick="
                                ouvrirChatClient(
                                    ${commande.id}
                                )
                            "
                        >
                            💬 Ouvrir le chat
                        </button>

                    </article>

                `
            ).join("");

    } catch (error) {

        console.error(
            "Commandes :",
            error
        );


        container.innerHTML = `

            <div class="error">

                ❌ Impossible de charger
                vos commandes.

            </div>

        `;

    }
}
/* =========================================================
   CHAT CLIENT
========================================================= */

async function ouvrirChatClient(commandeId) {

    commandeActuelle =
        Number(commandeId);

    ouvrirPage("chat");

    await chargerChatClient(
        commandeActuelle
    );
}


/* =========================================================
   CHARGER LE CHAT CLIENT
========================================================= */

async function chargerChatClient(commandeId) {

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


    messagesContainer.innerHTML =
        "<p>Chargement...</p>";


    try {

        const response =
            await fetch(
                `/api/chat/${commandeId}`,
                {
                    method: "GET",

                    credentials:
                        "same-origin"
                }
            );


        const data =
            await response.json();


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
                    💬 Commande #${commandeId}
                </strong>

            `;

        }


        const messages =
            Array.isArray(data.messages)
                ? data.messages
                : [];


        if (!messages.length) {

            messagesContainer.innerHTML = `

                <div class="empty-state">

                    <p>
                        Aucun message pour le moment.
                    </p>

                    <small>
                        Vous pouvez envoyer
                        un message à
                        l'administration ci-dessous.
                    </small>

                </div>

            `;

            return;
        }


        messagesContainer.innerHTML =
            messages.map(
                message => {

                    const estAdmin =
                        message.auteur === "Admin";


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

                                ${
                                    estAdmin
                                    ? "👨‍💼 Administration"
                                    : "👤 Vous"
                                }

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
   ENVOYER MESSAGE DANS LE CHAT
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
                `/api/chat/${commandeActuelle}`,
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


        const data =
            await response.json();


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
   MESSAGES GÉNÉRAUX
========================================================= */

/*
 * IMPORTANT :
 *
 * Flask possède cette route :
 *
 * POST /api/messages-general
 *
 * et attend :
 *
 * {
 *     "nom": "...",
 *     "message": "..."
 * }
 *
 * L'ancienne version utilisait :
 *
 * /api/message-general
 *
 * et "client_nom".
 *
 * C'était la cause de :
 *
 * "Route API introuvable"
 *
 * Cette version est corrigée.
 */


async function envoyerMessageGeneral() {

    const nomInput =
        document.getElementById(
            "message-nom"
        );


    const messageInput =
        document.getElementById(
            "message-general"
        );


    const nom =
        nomInput
        ? nomInput.value.trim()
        : "";


    const message =
        messageInput
        ? messageInput.value.trim()
        : "";


    if (!nom) {

        notify(
            "Veuillez entrer votre nom."
        );

        if (nomInput) {
            nomInput.focus();
        }

        return;
    }


    if (!message) {

        notify(
            "Veuillez écrire votre message."
        );

        if (messageInput) {
            messageInput.focus();
        }

        return;
    }


    if (message.length > 3000) {

        notify(
            "Votre message est trop long."
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
         * Route Flask correcte :
         *
         * /api/messages-general
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


        /*
         * On vérifie d'abord
         * que le serveur a répondu.
         */

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


        /*
         * Nettoyer les champs
         */

        if (nomInput) {

            nomInput.value = "";

        }


        if (messageInput) {

            messageInput.value = "";

        }


        notify(
            "✅ Votre message a été envoyé."
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

            bouton.disabled = false;

            bouton.textContent =
                "Envoyer le message";

        }

    }
}


/* =========================================================
   ACTUALISER LE CHAT
========================================================= */

function actualiserChatAutomatiquement() {

    if (!commandeActuelle) {
        return;
    }


    const chat =
        document.getElementById(
            "chat"
        );


    if (!chat) {
        return;
    }


    if (
        !chat.classList.contains(
            "active"
        )
    ) {
        return;
    }


    chargerChatClient(
        commandeActuelle
    );
}


/*
 * Actualisation toutes les 5 secondes.
 */

setInterval(
    actualiserChatAutomatiquement,
    5000
);


/* =========================================================
   NOTIFICATIONS PUSH
========================================================= */

async function demanderNotifications() {

    /*
     * Vérifier si le navigateur
     * supporte les notifications.
     */

    if (
        !("Notification" in window)
    ) {

        notify(
            "❌ Les notifications ne sont pas supportées par votre navigateur."
        );

        return;
    }


    try {

        const permission =
            await Notification.requestPermission();


        if (
            permission !== "granted"
        ) {

            notify(
                "🔕 Notifications non autorisées."
            );

            return;
        }


        /*
         * Si push.js existe,
         * on lui laisse gérer
         * l'abonnement VAPID.
         */

        if (
            typeof window.abonnerNotifications ===
            "function"
        ) {

            await window.abonnerNotifications();

            notify(
                "🔔 Notifications activées."
            );

            return;
        }


        /*
         * Compatibilité avec certaines
         * anciennes versions de push.js.
         */

        if (
            typeof window.activerNotifications ===
            "function"
        ) {

            await window.activerNotifications();

            notify(
                "🔔 Notifications activées."
            );

            return;
        }


        /*
         * Notification simple si aucun
         * système Push n'est disponible.
         */

        try {

            new Notification(
                "Yemalin Aura",
                {
                    body:
                        "Les notifications sont activées."
                }
            );

        } catch (notificationError) {

            console.warn(
                "Notification locale impossible :",
                notificationError
            );

        }


        notify(
            "🔔 Notifications autorisées."
        );


    } catch (error) {

        console.error(
            "Notifications :",
            error
        );


        notify(
            "❌ Impossible d'activer les notifications."
        );

    }
       }
/* =========================================================
   INITIALISATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        /*
         * Afficher immédiatement
         * le contenu du panier.
         */

        afficherPanier();


        /*
         * Préparer la page
         * des commandes.
         */

        const commandes =
            document.getElementById(
                "liste-commandes"
            );


        if (commandes) {

            chargerCommandesClient();

        }


        /*
         * Permettre l'envoi du message
         * général avec Ctrl + Entrée.
         */

        const messageGeneral =
            document.getElementById(
                "message-general"
            );


        if (messageGeneral) {

            messageGeneral.addEventListener(
                "keydown",
                function(event) {

                    if (
                        event.ctrlKey &&
                        event.key === "Enter"
                    ) {

                        event.preventDefault();

                        envoyerMessageGeneral();

                    }

                }
            );

        }


        /*
         * Permettre l'envoi du chat
         * avec la touche Entrée.
         *
         * Ton index.html possède déjà
         * onkeydown="envoyerChat()",
         * mais ceci ajoute une sécurité.
         */

        const chatInput =
            document.getElementById(
                "chat-message"
            );


        if (chatInput) {

            chatInput.addEventListener(
                "keydown",
                function(event) {

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

    }
);


/* =========================================================
   PROTECTION DU LOCALSTORAGE
========================================================= */

window.addEventListener(
    "storage",
    function(event) {

        if (
            event.key ===
            "yemalin_panier"
        ) {

            try {

                panier =
                    JSON.parse(
                        event.newValue ||
                        "[]"
                    );


                if (
                    !Array.isArray(
                        panier
                    )
                ) {

                    panier = [];

                }

            } catch (error) {

                panier = [];

            }


            afficherPanier();

        }

    }
);


/* =========================================================
   VÉRIFICATION DU PANIER
========================================================= */

function nettoyerPanier() {

    if (
        !Array.isArray(
            panier
        )
    ) {

        panier = [];

    }


    panier =
        panier.filter(
            item => {

                if (!item) {
                    return false;
                }


                if (
                    !item.id ||
                    !item.nom
                ) {

                    return false;

                }


                const prix =
                    Number(
                        item.prix
                    );


                const quantite =
                    Number(
                        item.quantite
                    );


                if (
                    !Number.isFinite(
                        prix
                    )
                ) {

                    return false;

                }


                if (
                    !Number.isFinite(
                        quantite
                    ) ||
                    quantite <= 0
                ) {

                    return false;

                }


                item.id =
                    Number(
                        item.id
                    );


                item.prix =
                    prix;


                item.quantite =
                    Math.floor(
                        quantite
                    );


                return true;

            }
        );


    sauvegarderPanier();

}


/* =========================================================
   LANCER LE NETTOYAGE
========================================================= */

nettoyerPanier();

afficherPanier();


/* =========================================================
   EMPÊCHER LES ERREURS SI UNE FONCTION
   EST APPELÉE AVANT LE CHARGEMENT COMPLET
========================================================= */

window.ouvrirPage =
    ouvrirPage;


window.ouvrirPanier =
    ouvrirPanier;


window.ajouterPanier =
    ajouterPanier;


window.retirerPanier =
    retirerPanier;


window.modifierQuantite =
    modifierQuantite;


window.viderPanier =
    viderPanier;


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


window.demanderNotifications =
    demanderNotifications;


/* =========================================================
   FIN DU SCRIPT
========================================================= */
