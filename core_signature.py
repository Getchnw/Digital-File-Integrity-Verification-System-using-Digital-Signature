from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64

class DigitalSignatureCore:
    @staticmethod
    def generate_keys():
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        return private_key, public_key

    @staticmethod
    def hash_file_data(file_bytes):
        return SHA256.new(file_bytes)

    @staticmethod
    def sign_file(private_key_pem, file_bytes):
        try:
            private_key = RSA.import_key(private_key_pem)
        except (ValueError, IndexError, TypeError):
            raise ValueError("INVALID_PRIVATE_KEY")

        hash_obj = DigitalSignatureCore.hash_file_data(file_bytes)
        signer = pkcs1_15.new(private_key)
        signature = signer.sign(hash_obj)
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_file(public_key_pem, file_bytes, signature_b64):
        try:
            public_key = RSA.import_key(public_key_pem)
        except (ValueError, IndexError, TypeError):
            return "INVALID_KEY_FORMAT"

        try:
            signature = base64.b64decode(signature_b64)
            hash_obj = DigitalSignatureCore.hash_file_data(file_bytes)
            verifier = pkcs1_15.new(public_key)
            verifier.verify(hash_obj, signature)
            return "VALID"
        except (ValueError, TypeError):
            return "TAMPERED_OR_WRONG_KEY"
        except Exception:
            return "UNKNOWN_ERROR"