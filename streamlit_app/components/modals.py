import json
import streamlit as st
from core.storage_service import save_templates

@st.dialog("📁 Sao lưu & Khôi phục Thư viện mẫu")
def show_backup_restore_dialog(templates):
    st.subheader("📥 Khôi phục dữ liệu (Import)")
    st.caption("Chọn tệp templates.json từ máy tính để nạp danh sách bài tập mới:")
    uploaded_file = st.file_uploader(
        "Chọn tệp templates.json",
        type=["json"],
        key="modal_templates_uploader"
    )
    if st.button("🔌 Áp dụng dữ liệu mới", use_container_width=True, type="primary"):
        if uploaded_file is not None:
            try:
                uploaded_templates = json.load(uploaded_file)
                if isinstance(uploaded_templates, dict):
                    save_templates(uploaded_templates)
                    st.session_state.templates_crud_success = "✅ Đã nạp danh sách bài tập mới thành công!"
                    st.rerun()
                else:
                    st.error("Cấu trúc file templates.json không hợp lệ.")
            except Exception as e:
                st.error(f"Lỗi đọc file: {str(e)}")
        else:
            st.warning("Vui lòng chọn tệp templates.json trước khi bấm áp dụng.")
            
    st.markdown("---")
    st.subheader("📤 Sao lưu dữ liệu (Export)")
    st.caption("Tải tệp templates.json hiện tại về máy tính để sao lưu:")
    templates_data = json.dumps(templates, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Tải xuống templates.json",
        data=templates_data,
        file_name="templates.json",
        mime="application/json",
        use_container_width=True
    )

@st.dialog("📚 Chọn đề bài từ Thư viện mẫu")
def show_template_loader_dialog(templates):
    chapters = list(templates.keys())
    selected_chapter = st.selectbox("Chọn Chương", chapters, key="modal_grader_select_chapter")
    
    sessions = list(templates[selected_chapter].keys()) if selected_chapter else []
    selected_session = st.selectbox("Chọn Session", sessions, key="modal_grader_select_session")
    
    assignments_list = list(templates[selected_chapter][selected_session].keys()) if selected_chapter and selected_session else []
    selected_assignment = st.selectbox("Chọn Bài tập", assignments_list, key="modal_grader_select_assignment")
    
    if selected_chapter and selected_session and selected_assignment:
        data = templates[selected_chapter][selected_session][selected_assignment]
        st.markdown("**Xem trước đề bài:**")
        st.info(data["assignment"][:250] + ("..." if len(data["assignment"]) > 250 else ""))
        
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 Nạp đề bài", use_container_width=True, type="primary"):
            if selected_chapter and selected_session and selected_assignment:
                data = templates[selected_chapter][selected_session][selected_assignment]
                st.session_state.assignment_val = data["assignment"]
                st.session_state.criteria_val = data["criteria"]
                st.session_state.selected_chapter_name = selected_chapter
                st.session_state.selected_session_name = selected_session
                st.session_state.selected_assignment_name = selected_assignment
                st.session_state.template_load_success_msg = "✅ Đã nạp đề bài và tiêu chí thành công!"
                st.rerun()
    with col2:
        if st.button("Hủy bỏ", use_container_width=True):
            st.rerun()

@st.dialog("➕ Thêm đề bài mới")
def show_add_assignment_dialog(templates):
    # 1. Chapter Selection / Input
    chapter_options = []
    if templates:
        chapter_options = ["Chọn chương hiện có", "Nhập chương mới"]
    else:
        chapter_options = ["Nhập chương mới"]
        
    chapter_mode = st.radio("Tùy chọn Chương:", chapter_options, horizontal=True)
    if chapter_mode == "Chọn chương hiện có":
        selected_chapter = st.selectbox("Chọn Chương hiện có *", list(templates.keys()), key="modal_add_select_chapter")
        chapter_name = selected_chapter
    else:
        chapter_name = st.text_input("Tên Chương mới *", placeholder="Ví dụ: Chương [ IT211 - K24 ] Java Web Service")

    # 2. Session Selection / Input
    has_existing_sessions = templates and chapter_name in templates and templates[chapter_name]
    session_options = []
    if has_existing_sessions:
        session_options = ["Chọn session hiện có", "Nhập session mới"]
    else:
        session_options = ["Nhập session mới"]
        
    session_mode = st.radio("Tùy chọn Session:", session_options, horizontal=True)
    if session_mode == "Chọn session hiện có":
        selected_session = st.selectbox("Chọn Session hiện có *", list(templates[chapter_name].keys()), key="modal_add_select_session")
        session_name = selected_session
    else:
        session_name = st.text_input("Tên Session mới *", placeholder="Ví dụ: Session 19: Spring Security")

    # 3. Exercise details
    new_title = st.text_input("Tên Bài tập *", placeholder="Ví dụ: Bài tập 1 (JWT & Security)")
    new_assignment = st.text_area("Đề bài bài tập *", height=120)
    new_criteria = st.text_area("Tiêu chí chấm điểm *", height=100)
    
    if st.button("Thêm bài tập", use_container_width=True, type="primary"):
        if chapter_name and session_name and new_title and new_assignment and new_criteria:
            c_name = chapter_name.strip()
            s_name = session_name.strip()
            t_title = new_title.strip()
            
            if c_name not in templates:
                templates[c_name] = {}
            if s_name not in templates[c_name]:
                templates[c_name][s_name] = {}
            
            templates[c_name][s_name][t_title] = {
                "assignment": new_assignment,
                "criteria": new_criteria
            }
            if save_templates(templates):
                st.session_state.templates_crud_success = "✅ Đã thêm mẫu bài tập thành công!"
                st.rerun()
            else:
                st.error("Lỗi khi lưu dữ liệu.")
        else:
            st.warning("Vui lòng điền đầy đủ các thông tin bắt buộc (*).")

@st.dialog("✏️ Chỉnh sửa đề bài")
def show_edit_assignment_dialog(templates):
    if not templates:
        st.info("Chưa có mẫu nào để sửa.")
        return
        
    edit_chapter = st.selectbox("Chọn Chương", list(templates.keys()), key="modal_edit_c")
    edit_session = st.selectbox("Chọn Session", list(templates[edit_chapter].keys()) if edit_chapter else [], key="modal_edit_s")
    edit_title = st.selectbox("Chọn Bài tập", list(templates[edit_chapter][edit_session].keys()) if edit_chapter and edit_session else [], key="modal_edit_t")
    
    if edit_chapter and edit_session and edit_title:
        current_data = templates[edit_chapter][edit_session][edit_title]
        updated_assignment = st.text_area("Đề bài mới", value=current_data["assignment"], height=120)
        updated_criteria = st.text_area("Tiêu chí chấm điểm mới", value=current_data["criteria"], height=100)
        
        if st.button("Lưu thay đổi", use_container_width=True, type="primary"):
            templates[edit_chapter][edit_session][edit_title] = {
                "assignment": updated_assignment,
                "criteria": updated_criteria
            }
            if save_templates(templates):
                st.session_state.templates_crud_success = "✅ Đã cập nhật mẫu bài tập thành công!"
                st.rerun()
            else:
                st.error("Lỗi khi lưu dữ liệu.")

@st.dialog("🗑️ Xóa bài tập")
def show_delete_assignment_dialog(templates):
    if not templates:
        st.info("Chưa có mẫu nào để xóa.")
        return
        
    del_chapter = st.selectbox("Chọn Chương muốn xóa", list(templates.keys()), key="modal_del_c")
    del_session = st.selectbox("Chọn Session muốn xóa", list(templates[del_chapter].keys()) if del_chapter else [], key="modal_del_s")
    del_title = st.selectbox("Chọn Bài tập muốn xóa", list(templates[del_chapter][del_session].keys()) if del_chapter and del_session else [], key="modal_del_t")
    
    if del_chapter and del_session and del_title:
        st.warning(f"Bạn có chắc chắn muốn xóa bài tập '{del_title}' thuộc Session '{del_session}'?")
        if st.button("Xác nhận xóa bài tập", use_container_width=True, type="primary"):
            del templates[del_chapter][del_session][del_title]
            if not templates[del_chapter][del_session]:
                del templates[del_chapter][del_session]
            if not templates[del_chapter]:
                del templates[del_chapter]
            
            if save_templates(templates):
                st.session_state.templates_crud_success = "✅ Đã xóa mẫu bài tập thành công!"
                st.rerun()
            else:
                st.error("Lỗi khi lưu dữ liệu.")
