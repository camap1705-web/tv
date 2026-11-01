# Ghi đè toàn bộ file app.py hoàn chỉnh, bổ sung tài khoản mặc định và tối ưu đăng nhập
import os

app_hoan_chinh_moi = r'''
import os
import time
import sqlite3
import streamlit as st
from google import genai
from google.genai import types
from docx import Document
from io import BytesIO

st.set_page_config(
    page_title="AI Education KHKT - Đề Thi Chuyên Sâu",
    page_icon="🎓",
    layout="wide"
)

# ----------------- DATABASE SQLITE -----------------
def init_db():
    conn = sqlite3.connect("users_data.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        subject TEXT,
        topic TEXT,
        level TEXT,
        max_score INTEGER,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Tự động tạo một tài khoản mặc định (admin / admin123) nếu chưa tồn tại
    try:
        c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', 'admin123')")
    except Exception:
        pass

    conn.commit()
    conn.close()

init_db()

def register_user(username, password):
    try:
        conn = sqlite3.connect("users_data.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    conn = sqlite3.connect("users_data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

# ----------------- SESSION STATE -----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# ----------------- LOGIN / REGISTER -----------------
if not st.session_state["logged_in"]:
    st.title("🎓 Chào mừng bạn đến với AI Education KHKT")
    st.info("💡 Tài khoản dùng thử mặc định có sẵn: Tên tài khoản: admin | Mật khẩu: admin123")
    tab1, tab2 = st.tabs(["🔑 Đăng Nhập", "📝 Đăng Ký Tài Khoản"])

    with tab1:
        st.subheader("Đăng nhập hệ thống")
        login_user = st.text_input("Tên tài khoản", key="login_user_input")
        login_pass = st.text_input("Mật khẩu", type="password", key="login_pass_input")
        if st.button("Đăng Nhập", use_container_width=True):
            if verify_user(login_user.strip(), login_pass.strip()):
                st.session_state["logged_in"] = True
                st.session_state["username"] = login_user.strip()
                st.success(f"Đăng nhập thành công! Chào mừng {login_user}.")
                st.rerun()
            else:
                st.error("Sai tên tài khoản hoặc mật khẩu!")

    with tab2:
        st.subheader("Tạo tài khoản mới")
        reg_user = st.text_input("Nhập tên tài khoản mong muốn", key="reg_user_input")
        reg_pass = st.text_input("Nhập mật khẩu", type="password", key="reg_pass_input")
        if st.button("Đăng Ký", use_container_width=True):
            if reg_user and reg_pass:
                if register_user(reg_user.strip(), reg_pass.strip()):
                    st.success("Đăng ký thành công! Hãy chuyển sang Tab Đăng Nhập.")
                else:
                    st.error("Tài khoản đã tồn tại trên hệ thống!")
            else:
                st.warning("Vui lòng điền đầy đủ thông tin!")

# ----------------- MAIN APPLICATION -----------------
else:
    st.sidebar.title(f"👤 Chào, {st.session_state['username']}!")
    if st.sidebar.button("Đăng Xuất", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.title("🧠 Trợ Lý AI - Tạo Đề Thi Chuyên Sâu & Lưu Trữ")

    main_tab, archive_tab = st.tabs(["⚡ Tạo Đề Thi Mới", "📂 Lưu Trữ Đề Thi & Tải Về (WPS)"])

    # TAB 1: TẠO ĐỀ THI MỚI
    with main_tab:
        st.subheader("Thiết lập các thông số đề thi của bạn")

        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("1. Chọn Môn Học:", ["Toán Học", "Vật Lý", "Hóa Học", "Sinh Học", "Tiếng Anh", "Ngữ Văn"])
            topic = st.text_input("2. Tên Bài / Chủ Đề Chi Tiết:", placeholder="Ví dụ: Khảo sát hàm số, Câu điều kiện loại 2,...")

        with col2:
            level = st.selectbox("3. Mức Độ Nhận Thức:", ["Dễ (Nhận biết)", "Trung bình (Thông hiểu)", "Khó (Vận dụng)", "Cực khó (Vận dụng cao)"])
            max_score = st.selectbox("4. Thang Điểm Đề Thi:", [7, 8, 9, 10])

        if st.button("🚀 Bắt Đầu Tạo Đề Thi", use_container_width=True):
            if not topic:
                st.warning("Vui lòng điền 'Tên Bài / Chủ Đề Chi Tiết' trước khi bắt đầu!")
            else:
                with st.spinner("AI đang thiết kế đề thi chuyên sâu siêu tốc..."):
                    try:
                        api_key = os.environ.get("GEMINI_API_KEY", "")
                        client = genai.Client(api_key=api_key)

                        prompt = (
                            f"Biên soạn một đề thi môn {subject} dành cho bài học/chủ đề: '{topic}'. "
                            f"Yêu cầu độ khó: {level}. Thang điểm tối đa của đề thi là: {max_score} điểm. "
                            f"Bố cục rõ ràng, chia rõ tỷ lệ câu hỏi tương ứng để đạt tối đa {max_score} điểm. "
                            f"Trình bày thành 2 phần: "
                            f"Phần 1: Đề bài kiểm tra, Phần 2: Đáp án chi tiết và hướng dẫn giải."
                        )

                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.3,
                                max_output_tokens=3000,
                            )
                        )

                        exam_content = response.text

                        conn = sqlite3.connect("users_data.db")
                        c = conn.cursor()
                        c.execute("""INSERT INTO exams (username, subject, topic, level, max_score, content)
                                  VALUES (?, ?, ?, ?, ?, ?)""",
                                  (st.session_state["username"], subject, topic, level, max_score, exam_content))
                        conn.commit()
                        conn.close()

                        st.success("🎉 Đã biên soạn đề thi thành công! Đề đã được tự động lưu vào hệ thống lưu trữ.")
                        st.text_area("Xem trước nội dung đề thi từ AI:", value=exam_content, height=400)

                    except Exception as e:
                        st.error(f"Đã xảy ra lỗi khi tạo đề thi: {str(e)}")

    # TAB 2: LƯU TRỮ VÀ TẢI VỀ
    with archive_tab:
        st.subheader("Danh sách toàn bộ đề thi đã được tạo của bạn")

        conn = sqlite3.connect("users_data.db")
        c = conn.cursor()
        c.execute("SELECT id, subject, topic, level, max_score, content, created_at FROM exams WHERE username=? ORDER BY created_at DESC", (st.session_state["username"],))
        rows = c.fetchall()
        conn.close()

        if not rows:
            st.info("Bạn chưa tạo đề thi nào. Hãy sang tab 'Tạo Đề Thi Mới' để bắt đầu nhé!")
        else:
            for row in rows:
                exam_id, sub, top, lvl, score, content, date_created = row

                with st.expander(f"📚 {sub} - {top} (Thang điểm: {score}đ | Ngày tạo: {date_created})"):
                    st.write(f"**Môn:** {sub} | **Chủ đề:** {top}")
                    st.write(f"**Mức độ:** {lvl} | **Thang điểm tối đa:** {score} điểm")
                    st.markdown("--- ")
                    st.text_area("Nội dung chi tiết:", value=content, height=250, key=f"text_{exam_id}")

                    # Xuất Word (.docx)
                    doc = Document()
                    doc.add_heading(f"ĐỀ THI MÔN {sub.upper()}", 1)
                    doc.add_paragraph(f"Chủ đề: {top}")
                    doc.add_paragraph(f"Mức độ: {lvl} | Thang điểm: {score}đ")
                    doc.add_paragraph("----------------------------------------------------")

                    for line in content.split('\n'):
                        doc.add_paragraph(line)

                    docx_buffer = BytesIO()
                    doc.save(docx_buffer)
                    docx_buffer.seek(0)

                    file_name_output = f"De_Thi_{sub}_{exam_id}.docx".replace(" ", "_")
                    st.download_button(
                        label=f"📥 Tải về file Word (.docx / WPS) cho đề này",
                        data=docx_buffer,
                        file_name=file_name_output,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_{exam_id}"
                    )
'''

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_hoan_chinh_moi)

print("Đã thiết lập tài khoản mặc định và tối ưu hóa hệ thống đăng nhập thành công!")
