"""
RSA Signature Module for CreatePay Test Framework.

Supports:
- RSA private key signing
- RSA public key verification
- SHA256WithRSA algorithm
- PEM format keys
"""
from pathlib import Path
from typing import Union, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64


class RSASignerError(Exception):
    """RSA signer related errors."""
    pass


class RSASigner:
    """RSA signature and verification handler."""
    
    def __init__(
        self,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None
    ):
        """
        Initialize RSA signer.
        
        Args:
            private_key_path: Path to private key file (PEM format)
            public_key_path: Path to public key file (PEM format)
        """
        self.private_key = None
        self.public_key = None
        self._base_dir = Path(__file__).parent.parent  # api-test-framework directory
        
        if private_key_path:
            self.load_private_key(private_key_path)
        
        if public_key_path:
            self.load_public_key(public_key_path)
    
    def _resolve_path(self, key_path: str) -> Path:
        """
        Resolve key file path relative to project directory.
        
        Args:
            key_path: Relative or absolute path to key file
            
        Returns:
            Resolved Path object
        """
        path = Path(key_path)
        
        # If path is absolute, use it as-is
        if path.is_absolute():
            return path
        
        # Try relative to base directory first
        base_path = self._base_dir / path
        if base_path.exists():
            return base_path
        
        # Try relative to current working directory
        if path.exists():
            return path
        
        # Return base_path even if it doesn't exist (will fail later with clear error)
        return base_path
    
    def load_private_key(self, key_path: str, password: Optional[bytes] = None):
        """
        Load RSA private key from PEM file.
        
        Args:
            key_path: Path to private key file
            password: Password for encrypted key (optional)
            
        Raises:
            RSASignerError: If key loading fails
        """
        try:
            key_file = self._resolve_path(key_path)
            if not key_file.exists():
                raise RSASignerError(f"Private key file not found: {key_path}")
            
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            self.private_key = serialization.load_pem_private_key(
                key_data,
                password=password,
                backend=default_backend()
            )
        except Exception as e:
            raise RSASignerError(f"Failed to load private key: {e}")
    
    def load_public_key(self, key_path: str):
        """
        Load RSA public key from PEM file.
        
        Args:
            key_path: Path to public key file
            
        Raises:
            RSASignerError: If key loading fails
        """
        try:
            key_file = self._resolve_path(key_path)
            if not key_file.exists():
                raise RSASignerError(f"Public key file not found: {key_path}")
            
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            self.public_key = serialization.load_pem_public_key(
                key_data,
                backend=default_backend()
            )
        except Exception as e:
            raise RSASignerError(f"Failed to load public key: {e}")
    
    def sign(self, data: Union[str, bytes], encoding: str = 'utf-8') -> str:
        """
        Sign data with RSA private key using SHA256WithRSA.
        
        Args:
            data: Data to sign
            encoding: Text encoding (default: utf-8)
            
        Returns:
            Base64 encoded signature
            
        Raises:
            RSASignerError: If signing fails
        """
        if not self.private_key:
            raise RSASignerError("Private key not loaded")
        
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode(encoding)
            
            # Sign data
            signature = self.private_key.sign(
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Return base64 encoded signature
            return base64.b64encode(signature).decode('ascii')
        
        except Exception as e:
            raise RSASignerError(f"Signing failed: {e}")
    
    def verify(
        self,
        data: Union[str, bytes],
        signature: str,
        encoding: str = 'utf-8'
    ) -> bool:
        """
        Verify signature with RSA public key.
        
        Args:
            data: Original data
            signature: Base64 encoded signature
            encoding: Text encoding (default: utf-8)
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.public_key:
            raise RSASignerError("Public key not loaded")
        
        try:
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode(encoding)
            
            # Decode base64 signature
            signature_bytes = base64.b64decode(signature)
            
            # Verify signature
            self.public_key.verify(
                signature_bytes,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            return True
        
        except Exception:
            return False
    
    @staticmethod
    def generate_key_pair(
        key_size: int = 2048,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None
    ) -> tuple:
        """
        Generate RSA key pair.
        
        Args:
            key_size: Key size in bits (default: 2048)
            private_key_path: Path to save private key (optional)
            public_key_path: Path to save public key (optional)
            
        Returns:
            Tuple of (private_key, public_key)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Save keys if paths provided
        if private_key_path:
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            Path(private_key_path).write_bytes(private_pem)
        
        if public_key_path:
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            Path(public_key_path).write_bytes(public_pem)
        
        return private_key, public_key


def sign_data(data: str, private_key_path: str) -> str:
    """
    Convenience function to sign data.
    
    Args:
        data: Data to sign
        private_key_path: Path to private key
        
    Returns:
        Base64 encoded signature
    """
    signer = RSASigner(private_key_path=private_key_path)
    return signer.sign(data)


def verify_signature(data: str, signature: str, public_key_path: str) -> bool:
    """
    Convenience function to verify signature.
    
    Args:
        data: Original data
        signature: Base64 encoded signature
        public_key_path: Path to public key
        
    Returns:
        True if valid, False otherwise
    """
    signer = RSASigner(public_key_path=public_key_path)
    return signer.verify(data, signature)
