import pytest
from core_signature import DigitalSignatureCore

def test_key_generation():
    priv, pub = DigitalSignatureCore.generate_keys()
    assert b"PRIVATE KEY" in priv
    assert b"PUBLIC KEY" in pub

def test_valid_signature_flow():
    # 1. สร้าง Key
    priv, pub = DigitalSignatureCore.generate_keys()
    
    # 2. จำลองไฟล์
    original_file = b"This is a strictly confidential document."
    
    # 3. เซ็นไฟล์
    signature = DigitalSignatureCore.sign_file(priv, original_file)
    
    # 4. ตรวจสอบ (ต้องผ่าน)
    is_valid = DigitalSignatureCore.verify_file(pub, original_file, signature)
    assert is_valid == True

def test_tampered_file_rejected():
    priv, pub = DigitalSignatureCore.generate_keys()
    original_file = b"Transfer 100 USD to John"
    signature = DigitalSignatureCore.sign_file(priv, original_file)
    
    # แฮกเกอร์แอบแก้ไฟล์ระหว่างทาง
    hacked_file = b"Transfer 999 USD to Hacker"
    
    # ตรวจสอบ (ต้องไม่ผ่าน)
    is_valid = DigitalSignatureCore.verify_file(pub, hacked_file, signature)
    assert is_valid == False

def test_wrong_public_key_rejected():
    # ผู้ส่งตัวจริง
    priv1, pub1 = DigitalSignatureCore.generate_keys()
    # ผู้สวมรอย
    priv2, pub2 = DigitalSignatureCore.generate_keys()
    
    file_data = b"Hello World"
    
    # เซ็นด้วยกุญแจคนสวมรอย
    signature_hacker = DigitalSignatureCore.sign_file(priv2, file_data)
    
    # คนรับพยายามตรวจด้วยกุญแจคนส่งตัวจริง (ต้องไม่ผ่าน เพราะไม่ใช่คนเดียวกันเซ็น)
    is_valid = DigitalSignatureCore.verify_file(pub1, file_data, signature_hacker)
    assert is_valid == False