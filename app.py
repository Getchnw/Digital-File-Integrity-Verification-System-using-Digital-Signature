import streamlit as st
from core_signature import DigitalSignatureCore
import qrcode
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Digital Signature System", layout="wide")
st.title("🔐 Digital File Integrity System")
st.markdown("ระบบตรวจสอบความถูกต้องของไฟล์ด้วย Digital Signature (RSA + SHA-256)")

# เมนูด้านข้าง
menu = st.sidebar.radio("เลือกการทำงาน", ["1. สร้างกุญแจ (Key Gen)", "2. เซ็นไฟล์ (Sign File)", "3. ตรวจสอบไฟล์ (Verify)"])

if menu == "1. สร้างกุญแจ (Key Gen)":
    st.header("🔑 สร้างคู่กุญแจ (RSA Key Pair)")
    st.info("Private Key เก็บไว้เซ็นไฟล์ (ห้ามให้ใครรู้) | Public Key แจกให้คนอื่นเพื่อใช้ตรวจสอบ")
    
    # 1. เช็คว่ามีตัวแปรเก็บ Key ใน session_state หรือยัง ถ้ายังให้สร้างเตรียมไว้
    if 'priv_key' not in st.session_state:
        st.session_state['priv_key'] = None
    if 'pub_key' not in st.session_state:
        st.session_state['pub_key'] = None

    # 2. เมื่อกดปุ่ม ให้สร้าง Key แล้วเก็บลง session_state
    if st.button("Generate Keys"):
        priv, pub = DigitalSignatureCore.generate_keys()
        st.session_state['priv_key'] = priv
        st.session_state['pub_key'] = pub
        
    # 3. นำ Key จาก session_state มาแสดงผล (จะไม่หายไปไหนเวลากดโหลด)
    if st.session_state['priv_key'] is not None and st.session_state['pub_key'] is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Private Key")
            st.code(st.session_state['priv_key'].decode('utf-8'))
            st.download_button("ดาวน์โหลด Private Key", st.session_state['priv_key'], file_name="private_key.pem")
        with col2:
            st.subheader("Public Key")
            st.code(st.session_state['pub_key'].decode('utf-8'))
            st.download_button("ดาวน์โหลด Public Key", st.session_state['pub_key'], file_name="public_key.pem")

elif menu == "2. เซ็นไฟล์ (Sign File)":
    st.header("✍️ ลงลายมือชื่อดิจิทัล (Sign File)")
    
    priv_file = st.file_uploader("1. อัปโหลด Private Key (.pem)", type=['pem'])
    
    # 1. เพิ่ม accept_multiple_files=True
    target_files = st.file_uploader(
        "2. อัปโหลดไฟล์ที่ต้องการเซ็น (เลือกได้หลายไฟล์)", 
        type=['pdf', 'docx', 'png', 'jpg', 'txt'],
        accept_multiple_files=True
    )
    
    if priv_file and target_files:
        if st.button("Sign All Documents"):
            priv_key_data = priv_file.read()
            
            # 2. วนลูปประมวลผลไฟล์ที่อัปโหลดมาทั้งหมด
            for uploaded_file in target_files:
                file_data = uploaded_file.read()
                
                # เซ็นไฟล์
                signature = DigitalSignatureCore.sign_file(priv_key_data, file_data)
                
                # แสดงผลแยกตามไฟล์ด้วย st.expander เพื่อความสะอาดตา
                with st.expander(f"📄 ผลลัพธ์สำหรับไฟล์: {uploaded_file.name}"):
                    st.success(f"✅ เซ็นไฟล์ {uploaded_file.name} สำเร็จ!")
                    st.text_area(f"Digital Signature (Base64) - {uploaded_file.name}", signature, height=100)
                    
                    # สร้าง QR Code
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(signature)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(byte_im, width=200, caption=f"QR Code: {uploaded_file.name}")
                    with col2:
                        st.download_button(
                            label=f"ดาวน์โหลด QR Code ({uploaded_file.name})",
                            data=byte_im,
                            file_name=f"sig_{uploaded_file.name}.png",
                            mime="image/png",
                            key=f"btn_{uploaded_file.name}" # ต้องระบุ key ให้ต่างกันในแต่ละไฟล์
                        )

elif menu == "3. ตรวจสอบไฟล์ (Verify)":
    st.header("🛡️ ตรวจสอบไฟล์ (Batch Verification & Visual Report)")
    
    pub_file = st.file_uploader("1. อัปโหลด Public Key ของผู้ส่ง", type=['pem'])
    qr_file = st.file_uploader("2. อัปโหลด QR Code Signature", type=['png', 'jpg', 'jpeg'])
    
    # รองรับ Batch Verification (อัปโหลดหลายไฟล์พร้อมกัน)
    target_files = st.file_uploader("3. อัปโหลดไฟล์ที่ต้องการตรวจสอบ (เลือกได้หลายไฟล์)", accept_multiple_files=True)
    
    if pub_file and qr_file and target_files:
        if st.button("Verify Now"):
            pub_key_data = pub_file.read()
            
            # อ่าน Signature จาก QR Code
            img = Image.open(qr_file)
            decoded_objects = decode(img)
            
            if not decoded_objects:
                st.error("❌ ไม่สามารถอ่าน QR Code ได้ กรุณาใช้รูป QR Code ที่ชัดเจน")
            else:
                signature = decoded_objects[0].data.decode('utf-8')
                
                st.markdown("---")
                st.subheader("📊 Visual Trust Report")
                
                # วนลูปตรวจทุกไฟล์ (Batch)
                for file in target_files:
                    file_data = file.read()
                    is_valid = DigitalSignatureCore.verify_file(pub_key_data, file_data, signature)
                    
                    # Tamper Highlight & Visual Report
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    file_size = len(file_data) / 1024 # KB
                    
                    if is_valid:
                        st.success(f"✅ **PASS:** `{file.name}` (ขนาด: {file_size:.2f} KB)")
                        st.caption(f"Verified at: {timestamp} | Integrity: Intact | Authenticity: Verified")
                    else:
                        st.error(f"🚨 **FAIL:** `{file.name}` (ขนาด: {file_size:.2f} KB)")
                        st.caption(f"Verified at: {timestamp} | Integrity: Compromised! ไฟล์ถูกดัดแปลงหรือใช้ Key ผิด")