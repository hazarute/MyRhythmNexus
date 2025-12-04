from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os
from pathlib import Path

from license_server.core.config import settings

def generate_keys():
    """
    Generates a 2048-bit RSA key pair (Private & Public).
    Saves them as PEM files in the current directory.
    """
    print("Generating RSA-2048 Key Pair...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serialize private key (PKCS8, No Encryption for simplicity in this context, 
    # but in prod you might want password protection)
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Generate public key
    public_key = private_key.public_key()

    # Serialize public key (SubjectPublicKeyInfo)
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Determine paths from settings (so .env is respected)
    # Settings may contain relative paths; resolve relative to project root
    private_key_path = Path(settings.PRIVATE_KEY_PATH)
    public_key_path = Path(settings.PUBLIC_KEY_PATH)

    if not private_key_path.is_absolute():
        private_key_path = (Path(__file__).parent / private_key_path).resolve()
    if not public_key_path.is_absolute():
        public_key_path = (Path(__file__).parent / public_key_path).resolve()

    # Ensure parent directory exists
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)

    # Write private key to file
    with open(private_key_path, "wb") as f:
        f.write(pem_private)
    
    # Write public key to file
    with open(public_key_path, "wb") as f:
        f.write(pem_public)

    print(f"\n✅ RSA Keys generated successfully!")
    print(f"🔑 Private Key: {private_key_path}")
    print(f"🔒 Public Key:  {public_key_path}")
    print("\n⚠️  UYARI: 'private.pem' dosyasını ASLA paylaşmayın ve güvenli tutun.")
    print("ℹ️  BİLGİ: 'public.pem' dosyasını MyRhythmNexus istemcisine gömeceğiz.")

if __name__ == "__main__":
    generate_keys()
