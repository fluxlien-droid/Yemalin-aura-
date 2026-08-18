/* =========================================================
   YEMALIN AURA — SCRIPT PRINCIPAL
   Compatible avec index.html
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
    const box = document.getElementById("notification");

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
   NAVIGATION ENTRE LES PAGES
========================================================= */

function ouvrirPage(pageId) {

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    const page = document.getElementById(pageId);

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
        chargerMessagesGeneraux();
    }
}


/* =========================================================
   PANIER
========================================================= */

function ajouterPanier(produit) {

    const existant = panier.find(
        item => Number(item.id) === Number(produit.id)
    );

    if (existant) {

        existant.quantite += 1;

    } else {

        panier.push({
            id: Number(produit.id),
            nom: produit.nom,
            prix: Number(produit.prix),
            quantite: 1
        });
    }

    sauvegarderPanier();
    afficherPanier();

    notify("🛒 Produit ajouté au panier.");
}


function retirerPanier(id) {

    panier = panier.filter(
        item => Number(item.id) !== Number(id)
    );

    sauvegarderPanier();
    afficherPanier();
}


function modifierQuantite(id, changement) {

    const produit = panier.find(
        item => Number(item.id) === Number(id)
    );

    if (!produit) return;

    produit.quantite += changement;

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

    notify("🛒 Panier vidé.");
}


function calculerTotal() {

    return panier.reduce(
        (total, item) =>
            total +
            Number(item.prix) *
            Number(item.quantite),
        0
    );
}


function nombreArticles() {

    return panier.reduce(
        (total, item) =>
            total + Number(item.quantite),
        0
    );
}


function afficherPanier() {

    const compteur =
        document.getElementById("compteur");

    const compteurRapide =
        document.getElementById("compteur-rapide");

    const contenu =
        document.getElementById("contenu-panier");

    const total =
        document.getElementById("total");


    const nombre = nombreArticles();

    if (compteur) {
        compteur.textContent = nombre;
    }

    if (compteurRapide) {
        compteurRapide.textContent = nombre;
    }


    if (total) {
        total.textContent =
            calculerTotal().toLocaleString("fr-FR");
    }


    if (!contenu) return;


    if (!panier.length) {

        contenu.innerHTML = `
            <div class="empty-state">
                <p>🛒 Votre panier est vide.</p>

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


    contenu.innerHTML = panier.map(item => {

        const sousTotal =
            Number(item.prix) *
            Number(item.quantite);

        return `
            <article class="cart-item">

                <div class="cart-item-info">

                    <h3>
                        ${escapeHtml(item.nom)}
                    </h3>

                    <p>
                        ${Number(item.prix).toLocaleString("fr-FR")}
                        FCFA / unité
                    </p>

                </div>


                <div class="cart-quantity">

                    <button
                        type="button"
                        onclick="modifierQuantite(
                            ${item.id},
                            -1
                        )"
                    >
                        −
                    </button>

                    <strong>
                        ${item.quantite}
                    </strong>

                    <button
                        type="button"
                        onclick="modifierQuantite(
                            ${item.id},
                            1
                        )"
                    >
                        +
                    </button>

                </div>


                <strong class="cart-subtotal">
                    ${sousTotal.toLocaleString("fr-FR")}
                    FCFA
                </strong>


                <button
                    type="button"
                    class="btn"
                    onclick="retirerPanier(${item.id})"
                >
                    🗑️
                </button>

            </article>
        `;

    }).join("") + `

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
        document.getElementById("client-nom")
            ?.value.trim();

    const telephone =
        document.getElementById("telephone")
            ?.value.trim();

    const adresse =
        document.getElementById("adresse")
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
    }


    try {

        const response = await fetch(
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

                    telephone: telephone,

                    adresse: adresse,

                    produits: panier.map(item => ({
                        produit_id:
                            Number(item.id),

                        quantite:
                            Number(item.quantite)
                    }))
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            throw new Error(
                data.message ||
                "Impossible de passer la commande."
            );
        }


        commandeActuelle =
            data.commande ||
            data;


        panier = [];

        sauvegarderPanier();

        afficherPanier();


        notify(
            "✅ Commande envoyée avec succès."
        );


        ouvrirPage("commandes");

        chargerCommandesClient();


        document.getElementById(
            "client-nom"
        ).value = "";

        document.getElementById(
            "telephone"
        ).value = "";

        document.getElementById(
            "adresse"
        ).value = "";


    } catch (error) {

        console.error(
            "Commande:",
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

    if (!container) return;


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
                "Erreur."
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
                        Vous n'avez encore aucune commande.
                    </p>
                </div>
            `;

            return;
        }


        container.innerHTML =
            commandes.map(commande => `

                <article class="order-card">

                    <h3>
                        📦 Commande #${commande.id}
                    </h3>

                    <p>
                        <strong>
                            Total :
                        </strong>

                        ${Number(
                            commande.total || 0
                        ).toLocaleString("fr-FR")}

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
                                commande.date || ""
                            )}
                        </small>
                    </p>

                    <button
                        type="button"
                        class="btn"
                        onclick="ouvrirChatClient(
                            ${commande.id}
                        )"
                    >
                        💬 Ouvrir le chat
                    </button>

                </article>

            `).join("");


    } catch (error) {

        console.error(
            "Commandes:",
            error
        );

        container.innerHTML = `
            <div class="error">
                Impossible de charger vos commandes.
            </div>
        `;
    }
}


/* =========================================================
   CHAT CLIENT
========================================================= */

async function ouvrirChatClient(
    commandeId
) {

    commandeActuelle =
        commandeId;

    ouvrirPage("chat");

    await chargerChatClient(
        commandeId
    );
}


async function chargerChatClient(
    commandeId
) {

    const messagesContainer =
        document.getElementById(
            "chat-messages"
        );

    const info =
        document.getElementById(
            "chat-info"
        );


    if (!messagesContainer) return;


    messagesContainer.innerHTML =
        "<p>Chargement...</p>";


    try {

        const response =
            await fetch(
                `/api/chat/${commandeId}`,
                {
                    credentials:
                        "same-origin"
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            throw new Error(
                data.message ||
                "Chat indisponible."
            );
        }


        if (info) {

            info.innerHTML = `
                <strong>
                    Commande #${commandeId}
                </strong>
            `;
        }


        const messages =
            data.messages || [];


        if (!messages.length) {

            messagesContainer.innerHTML = `
                <p>
                    Aucun message pour le moment.
                </p>
            `;

            return;
        }


        messagesContainer.innerHTML =
            messages.map(message => {

                const admin =
                    message.auteur === "Admin";

                return `
                    <div class="
                        message-bubble
                        ${admin
                            ? "message-admin"
                            : "message-client"}
                    ">

                        <strong>
                            ${admin
                                ? "Administration"
                                : escapeHtml(
                                    message.client_nom ||
                                    "Vous"
                                )}
                        </strong>

                        <p>
                            ${escapeHtml(
                                message.message
                            )}
                        </p>

                        <small>
                            ${escapeHtml(
                                message.date || ""
                            )}
                        </small>

                    </div>
                `;

            }).join("");


        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;


    } catch (error) {

        console.error(
            "Chat:",
            error
        );

        messagesContainer.innerHTML = `
            <div class="error">
                ${escapeHtml(
                    error.message ||
                    "Erreur de chargement du chat."
                )}
            </div>
        `;
    }
}


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


    if (!input) return;


    const message =
        input.value.trim();


    if (!message) return;


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

                    body: JSON.stringify({
                        message: message
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

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

async function envoyerMessageGeneral() {

    const nom =
        document.getElementById(
            "message-nom"
        )?.value.trim();

    const message =
        document.getElementById(
            "message-general"
        )?.value.trim();


    if (!nom) {

        notify(
            "Veuillez entrer votre nom."
        );

        return;
    }


    if (!message) {

        notify(
            "Veuillez écrire votre message."
        );

        return;
    }


    try {

        const response =
            await fetch(
                "/api/message-general",
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
                        message: message
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            throw new Error(
                data.message ||
                "Message non envoyé."
            );
        }


        document.getElementById(
            "message-general"
        ).value = "";


        notify(
            "✅ Message envoyé."
        );


        chargerMessagesGeneraux();


    } catch (error) {

        notify(
            "❌ " +
            (
                error.message ||
                "Erreur d'envoi."
            )
        );
    }
}


async function chargerMessagesGeneraux() {

    try {

        const response =
            await fetch(
                "/api/messages-generaux",
                {
                    credentials:
                        "same-origin"
                }
            );


        if (!response.ok) return;


        const data =
            await response.json();


        console.log(
            "Messages généraux:",
            data
        );

    } catch (error) {

        console.error(
            "Messages généraux:",
            error
        );
    }
}

/* =========================================================
   NOTIFICATIONS
========================================================= */

async function demanderNotifications() {

    if (
        !("Notification" in window)
    ) {

        notify(
            "❌ Les notifications ne sont pas supportées."
        );

        return;
    }


    try {

        const permission =
            await Notification.requestPermission();


        if (permission !== "granted") {

            notify(
                "🔕 Notifications non autorisées."
            );

            return;
        }


        if (
            "serviceWorker" in navigator &&
            "PushManager" in window
        ) {

            const registration =
                await navigator.serviceWorker.ready;


            const existing =
                await registration.pushManager
                    .getSubscription();


            if (existing) {

                notify(
                    "🔔 Notifications déjà activées."
                );

                return;
            }


            notify(
                "🔔 Notification activée."
            );

            /*
             * L'inscription Push complète
             * est gérée par push.js.
             */

            if (
                typeof window.activerPush ===
                "function"
            ) {

                await window.activerPush(
                    registration
                );
            }

        } else {

            notify(
                "🔔 Notifications activées."
            );
        }


    } catch (error) {

        console.error(
            "Notifications:",
            error
        );

        notify(
            "❌ Impossible d'activer les notifications."
        );
    }
}


/* =========================================================
   ACTUALISATION DU CHAT
========================================================= */

setInterval(() => {

    if (
        commandeActuelle &&
        document.getElementById("chat")
            ?.classList.contains("active")
    ) {

        chargerChatClient(
            commandeActuelle
        );
    }

}, 5000);


/* =========================================================
   INITIALISATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        afficherPanier();

        chargerCommandesClient();

    }
);
