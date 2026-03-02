import streamlit as st
from core_signature import DigitalSignatureCore
import qrcode
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
import datetime
import json

st.set_page_config(page_title="Digital Signature System", layout="wide")

# CSS จัดการพื้นที่
st.markdown("""
    <style>
        div[data-testid="stUploadedFileList"] { max-height: 250px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🔐 Digital File Integrity System")
st.markdown("ระบบตรวจสอบความถูกต้องของไฟล์ด้วย Digital Signature (RSA + SHA-256)")

menu = st.sidebar.radio("เลือกการทำงาน", ["1. สร้างกุญแจ (Key Gen)", "2. เซ็นไฟล์ (Sign File)", "3. ตรวจสอบไฟล์ (Verify)"])

if menu == "1. สร้างกุญแจ (Key Gen)":
    st.header("🔑 สร้างคู่กุญแจ (RSA Key Pair)")
    if 'priv_key' not in st.session_state:
        st.session_state['priv_key'], st.session_state['pub_key'] = None, None

    if st.button("Generate Keys"):
        priv, pub = DigitalSignatureCore.generate_keys()
        st.session_state['priv_key'] = priv
        st.session_state['pub_key'] = pub
        
    if st.session_state['priv_key']:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Private Key")
            # นำส่วนแสดงผลกลับมา
            st.code(st.session_state['priv_key'].decode('utf-8')) 
            st.download_button("ดาวน์โหลด Private Key", st.session_state['priv_key'], file_name="private_key.pem")
        with col2:
            st.subheader("Public Key")
            # นำส่วนแสดงผลกลับมา
            st.code(st.session_state['pub_key'].decode('utf-8')) 
            st.download_button("ดาวน์โหลด Public Key", st.session_state['pub_key'], file_name="public_key.pem")

elif menu == "2. เซ็นไฟล์ (Sign File)":
    st.header("✍️ ลงลายมือชื่อดิจิทัล (Sign File)")
    
    # --- 1. เตรียมกล่องเก็บผลลัพธ์ใน Session State ---
    if 'signed_results' not in st.session_state:
        st.session_state['signed_results'] = []
    
    signer_name = st.text_input("ชื่อผู้ลงนาม (Signer Name)", placeholder="เช่น นายสมชาย หรือ แผนก IT")
    priv_file = st.file_uploader("1. อัปโหลด Private Key (.pem)", type=['pem'])
    target_files = st.file_uploader("2. อัปโหลดไฟล์ที่ต้องการเซ็น (เลือกได้หลายไฟล์)", accept_multiple_files=True)
    
    if priv_file and target_files and signer_name:
        if st.button("Sign All Documents"):
            priv_key_data = priv_file.read()
            
            # เคลียร์ผลลัพธ์เก่าทิ้งทุกครั้งที่กดเซ็นใหม่
            st.session_state['signed_results'] = []
            
            for uploaded_file in target_files:
                file_data = uploaded_file.read()
                try:
                    signature = DigitalSignatureCore.sign_file(priv_key_data, file_data)
                    
                    # ห่อ Metadata ใส่ JSON
                    metadata = {
                        "file_name": uploaded_file.name,
                        "signer": signer_name,
                        "signed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "signature": signature
                    }
                    json_data = json.dumps(metadata, ensure_ascii=False)
                    
                    # สร้าง QR Code แบบ Dynamic Version
                    qr = qrcode.QRCode(
                        version=None, 
                        error_correction=qrcode.constants.ERROR_CORRECT_L, 
                        box_size=4, 
                        border=2
                    )
                    qr.add_data(json_data)
                    qr.make(fit=True)
                    
                    buf = BytesIO()
                    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
                    qr_bytes = buf.getvalue()
                    
                    # --- 2. เก็บผลลัพธ์ทั้งหมดลง Session State ---
                    st.session_state['signed_results'].append({
                        "file_name": uploaded_file.name,
                        "json_data": json_data,
                        "qr_bytes": qr_bytes,
                        "status": "success"
                    })

                except ValueError as e:
                    # เก็บสถานะ Error ลง Session State ด้วย
                    st.session_state['signed_results'].append({
                        "file_name": uploaded_file.name,
                        "error_msg": str(e),
                        "status": "error"
                    })

        # --- 3. แสดงผลลัพธ์จาก Session State (อยู่นอก if st.button) ---
        if st.session_state['signed_results']:
            for result in st.session_state['signed_results']:
                if result["status"] == "success":
                    with st.expander(f"📄 ผลลัพธ์: {result['file_name']}", expanded=True):
                        st.success(f"✅ เซ็นไฟล์สำเร็จ!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(result['qr_bytes'], width=200, caption=f"QR Code: {result['file_name']}")
                        with col2:
                            # พอเรากดโหลดหน้าเว็บจะ Refresh แต่มันจะเข้ามาอ่านข้อมูลจาก Session State มาแสดงต่อได้
                            st.download_button(
                                "1️⃣ โหลด QR Code", 
                                result['qr_bytes'], 
                                file_name=f"qr_{result['file_name']}.png", 
                                mime="image/png", 
                                key=f"qr_{result['file_name']}"
                            )
                            st.download_button(
                                "2️⃣ โหลดไฟล์ Signature (.json)", 
                                result['json_data'].encode('utf-8'), 
                                file_name=f"{result['file_name']}.json", 
                                mime="application/json", 
                                key=f"json_{result['file_name']}"
                            )
                            st.caption("แนะนำให้โหลด .json ไปใช้สำหรับตรวจเช็คแบบ Batch ครับ")
                else:
                    st.error(f"❌ กุญแจผิดพลาดสำหรับ {result['file_name']}: {result['error_msg']}")
                    
elif menu == "3. ตรวจสอบไฟล์ (Verify)":
    st.header("🛡️ ตรวจสอบไฟล์ (Batch Verification & Visual Report)")
    st.info("คุณสามารถอัปโหลดไฟล์ Signature แบบ .json พร้อมกันหลายไฟล์เพื่อเช็ค Batch หรือใช้รูป QR Code ทีละไฟล์ก็ได้")
    
    pub_file = st.file_uploader("1. อัปโหลด Public Key ของผู้ส่ง", type=['pem'])
    sig_files = st.file_uploader("2. อัปโหลด Signature (.json) หรือ QR Code", type=['json', 'png', 'jpg'], accept_multiple_files=True)
    target_files = st.file_uploader("3. อัปโหลดไฟล์ต้นฉบับที่ต้องการตรวจ", accept_multiple_files=True)
    
    if st.button("Verify Now") and pub_file and sig_files and target_files:
        pub_key_data = pub_file.read()
        
        # จัดเตรียม Dictionary เก็บ Signature ตามชื่อไฟล์
        signatures_dict = {}
        for sf in sig_files:
            if sf.name.endswith('.json'):
                data = json.loads(sf.read().decode('utf-8'))
                signatures_dict[data.get('file_name', sf.name)] = data
            else: # กรณีเป็น QR Image
                decoded = decode(Image.open(sf))
                if decoded:
                    try:
                        data = json.loads(decoded[0].data.decode('utf-8'))
                        signatures_dict[data.get('file_name', sf.name)] = data
                    except:
                        st.error(f"ข้อมูลใน QR {sf.name} ไม่ถูกต้อง")

        st.markdown("---")
        st.subheader("📊 Visual Trust Report")
        
        for file in target_files:
            file_data = file.read()
            meta = signatures_dict.get(file.name)
            
            if not meta:
                st.warning(f"⚠️ ข้ามไฟล์ `{file.name}` (ไม่พบ Signature หรือ QR ที่ตรงกับชื่อไฟล์นี้)")
                continue
                
            status = DigitalSignatureCore.verify_file(pub_key_data, file_data, meta['signature'])
            file_size = len(file_data) / 1024
            
            if status == "VALID":
                st.success(f"✅ **PASS:** `{file.name}` ({file_size:.2f} KB)")
                st.caption(f"✍️ ลงนามโดย: **{meta['signer']}** | 🕒 เวลา: {meta['signed_at']} | Integrity: Intact")
            elif status == "TAMPERED_OR_WRONG_KEY":
                st.error(f"🚨 **FAIL:** `{file.name}` ({file_size:.2f} KB)")
                st.caption(f"ข้อมูลอ้างอิง: ลงนามโดย {meta.get('signer', 'Unknown')} | สาเหตุ: ไฟล์ถูกดัดแปลง หรือ ไม่ใช่กุญแจของผู้ส่งตัวจริง")
            else:
                st.error(f"❌ **ERROR:** `{file.name}` (รูปแบบ Public Key ไม่ถูกต้อง)")