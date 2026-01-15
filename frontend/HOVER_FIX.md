# Sửa Lỗi Hover Tooltip trong Streamlit

## Vấn đề
Hover tooltip không hoạt động vì:
1. **Iframe bị render lại nhiều lần**: Streamlit rerun toàn bộ trang mỗi khi có thay đổi
2. **DOM state bị reset**: Mỗi lần rerun, iframe mới được tạo, JavaScript state bị mất
3. **Tooltip position: fixed bị reset**: Vị trí tooltip không được giữ lại

## Giải pháp

### 1. Thêm Message ID System
```python
if "message_counter" not in st.session_state:
    st.session_state.message_counter = 0
```
- Mỗi message có ID duy nhất và ổn định
- ID không thay đổi khi Streamlit rerun

### 2. Sử dụng `key` Parameter trong components.html
```python
components.html(html_content, height=estimated_height, scrolling=True, key=f"citation_{message_id}")
```
- `key` parameter ngăn Streamlit render lại iframe khi không cần thiết
- Iframe chỉ được tạo mới khi message_id thay đổi
- JavaScript state được giữ nguyên giữa các lần rerun

### 3. Cải thiện JavaScript
- **Thêm click handler**: Cho phép toggle tooltip bằng click
- **Thêm scroll handler**: Giữ tooltip khi scroll
- **Cải thiện positioning**: Tooltip tự động hiển thị bên dưới nếu không đủ chỗ ở trên
- **Thêm pointer-events: none**: Ngăn tooltip chặn sự kiện chuột

### 4. Enable Scrolling
```python
scrolling=True
```
- Cho phép cuộn nội dung nếu quá dài
- Overflow được xử lý đúng cách

## Kết quả
✅ Hover tooltip hoạt động ổn định
✅ Không bị reset khi Streamlit rerun
✅ Click để toggle tooltip
✅ Tự động điều chỉnh vị trí khi không đủ không gian
✅ Hoạt động mượt mà với scroll

## Các thay đổi chính

1. **app.py line 18-21**: Thêm message_counter vào session state
2. **app.py line 184**: Thêm parameter message_id vào function
3. **app.py line 190-192**: Generate stable message ID
4. **app.py line 444**: Thêm key parameter và enable scrolling
5. **app.py line 327**: Thêm currentTooltip tracking
6. **app.py line 367**: Thêm click event listener
7. **app.py line 411-415**: Cải thiện tooltip positioning
8. **app.py line 433-440**: Thêm scroll handler
9. **app.py line 650**: Pass message ID khi render history
10. **app.py line 662-669**: Thêm ID cho user message
11. **app.py line 701-705**: Thêm ID cho assistant message
