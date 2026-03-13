#!/usr/bin/env python3
"""
Generate test RSA key pairs for CreatePay Test Framework.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rsa_signer import RSASigner


def generate_test_keys():
    """Generate test RSA key pairs."""
    base_dir = Path(__file__).parent.parent
    keys_dir = base_dir / 'config' / 'keys'
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate test keys
    private_key_path = keys_dir / 'test_private_key.pem'
    public_key_path = keys_dir / 'test_public_key.pem'
    
    print("Generating RSA key pair...")
    RSASigner.generate_key_pair(
        key_size=2048,
        private_key_path=str(private_key_path),
        public_key_path=str(public_key_path)
    )
    
    print(f"✓ Private key saved to: {private_key_path}")
    print(f"✓ Public key saved to: {public_key_path}")
    print("\n⚠️  WARNING: These are TEST keys only!")
    print("   Do NOT use in production environment!")


if __name__ == '__main__':
    generate_test_keys()
