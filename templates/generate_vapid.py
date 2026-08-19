# generate_vapid.py
#
# Générateur de clés VAPID pour Yemalin Aura
#
# À exécuter une seule fois.
# Ne partage JAMAIS la clé privée.

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def main():

    # Génération d'une nouvelle clé privée
    private_key = ec.generate_private_key(
        ec.SECP256R1()
    )

    # Clé publique
    public_key = private_key.public_key()

    # Clé privée en hexadécimal
    private_hex = (
        private_key
        .private_numbers()
        .private_value
        .to_bytes(32, "big")
        .hex()
    )

    # Clé publique au format utilisé par Web Push
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    public_hex = public_bytes.hex()

    print()
    print("=" * 55)
    print("       YEMALIN AURA — CLÉS VAPID")
    print("=" * 55)
    print()

    print("VAPID_PUBLIC_KEY=")
    print(public_hex)

    print()

    print("VAPID_PRIVATE_KEY=")
    print(private_hex)

    print()

    print("VAPID_EMAIL=mailto:ton-email@example.com")

    print()
    print("=" * 55)
    print("⚠️ NE PARTAGE JAMAIS VAPID_PRIVATE_KEY")
    print("=" * 55)


if __name__ == "__main__":
    main()
