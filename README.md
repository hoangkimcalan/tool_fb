
# Tool Facebook Automation

## Giới thiệu
Tool này là một công cụ tự động hóa các thao tác trên Facebook, sử dụng Selenium WebDriver để điều khiển trình duyệt Chrome. Công cụ hỗ trợ các chức năng như: đăng nhập, lưu/đọc cookie, thả cảm xúc, bình luận, chia sẻ bài viết, đăng bài mới, nhắn tin, kết bạn, lướt Facebook, xem thông báo, v.v. Mục tiêu là giúp người dùng tiết kiệm thời gian và thao tác lặp lại trên Facebook, đặc biệt phù hợp cho các hoạt động marketing, tuyển dụng, chăm sóc khách hàng, hoặc quản lý nhiều tài khoản.

## Cấu trúc thư mục

```
├── convert.py
├── cookies4.pkl
├── fb_cookies.json
├── ntd_converted.wav
├── ntd.m4a
├── README.md
├── requirements.txt
├── toolfacebook.py         # File chính chứa các hàm tự động hóa Facebook
├── toolfacebook.spec
├── user_accounts.json      # Danh sách tài khoản Facebook sử dụng cho tool
├── utils.py                # Các hàm tiện ích hỗ trợ thao tác trình duyệt, log, ẩn process...
├── api/
│   └── api_service.py
├── build/
│   └── ...
└── __pycache__/
```

## Yêu cầu hệ thống
- Windows OS
- Python 3.10+
- Google Chrome
- ChromeDriver (tự động cài qua webdriver_manager)

## Cài đặt
1. Cài Python và Chrome.
2. Cài các thư viện cần thiết:
	```bash
	pip install -r requirements.txt
	```
3. Đảm bảo file `user_accounts.json` đã có thông tin tài khoản Facebook.


## Hướng dẫn sử dụng
### 1. Chạy tool với 1 tài khoản Facebook (Test nhanh)
Giả sử bạn muốn test tool với một tài khoản trong file `user_accounts.json`:
1. Mở file `user_accounts.json`, kiểm tra hoặc thêm tài khoản Facebook cần test (bao gồm user, pass, 2FA nếu có).
2. Đảm bảo tài khoản này chưa bị checkpoint hoặc khóa.
3. Chạy tool:
	 ```bash
	 python toolfacebook.py
	 ```
4. Tool sẽ tự động lấy tài khoản đầu tiên trong danh sách để đăng nhập và thực hiện các thao tác tự động (hoặc bạn có thể chỉnh sửa code để chọn tài khoản cụ thể).
5. Kiểm tra log trong `assets/logs/toolfacebook.log` để xem chi tiết quá trình chạy.

### 2. Sử dụng với nhiều tài khoản
- Có thể thêm nhiều tài khoản vào `user_accounts.json`, tool sẽ lần lượt thao tác với từng tài khoản (hoặc tùy chỉnh theo nhu cầu).

### 3. Map tài khoản Facebook với user app chat365_pc
Tool này được thiết kế để nhúng vào ứng dụng chat365_pc. File `user_accounts.json` dùng để ánh xạ (map) giữa user_id của hệ thống chat365 với tài khoản Facebook tương ứng:

- Trường `user_id_QLC`: ID người dùng trên hệ thống quản lý chat365.
- Trường `user_id_chat`: ID người dùng trên hệ thống chat.
- Trường `facebook_username`, `facebook_password`, `facebook_2fa_code`: Thông tin đăng nhập Facebook.
- Trường `note`: Ghi chú phân biệt tài khoản.

**Cơ chế hoạt động khi nhúng vào app chat365_pc:**
- Khi người dùng đăng nhập hoặc khởi chạy app chat365_pc, app sẽ lấy user_id hiện tại, tra cứu trong `user_accounts.json` để lấy thông tin tài khoản Facebook tương ứng.
- Tool sẽ tự động khởi động trình duyệt, đăng nhập Facebook bằng tài khoản đã map, sẵn sàng thực hiện các thao tác tự động hóa (gửi tin nhắn, tương tác, v.v) theo kịch bản của app chat.
- Điều này giúp mỗi user trên chat365_pc có thể gắn với một tài khoản Facebook riêng biệt, phục vụ cho các tính năng như gửi tin nhắn Facebook, tự động hóa marketing, chăm sóc khách hàng, v.v.

### 4. Lưu ý khi tích hợp
- Đảm bảo bảo mật file `user_accounts.json`, không để lộ thông tin tài khoản.
- Có thể mở rộng thêm các trường khác trong file JSON để phục vụ nhu cầu tích hợp sâu hơn với app chat365_pc.

## Ví dụ cấu trúc 1 entry trong `user_accounts.json`
```json
{
	"user_id_QLC": "22615833",
	"user_id_chat": "10406031", 
	"facebook_username": "gianvu17607@gmail.com",
	"facebook_password": "lvqh1234",
	"facebook_2fa_code": "",
	"note": "Chị Dung"
}
```

## Luồng hoạt động tổng quát
1. **Khởi tạo:**
	- Ẩn process, thiết lập môi trường, chuẩn bị log.
2. **Đăng nhập Facebook:**
	- Đọc cookie từ file (nếu có) để đăng nhập nhanh.
	- Nếu cookie hết hạn, đăng nhập bằng tài khoản và mật khẩu, có hỗ trợ 2FA.
	- Lưu lại cookie mới sau khi đăng nhập thành công.
3. **Thực hiện các thao tác tự động:**
	- Thả cảm xúc (Like, Love, Care, ...)
	- Bình luận bài viết (random nội dung)
	- Chia sẻ bài viết
	- Đăng bài mới lên news feed
	- Lướt Facebook, xem video, gửi tin nhắn, kết bạn, đọc thông báo...
4. **Log hoạt động:**
	- Ghi log chi tiết quá trình chạy vào thư mục `assets/logs/toolfacebook.log`.

## Giải thích các file chính
- `toolfacebook.py`: Chứa các hàm chính để tự động hóa Facebook, gồm:
  - Đăng nhập, lưu/đọc cookie
  - Thả cảm xúc, bình luận, chia sẻ, đăng bài, nhắn tin, kết bạn, lướt Facebook, đọc thông báo
- `user_accounts.json`: Danh sách tài khoản Facebook (user, pass, 2FA, note...)
- `utils.py`: Các hàm hỗ trợ như: gõ text tự nhiên, cuộn mượt, log, ẩn process, chạy quyền admin...
- `requirements.txt`: Danh sách thư viện Python cần cài đặt

## Mô tả các chức năng chính

### 1. Đăng nhập & Quản lý Cookie
- **load_cookies(browser):** Đọc cookie từ file JSON, giúp đăng nhập nhanh không cần nhập lại tài khoản.
- **save_cookies(browser):** Lưu cookie mới sau khi đăng nhập thành công.
- **login(username, password, code_2fa, browser):** Đăng nhập Facebook, tự động nhập 2FA nếu có.

### 2. Tương tác bài viết
- **react_post(browser):** Thả cảm xúc (Like, Love, Care, ...)
- **comment_post(browser, actions):** Bình luận bài viết với nội dung ngẫu nhiên.
- **share_post(browser, actions):** Chia sẻ bài viết với nội dung ngẫu nhiên.

### 3. Đăng bài mới
- **post_news_feed(browser):** Đăng bài mới lên news feed với nội dung random.

### 4. Nhắn tin, kết bạn, lướt Facebook
- **list_friend(browser):** Lấy danh sách bạn bè, gửi tin nhắn ngẫu nhiên.
- **send_message(browser, link_user, content):** Nhắn tin cho một người cụ thể.
- **add_friend(browser):** Gửi lời mời kết bạn.
- **surf_facebook(id, title, browser):** Lướt dạo Facebook theo kịch bản.

### 5. Xem thông báo
- **read_notification(browser):** Đọc thông báo Facebook.

### 6. Tiện ích hỗ trợ (utils.py)
- **type_text_input(element, text):** Gõ text tự nhiên như người thật.
- **smooth_scroll(browser, start, end, duration):** Cuộn trang mượt mà.
- **log_message(message, level):** Ghi log hoạt động.
- **hide_process(), run_as_trusted(), initialize():** Ẩn process, chạy quyền admin, khởi tạo môi trường.

## Tùy biến & mở rộng
- Có thể chỉnh sửa nội dung bình luận, chia sẻ, bài đăng trong các biến COMMENTS, SHARE_POSTS, CONTENT_POST ở đầu file `toolfacebook.py`.
- Có thể thêm tài khoản mới vào `user_accounts.json`.
- Có thể mở rộng thêm các hàm tự động hóa khác theo nhu cầu.

## Lưu ý bảo mật
- Không chia sẻ file `user_accounts.json` cho người khác.
- Không public mã nguồn chứa thông tin tài khoản thật lên internet.

## Liên hệ & hỗ trợ
- Nếu cần hỗ trợ hoặc muốn đóng góp, vui lòng liên hệ tác giả qua email hoặc github.
