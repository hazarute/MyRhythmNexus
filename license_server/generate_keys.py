from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

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

    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    private_key_path = os.path.join(base_dir, "private.pem")
    public_key_path = os.path.join(base_dir, "public.pem")

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
