/* =====================================================
   YEMALIN AURA — script.js
===================================================== */

let panier = [];

let commandeChatActive = null;


/* =====================================================
   INITIALISATION
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    chargerPanier();

    afficherPanier();

    afficherCompteur();

});


/* =====================================================
   NAVIGATION
===================================================== */

function ouvrirPage(page) {

    document
        .querySelectorAll(".page")
        .forEach(section => {
            section.classList.remove("active");
        });


    const cible =
        document.getElementById(page);


    if (cible) {

        cible.classList.add("active");

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }


    if (page === "commandes") {

        chargerCommandes();

    }


    if (page === "messages") {

        // La page message est prête.
        // Aucun chargement obligatoire ici.

    }

}


function ouvrirPanier() {

    ouvrirPage("panier");

    afficherPanier();

}


/* =====================================================
   PANIER — STOCKAGE
===================================================== */

function chargerPanier() {

    try {

        const sauvegarde =
            localStorage.getItem(
                "yemalin_panier"
            );


        if (sauvegarde) {

            panier =
                JSON.parse(sauvegarde);

        }

    } catch (e) {

        panier = [];

    }

}


function sauvegarderPanier() {

    localStorage.setItem(
        "yemalin_panier",
        JSON.stringify(panier)
    );

}


/* =====================================================
   AJOUTER AU PANIER
===================================================== */

function ajouterPanier(produit) {

    const existant =
        panier.find(
            p => p.id === produit.id
        );


    if (existant) {

        existant.quantite += 1;

    } else {

        panier.push({

            id: produit.id,

            nom: produit.nom,

            prix: Number(produit.prix),

            quantite: 1

        });

    }


    sauvegarderPanier();

    afficherPanier();

    afficherCompteur();


    notification(
        `${produit.nom} ajouté au panier.`
    );

}


/* =====================================================
   QUANTITÉ
===================================================== */

function augmenterQuantite(id) {

    const produit =
        panier.find(
            p => p.id === id
        );


    if (!produit) {
        return;
    }


    produit.quantite += 1;


    sauvegarderPanier();

    afficherPanier();

    afficherCompteur();

}


function diminuerQuantite(id) {

    const produit =
        panier.find(
            p => p.id === id
        );


    if (!produit) {
        return;
    }


    produit.quantite -= 1;


    if (produit.quantite <= 0) {

        panier =
            panier.filter(
                p => p.id !== id
            );

    }


    sauvegarderPanier();

    afficherPanier();

    afficherCompteur();

}


function supprimerPanier(id) {

    panier =
        panier.filter(
            p => p.id !== id
        );


    sauvegarderPanier();

    afficherPanier();

    afficherCompteur();

}


/* =====================================================
   COMPTEUR
===================================================== */

function afficherCompteur() {

    const totalArticles =
        panier.reduce(
            (total, produit) =>
                total + produit.quantite,
            0
        );


    const compteur =
        document.getElementById(
            "compteur"
        );


    if (compteur) {

        compteur.textContent =
            totalArticles;

    }


    const compteurRapide =
        document.getElementById(
            "compteur-rapide"
        );


    if (compteurRapide) {

        compteurRapide.textContent =
            totalArticles;

    }

}


/* =====================================================
   AFFICHAGE PANIER
===================================================== */

function afficherPanier() {

    const container =
        document.getElementById(
            "contenu-panier"
        );


    const totalElement =
        document.getElementById(
            "total"
        );


    if (!container) {
        return;
    }


    if (!panier.length) {

        container.innerHTML = `
            <div class="empty-products">
                🛒 Votre panier est vide.
            </div>
        `;


        if (totalElement) {

            totalElement.textContent =
                "0";

        }


        return;

    }


    container.innerHTML = "";


    let total = 0;


    panier.forEach(produit => {

        const sousTotal =
            produit.prix *
            produit.quantite;


        total += sousTotal;


        const div =
            document.createElement(
                "div"
            );


        div.className =
            "panier-item";


        div.innerHTML = `

            <div class="panier-info">

                <strong>
                    ${escapeHtml(produit.nom)}
                </strong>

                <small>
                    ${formatFCFA(produit.prix)}
                    FCFA ×
                    ${produit.quantite}
                </small>

                <br>

                <small>
                    Sous-total :
                    <b>
                        ${formatFCFA(sousTotal)}
                        FCFA
                    </b>
                </small>

            </div>


            <div class="panier-actions">

                <button
                    onclick="diminuerQuantite(${produit.id})"
                >
                    −
                </button>

                <span>
                    ${produit.quantite}
                </span>

                <button
                    onclick="augmenterQuantite(${produit.id})"
                >
                    +
                </button>

                <button
                    onclick="supprimerPanier(${produit.id})"
                >
                    🗑️
                </button>

            </div>

        `;


        container.appendChild(div);

    });


    if (totalElement) {

        totalElement.textContent =
            formatFCFA(total);

    }

}


/* =====================================================
   PASSER COMMANDE
===================================================== */

async function passerCommande() {

    if (!panier.length) {

        notification(
            "Votre panier est vide."
        );

        return;

    }


    const nom =
        document
            .getElementById(
                "client-nom"
            )
            ?.value
            .trim();


    const telephone =
        document
            .getElementById(
                "telephone"
            )
            ?.value
            .trim();


    const adresse =
        document
            .getElementById(
                "adresse"
            )
            ?.value
            .trim();


    if (!nom || !telephone) {

        notification(
            "Veuillez renseigner votre nom et votre téléphone."
        );

        return;

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

                    body: JSON.stringify({

                        client_nom:
                            nom,

                        telephone:
                            telephone,

                        adresse:
                            adresse,

                        panier:
                            panier

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            notification(
                data.message ||
                "Impossible d'envoyer la commande."
            );

            return;

        }


        panier = [];


        sauvegarderPanier();

        afficherPanier();

        afficherCompteur();


        notification(
            `Commande #${data.commande_id} envoyée avec succès.`
        );


        document
            .getElementById(
                "client-nom"
            )
            .value = "";


        document
            .getElementById(
                "telephone"
            )
            .value = "";


        document
            .getElementById(
                "adresse"
            )
            .value = "";


        ouvrirPage("commandes");


        chargerCommandes();


    } catch (error) {

        notification(
            "Erreur de connexion au serveur."
        );

    }

}


/* =====================================================
   COMMANDES CLIENT
===================================================== */

async function chargerCommandes() {

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
                "/api/commandes"
            );


        if (!response.ok) {

            throw new Error();

        }


        const commandes =
            await response.json();


        if (!commandes.length) {

            container.innerHTML = `
                <div class="empty-products">
                    📦 Aucune commande.
                </div>
            `;

            return;

        }


        container.innerHTML = "";


        commandes.forEach(commande => {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "commande-card";


            div.innerHTML = `

                <h3>
                    Commande #${commande.id}
                </h3>

                <span class="commande-statut">
                    ${escapeHtml(commande.statut)}
                </span>

                <p>
                    💰
                    ${formatFCFA(commande.total)}
                    FCFA
                </p>

                <p>
                    📍
                    ${escapeHtml(
                        commande.adresse ||
                        "Lieu non précisé"
                    )}
                </p>

                <p>
                    🕒
                    ${escapeHtml(commande.date)}
                </p>

                <button
                    class="commande-button"
                    onclick="ouvrirChatCommande(${commande.id})"
                >
                    💬 Ouvrir le chat privé
                </button>

            `;


            container.appendChild(div);

        });


    } catch (error) {

        container.innerHTML = `
            <div class="empty-products">
                Impossible de charger les commandes.
            </div>
        `;

    }

}


/* =====================================================
   CHAT
===================================================== */

async function ouvrirChatCommande(
    commandeId
) {

    commandeChatActive =
        commandeId;


    ouvrirPage("chat");


    const info =
        document.getElementById(
            "chat-info"
        );


    if (info) {

        info.textContent =
            `Conversation privée — Commande #${commandeId}`;

    }


    await chargerChat();

}


async function chargerChat() {

    if (!commandeChatActive) {
        return;
    }


    const container =
        document.getElementById(
            "chat-messages"
        );


    if (!container) {
        return;
    }


    try {

        const response =
            await fetch(
                `/api/commande/${commandeChatActive}`
            );


        if (!response.ok) {

            throw new Error();

        }


        const data =
            await response.json();


        container.innerHTML = "";


        if (!data.messages.length) {

            container.innerHTML = `
                <div class="empty-products">
                    Aucun message pour le moment.
                </div>
            `;

            return;

        }


        data.messages.forEach(message => {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "chat-bubble " +
                (
                    message.auteur === "Admin"
                    ? "admin"
                    : "client"
                );


            div.innerHTML = `

                <small>
                    ${escapeHtml(
                        message.auteur
                    )}
                    ·
                    ${escapeHtml(
                        message.date
                    )}
                </small>

                ${escapeHtml(
                    message.message
                )}

            `;


            container.appendChild(div);

        });


        container.scrollTop =
            container.scrollHeight;


    } catch (error) {

        container.innerHTML = `
            <div class="empty-products">
                Impossible de charger le chat.
            </div>
        `;

    }

}


/* =====================================================
   ENVOYER CHAT
===================================================== */

async function envoyerChat() {

    if (!commandeChatActive) {

        notification(
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
        return;
    }


    try {

        const response =
            await fetch(
                `/api/chat/${commandeChatActive}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        message:
                            message,

                        auteur:
                            "Client",

                        client_nom:
                            localStorage.getItem(
                                "yemalin_client_nom"
                            ) || ""

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            notification(
                data.message ||
                "Message non envoyé."
            );

            return;

        }


        input.value = "";


        await chargerChat();

    } catch (error) {

        notification(
            "Erreur de connexion."
        );

    }

}


/* =====================================================
   MESSAGE GÉNÉRAL
===================================================== */

async function envoyerMessageGeneral() {

    const nom =
        document
            .getElementById(
                "message-nom"
            )
            ?.value
            .trim();


    const message =
        document
            .getElementById(
                "message-general"
            )
            ?.value
            .trim();


    if (!nom || !message) {

        notification(
            "Veuillez remplir les champs."
        );

        return;

    }


    localStorage.setItem(
        "yemalin_client_nom",
        nom
    );


    try {

        const response =
            await fetch(
                "/api/message",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        client_nom:
                            nom,

                        message:
                            message

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.ok) {

            notification(
                data.message ||
                "Message non envoyé."
            );

            return;

        }


        document
            .getElementById(
                "message-general"
            )
            .value = "";


        notification(
            "Votre message a été envoyé."
        );


    } catch (error) {

        notification(
            "Erreur de connexion."
        );

    }

}


/* =====================================================
   NOTIFICATION
===================================================== */

function notification(message) {

    const element =
        document.getElementById(
            "notification"
        );


    if (!element) {
        return;
    }


    element.textContent =
        message;


    element.classList.add(
        "show"
    );


    clearTimeout(
        window.notificationTimer
    );


    window.notificationTimer =
        setTimeout(
            () => {

                element.classList.remove(
                    "show"
                );

            },
            3000
        );

}


/* =====================================================
   UTILITAIRES
===================================================== */

function formatFCFA(nombre) {

    return Number(nombre || 0)
        .toLocaleString(
            "fr-FR"
        );

}


function escapeHtml(value) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


/* =====================================================
   ACTUALISATION DU CHAT
===================================================== */

setInterval(
    () => {

        if (
            commandeChatActive &&
            document
                .getElementById("chat")
                ?.classList
                .contains("active")
        ) {

            chargerChat();

        }

    },
    4000
);