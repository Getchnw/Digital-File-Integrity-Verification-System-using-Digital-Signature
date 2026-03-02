from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64

class DigitalSignatureCore:
    @staticmethod
    def generate_keys():
        """
        สร้าง RSA Key Pair ขนาด 2048-bit
        คืนค่ากลับมาเป็น (Private Key, Public Key) ในรูปแบบ PEM format (ข้อความ)
        """
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        return private_key, public_key

    @staticmethod
    def hash_file_data(file_bytes):
        """
        นำข้อมูลไฟล์ (Bytes) มาผ่านกระบวนการ SHA-256
        """
        hash_obj = SHA256.new(file_bytes)
        return hash_obj

    @staticmethod
    def sign_file(private_key_pem, file_bytes):
        """
        นำ Private Key มาเซ็น (Sign) ค่า Hash ของไฟล์
        คืนค่ากลับมาเป็น Digital Signature รูปแบบ Base64 String
        """
        private_key = RSA.import_key(private_key_pem)
        hash_obj = DigitalSignatureCore.hash_file_data(file_bytes)
        
        # เซ็นด้วยมาตรฐาน PKCS#1 v1.5
        signer = pkcs1_15.new(private_key)
        signature = signer.sign(hash_obj)
        
        # แปลงเป็น Base64 เพื่อให้ง่ายต่อการเก็บและนำไปสร้าง QR Code
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_file(public_key_pem, file_bytes, signature_b64):
        """
        ตรวจสอบไฟล์ด้วย Public Key และ Signature
        คืนค่า True ถ้าไฟล์ถูกต้อง(ไม่ถูกแก้), คืนค่า False ถ้าไฟล์ถูกดัดแปลงหรือ Key ผิด
        """
        try:
            public_key = RSA.import_key(public_key_pem)
            signature = base64.b64decode(signature_b64)
            hash_obj = DigitalSignatureCore.hash_file_data(file_bytes)
            
            verifier = pkcs1_15.new(public_key)
            verifier.verify(hash_obj, signature)
            return True # ยืนยันสำเร็จ (Valid)
        
        except (ValueError, TypeError):
            # โยน Exception ออกมาถ้า Hash ไม่ตรงกัน (Invalid)
            return False