import asyncio
import random
import time
import traceback
import json
import os
import re
import time
import logging
from datetime import datetime
import os
import logging
import sys
import websockets
import aiohttp
import aiofiles
import re
import asyncio
import websockets
from datetime import datetime
import pyperclip
import csv
import psutil
import pandas as pd
from datetime import timedelta
from api import create_post, create_comment, create_reply_comment

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from post_structure_manager import *
from personal_post_manager import *

from utils import hide_process, initialize, log_message, run_as_trusted, smooth_scroll, type_text_input

COOKIE_FILENAME = "fb_cookies.json"
POST_STRUCTURE_FILENAME = "post_structure.json"

DEFAULT_COOKIE_DATA = "{}"
DEFAULT_POST_STRUCTURE_DATA = '{"posts": {}}'

# Lấy đường dẫn thư mục APPDATA trên Windows hoặc thư mục tương đương trên các OS khác
if sys.platform == "win32":
    appdata_path = os.getenv("APPDATA")
elif sys.platform == "darwin":  # macOS
    appdata_path = os.path.expanduser("~/Library/Application Support")
else:  # Linux
    appdata_path = os.path.expanduser("~/.config")

# Tạo đường dẫn đầy đủ đến các file
COOKIE_FILE = os.path.join(appdata_path, COOKIE_FILENAME)
POST_STRUCTURE_FILE = os.path.join(appdata_path, POST_STRUCTURE_FILENAME)

# Kiểm tra và tạo file fb_cookies.json
if not os.path.exists(COOKIE_FILE):
    print(f"File {COOKIE_FILE} not found. Creating a new one...")
    try:
        with open(COOKIE_FILE, "w") as f:
            f.write(DEFAULT_COOKIE_DATA)
    except IOError as e:
        print(f"Error creating file {COOKIE_FILE}: {e}")

# Kiểm tra và tạo file post_structure.json
if not os.path.exists(POST_STRUCTURE_FILE):
    print(f"File {POST_STRUCTURE_FILE} not found. Creating a new one...")
    try:
        with open(POST_STRUCTURE_FILE, "w") as f:
            f.write(DEFAULT_POST_STRUCTURE_DATA)
    except IOError as e:
        print(f"Error creating file {POST_STRUCTURE_FILE}: {e}")

# Các hằng số khác (không thay đổi)
# WEBSOCKET_URL = "ws://123.24.206.25:4000"
WEBSOCKET_URL = "ws://localhost:4000"
URL_IMAGE = "http://192.168.0.116:4000"


# Cấu hình cào comment
MAX_POSTS_TO_CRAWL = 30  # Số lượng bài mới nhất sẽ được cào comment

# Queue để lưu nội dung từ WebSocket
pending_posts = []
# Flag để dừng lướt khi có tin mới
stop_browsing = False
# Lưu client_id để sử dụng lại khi gửi URL
current_client_id = None
# Lưu thông tin tài khoản hiện tại
current_account_data = None

# Biến đếm số lần kết bạn và quản lý thời gian
friend_request_count = 0
friend_request_date = None
MAX_FRIEND_REQUESTS_PER_DAY = 30

# Biến global để theo dõi thời gian cào comment tự động
last_auto_crawl_time = None
AUTO_CRAWL_INTERVAL = 8000 

COMMENTS = [
    "Danh sách ứng viên trên Timviec365 thật sự rất chất lượng!",
    "Bạn nào đã sử dụng Timviec365 chưa? Đánh giá thế nào?",
    "Công cụ tìm ứng viên của Timviec365 rất tiện lợi, dễ sử dụng!",
    "Mình đã tìm được ứng viên phù hợp trên Timviec365, mọi người thử xem nhé!",
    "Trang web này rất hữu ích cho ai đang tìm việc!",
    "Bạn đã thử tìm việc trên Timviec365 chưa? Hãy chia sẻ trải nghiệm của bạn!",
    "Cảm ơn Timviec365 đã giúp tôi tìm được công việc phù hợp!",
    "Có ai có kinh nghiệm sử dụng Timviec365 không?",
    "Tìm việc nhanh chóng và hiệu quả trên Timviec365!",
    "Mọi người đã tìm được công việc tốt trên Timviec365 chưa?",
    "Cần tìm việc gấp, ai có kinh nghiệm chỉ giúp với!",
    "Làm thế nào để nâng cao hồ sơ ứng tuyển trên Timviec365?",
    "Timviec365 có những ưu điểm gì so với các trang tìm việc khác?",
    "Bạn có biết cách tối ưu CV để tăng cơ hội phỏng vấn không?",
    "Timviec365 có hỗ trợ ứng viên mới không?",
    "Mình đã nhận được nhiều cơ hội nhờ Timviec365, cảm ơn rất nhiều!",
    "Làm sao để tìm được công việc phù hợp với kỹ năng của mình?",
    "Có ai đã thành công tìm việc qua Timviec365 chưa?",
    "Bạn có kinh nghiệm gì khi phỏng vấn không?",
    "Chia sẻ mẹo giúp ứng tuyển thành công trên Timviec365 nhé!"
]

SHARE_POSTS = [
    "Cơ hội việc làm tuyệt vời! Hãy thử ngay trên Timviec365!",
    "Bạn đang tìm kiếm công việc? Timviec365 có thể giúp bạn!",
    "Nhiều cơ hội việc làm hấp dẫn đang chờ bạn trên Timviec365!",
    "Hãy chia sẻ công cụ hữu ích này đến bạn bè của bạn!",
    "Timviec365 - nơi giúp bạn kết nối với nhà tuyển dụng nhanh chóng!",
    "Bạn đã tìm việc hôm nay chưa? Đừng bỏ lỡ cơ hội trên Timviec365!",
    "Công cụ tìm việc miễn phí và hiệu quả trên Timviec365!",
    "Chia sẻ ngay để bạn bè của bạn cũng tìm được việc làm phù hợp!",
    "Nhiều công ty đang tuyển dụng trên Timviec365, đừng bỏ lỡ!",
    "Timviec365 giúp bạn dễ dàng tìm kiếm công việc phù hợp!",
    "Ứng tuyển nhanh chóng, không mất thời gian!",
    "Hàng ngàn việc làm mới được cập nhật mỗi ngày trên Timviec365!",
    "Bạn đang muốn thay đổi công việc? Hãy thử ngay Timviec365!",
    "Nhà tuyển dụng đang chờ đón bạn! Ứng tuyển ngay trên Timviec365!",
    "Hỗ trợ ứng viên tìm việc miễn phí và dễ dàng!",
    "Chia sẻ kinh nghiệm tìm việc hiệu quả trên Timviec365!",
    "Timviec365 giúp bạn kết nối với nhà tuyển dụng một cách nhanh chóng!",
    "Bạn đã thử tìm việc bằng Timviec365 chưa? Kết quả sẽ bất ngờ đấy!",
    "Hãy bắt đầu sự nghiệp mới của bạn ngay trên Timviec365!"
]

REACTIONS = [
    {"name": "Like", "xpath": '//div[@aria-label="Thích"] | //div[@aria-label="Like"]'},
    {"name": "Love", "xpath": '//div[@aria-label="Yêu thích"] | //div[@aria-label="Love"]'},
    {"name": "Care", "xpath": '//div[@aria-label="Thương thương"] | //div[@aria-label="Care"]'},
    {"name": "Haha", "xpath": '//div[@aria-label="Haha"]'},
    {"name": "Wow", "xpath": '//div[@aria-label="Wow"]'},
    {"name": "Sad", "xpath": '//div[@aria-label="Buồn"] | //div[@aria-label="Sad"]'},
    {"name": "Angry", "xpath": '//div[@aria-label="Phẫn nộ"] | //div[@aria-label="Angry"]'}
]

# Hàm lấy thông tin tài khoản hiện tại từ user_accounts.json
def get_current_account():
    """Lấy thông tin tài khoản hiện tại từ biến global current_account_data"""
    global current_account_data
    return current_account_data

# Hàm lấy tên Facebook từ tài khoản hiện tại
def get_facebook_name():
    """Lấy tên Facebook từ tài khoản hiện tại trong user_accounts.json"""
    try:
        acc = get_current_account()
        if acc:
            # Ưu tiên nameFb, nếu không có thì dùng note
            if "nameFb" in acc and acc["nameFb"]:
                return acc["nameFb"]
            elif "note" in acc and acc["note"]:
                return acc["note"]
        return "Unknown"
    except Exception as e:
        log_message(f"Không thể đọc tên từ user_accounts.json: {e}", logging.WARNING)
        return "Unknown"

# Hàm lấy roleWebSocket từ tài khoản hiện tại
def get_websocket_role():
    """Lấy roleWebSocket từ tài khoản hiện tại trong user_accounts.json"""
    try:
        acc = get_current_account()
        if acc and "roleWebSocket" in acc and acc["roleWebSocket"]:
            return acc["roleWebSocket"]
        return "B"  # Mặc định
    except Exception as e:
        log_message(f"Không thể đọc roleWebSocket từ user_accounts.json: {e}", logging.WARNING)
        return "B"

# Hàm lấy trường "to" từ tài khoản hiện tại
def get_id_tosend_websocket():
    """Lấy trường 'to' từ tài khoản hiện tại trong user_accounts.json"""
    try:
        acc = get_current_account()
        if acc and "to" in acc and acc["to"]:
            return acc["to"]
        return ""  # Mặc định
    except Exception as e:
        log_message(f"Không thể đọc trường 'to' từ user_accounts.json: {e}", logging.WARNING)
        return ""

# Hàm lấy thông tin đăng nhập từ tài khoản hiện tại
def get_login_credentials():
    """Lấy thông tin đăng nhập từ tài khoản hiện tại trong user_accounts.json"""
    try:
        acc = get_current_account()
        if acc:
            return {
                "username": acc.get("facebook_username", ""),
                "password": acc.get("facebook_password", ""),
                "code_2fa": acc.get("facebook_2fa_code", ""),
                "note": acc.get("note", ""),
                "user_id_QLC": acc.get("user_id_QLC", ""),
                "user_id_chat": acc.get("user_id_chat", "")
            }
        return None
    except Exception as e:
        log_message(f"Không thể đọc thông tin đăng nhập từ user_accounts.json: {e}", logging.ERROR)
        return None

# Hàm quản lý đếm số lần kết bạn
def reset_friend_request_counter():
    """Reset counter nếu sang ngày mới"""
    global friend_request_count, friend_request_date
    current_date = datetime.now().date()
    
    if friend_request_date is None or friend_request_date != current_date:
        friend_request_count = 0
        friend_request_date = current_date
        log_message(f"🔄 Reset counter kết bạn cho ngày mới: {current_date}", logging.INFO)
        return True
    return False

def increment_friend_request_counter():
    """Tăng counter số lần kết bạn"""
    global friend_request_count
    friend_request_count += 1
    log_message(f" Đã kết bạn lần thứ {friend_request_count}/{MAX_FRIEND_REQUESTS_PER_DAY} trong ngày", logging.INFO)
    return friend_request_count

def can_send_friend_request():
    """Kiểm tra có thể gửi lời mời kết bạn không"""
    reset_friend_request_counter()
    return friend_request_count < MAX_FRIEND_REQUESTS_PER_DAY

def get_friend_request_status():
    """Lấy thông tin trạng thái kết bạn"""
    reset_friend_request_counter()
    remaining = MAX_FRIEND_REQUESTS_PER_DAY - friend_request_count
    return {
        "count": friend_request_count,
        "max": MAX_FRIEND_REQUESTS_PER_DAY,
        "remaining": remaining,
        "date": friend_request_date.isoformat() if friend_request_date else None
    }

async def send_friend_request_status_to_websocket():
    """Gửi thông tin trạng thái kết bạn qua WebSocket"""
    try:
        status = get_friend_request_status()
        status_data = {
            "type": "friend_request_status",
            "status": status,
            "authorName": get_facebook_name(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Thêm thông tin user_id từ tài khoản hiện tại
        user_ids = get_id_tosend_websocket()
        status_data["to"] = user_ids
        
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            await websocket.send(json.dumps(status_data))
            log_message("✅ Đã gửi thông tin trạng thái kết bạn qua WebSocket!", logging.INFO)
    except Exception as e:
        log_message(f"❌ Lỗi khi gửi trạng thái kết bạn qua WebSocket: {e}", logging.ERROR)


# Hàm kết nối WebSocket để nhận nội dung mới với auto-reconnect
async def connect_websocket():
    """Kết nối WebSocket để nhận nội dung bài viết mới với khả năng tự động kết nối lại"""
    global stop_browsing, current_client_id
    
    # Đọc role từ tài khoản hiện tại
    current_client_id = get_websocket_role()
    log_message(f"Sử dụng roleWebSocket: {current_client_id}", logging.INFO)
    
    reconnect_interval = 5  # Thời gian chờ trước khi kết nối lại (giây)
    max_reconnect_interval = 60  # Thời gian chờ tối đa
    
    while True:  # Vòng lặp vô hạn để tự động kết nối lại
        try:
            log_message("Đang thử kết nối tới WebSocket server...", logging.INFO)
            
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                log_message("Đã kết nối thành công tới WebSocket server!", logging.INFO)
                
                # Reset reconnect interval khi kết nối thành công
                reconnect_interval = 5
                
                # Gửi tin nhắn đăng ký
                register_message = {
                    "type": "register",
                    "clientId": current_client_id,
                    "to": get_id_tosend_websocket(),
                }
                await websocket.send(json.dumps(register_message))
                log_message(f"Đã gửi tin nhắn đăng ký với clientId: {current_client_id}", logging.INFO)
                
                # Lắng nghe tin nhắn từ server
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "new_post":
                            log_message(f"Nhận được nội dung mới từ WebSocket: {data.get('content', '')[:50]}...", logging.INFO)
                            
                            # Xử lý attachments nếu có
                            attachments = data.get("attachments", [])
                            downloaded_images = []
                            
                            if attachments:
                                log_message(f"Phát hiện {len(attachments)} attachments", logging.INFO)
                                for attachment in attachments:
                                    if attachment.get("type", "").startswith("image"):
                                        image_url = attachment.get("url")
                                        image_name = attachment.get("name", f"image_{int(time.time())}.jpg")
                                        
                                        if image_url:
                                            log_message(f"Đang tải ảnh: {image_name} từ {image_url}", logging.INFO)
                                            downloaded_path = await download_image(image_url, image_name)
                                            if downloaded_path:
                                                downloaded_images.append(downloaded_path)
                            
                            # Thêm thông tin ảnh vào data
                            data["downloaded_images"] = downloaded_images
                            
                            pending_posts.append(data)
                            # Set flag để dừng lướt và chuyển sang đăng bài
                            global stop_browsing
                            stop_browsing = True
                            log_message("Đã set flag để dừng lướt và chuyển sang đăng bài", logging.INFO)
                            
                        elif data.get("type") == "comment":
                            log_message(f"Nhận được yêu cầu bình luận từ WebSocket: {data.get('content', '')[:50]}...", logging.INFO)
                            log_message(f"URL bài viết: {data.get('URL', 'N/A')}", logging.INFO)
                            
                            pending_posts.append(data)
                            # Set flag để dừng lướt và chuyển sang bình luận
                            stop_browsing = True
                            log_message("Đã set flag để dừng lướt và chuyển sang bình luận", logging.INFO)
                            
                        elif data.get("type") == "reply_comment":
                            log_message(f"Nhận được yêu cầu phản hồi bình luận từ WebSocket: {data.get('content', '')[:50]}...", logging.INFO)
                            log_message(f"URL bài viết: {data.get('URL', 'N/A')}", logging.INFO)
                            
                            pending_posts.append(data)
                            # Set flag để dừng lướt và chuyển sang bình luận
                            stop_browsing = True
                            log_message("Đã set flag để dừng lướt và chuyển sang bình luận", logging.INFO)
                            
                        elif data.get("type") == "reply_reply_comment":
                            log_message(f"Nhận được yêu cầu trả lời reply comment từ WebSocket: {data.get('content', '')[:50]}...", logging.INFO)
                            log_message(f"URL: {data.get('URL', 'N/A')}", logging.INFO)
                            log_message(f"CommentId: {data.get('commentId', 'N/A')}", logging.INFO)
                            log_message(f"ReplyId: {data.get('replyId', 'N/A')}", logging.INFO)
                            
                            pending_posts.append(data)
                            # Set flag để dừng lướt và chuyển sang trả lời reply
                            stop_browsing = True
                            log_message("Đã set flag để dừng lướt và chuyển sang trả lời reply", logging.INFO)
                            
                        elif data.get("type") == "crawl_comment_by_CRM":
                            log_message(f"Nhận được yêu cầu cào comment từ CRM: facebookId={data.get('facebookId', 'N/A')}, authorId={data.get('authorId', 'N/A')}", logging.INFO)
                            
                            pending_posts.append(data)
                            # Set flag để dừng lướt và chuyển sang cào comment tự động
                            stop_browsing = True
                            log_message("Đã set flag để dừng lướt và chuyển sang cào comment tự động từ CRM", logging.INFO)
                            
                        elif data.get("type") == "register_success":
                            log_message("Đăng ký WebSocket thành công!", logging.INFO)
                        else:
                            log_message(f"Nhận được tin nhắn WebSocket khác: {data.get('type', 'unknown')}", logging.INFO)
                            
                    except json.JSONDecodeError:
                        log_message(f"Lỗi decode JSON từ WebSocket: {message}", logging.ERROR)
                        
        except websockets.exceptions.ConnectionClosed:
            log_message("WebSocket connection bị đóng. Sẽ thử kết nối lại...", logging.WARNING)
        except websockets.exceptions.InvalidStatusCode as e:
            log_message(f"WebSocket status code không hợp lệ: {e}. Sẽ thử kết nối lại...", logging.ERROR)
        except websockets.exceptions.WebSocketException as e:
            log_message(f"WebSocket error: {e}. Sẽ thử kết nối lại...", logging.ERROR)
        except Exception as e:
            log_message(f"Lỗi kết nối WebSocket: {e}. Sẽ thử kết nối lại...", logging.ERROR)
        
        # Đợi trước khi thử kết nối lại
        log_message(f"Đợi {reconnect_interval} giây trước khi kết nối lại WebSocket...", logging.INFO)
        await asyncio.sleep(reconnect_interval)
        
        # Tăng thời gian chờ dần để tránh spam kết nối
        reconnect_interval = min(reconnect_interval * 1.5, max_reconnect_interval)
        
        log_message("Đang thử kết nối lại WebSocket...", logging.INFO)

# Hàm tải ảnh từ URL
async def download_image(url, filename):
    """Tải ảnh từ URL về thư mục temp của user"""
    try:
        import aiohttp
        import aiofiles
        
        # Sử dụng thư mục temp của user thay vì ProgramData
        DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "fb_images")
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        log_message(f"Thư mục lưu ảnh: {DOWNLOAD_FOLDER}", logging.INFO)
        
        url_image = URL_IMAGE + url
        # Đường dẫn đầy đủ của file
        filename = filename + '.png'
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        log_message(f"Đường dẫn file sẽ lưu: {file_path}", logging.INFO)
        
        # Tải ảnh bằng aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url_image) as response:
                if response.status == 200:
                    # Ghi file bằng aiofiles
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024):
                            await f.write(chunk)
                    
                    log_message(f"Đã tải ảnh thành công: {file_path}", logging.INFO)
                    return file_path
                else:
                    log_message(f"Lỗi tải ảnh: HTTP {response.status}", logging.ERROR)
                    return None
    except Exception as e:
        log_message(f"Lỗi khi tải ảnh từ {url_image}: {e}", logging.ERROR)
        return None


# lưu cookie lại mỗi khi đăng nhập thành công
async def save_cookies(browser):
    """Lưu cookies vào file JSON"""
    cookies = browser.get_cookies()
    if cookies:
        # Lọc chỉ giữ cookie chưa hết hạn
        valid_cookies = [cookie for cookie in cookies if 'expiry' not in cookie or cookie['expiry'] > time.time()]
        
        with open(COOKIE_FILE, "w") as file:
            json.dump(valid_cookies, file, indent=4)

        log_message("Cookies saved successfully!")
    else:
        log_message("No cookies to save.", logging.ERROR)

# load cookie từ file JSON để tránh đăng nhập lại
async def load_cookies(browser):
    """Nạp cookies từ file JSON"""
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
        try:
            with open(COOKIE_FILE, "r") as file:
                cookies = json.load(file)
            
            # Lọc chỉ giữ cookie chưa hết hạn
            valid_cookies = [cookie for cookie in cookies if 'expiry' not in cookie or cookie['expiry'] > time.time()]
            
            if valid_cookies:
                allowed_samesite = ["Strict", "Lax", "None"]
                for cookie in valid_cookies:
                    # Sửa hoặc xóa trường sameSite nếu không hợp lệ
                    if "sameSite" in cookie and cookie["sameSite"] not in allowed_samesite:
                        log_message(f"Cookie sameSite không hợp lệ: {cookie['sameSite']}, sẽ xóa trường này", logging.INFO)
                        del cookie["sameSite"]
                    browser.add_cookie(cookie)

                # Nếu có cookie hết hạn, cập nhật lại file JSON
                if len(valid_cookies) < len(cookies):
                    with open(COOKIE_FILE, "w") as file:
                        json.dump(valid_cookies, file, indent=4)
                    log_message("Expired cookies removed and updated JSON file.")

                log_message("Valid cookies loaded successfully!")
            else:
                log_message("All cookies have expired. Deleting cookie file...", logging.WARNING)
                os.remove(COOKIE_FILE)

        except json.JSONDecodeError:
            log_message("Corrupted cookie file. Deleting...", logging.ERROR)
            os.remove(COOKIE_FILE)
    return False

# Hàm đăng nhập Facebook
async def login(username, password, code_2fa, browser):
    try:
        """Hàm đăng nhập Facebook với async/await"""
        txtUser = browser.find_element(By.ID, 'email')
        await type_text_input(txtUser, username)
        await asyncio.sleep(random.uniform(1, 3))

        txtPassword = browser.find_element(By.ID, 'pass')
        await type_text_input(txtPassword, password)
        await asyncio.sleep(random.uniform(1, 3))

        txtPassword.send_keys(Keys.ENTER)
        await asyncio.sleep(random.uniform(5, 8))
        
        if '"userID":' in browser.page_source:
            log_message("Login successful!")
            await save_cookies(browser)
            # Reload Facebook homepage after successful login
            browser.get("https://facebook.com/")
            await asyncio.sleep(3)
    except Exception as e:
        log_message(f"Login failed: {e}",logging.ERROR)


#Hàm react_post
async def react_post(browser):
    """Chức năng thả reaction cho bài viết"""
    try:
        # 1. Tìm nút 'Like' ban đầu (Thích/Like)
        # Sử dụng WebDriverWait để chờ nút Like xuất hiện và có thể click được.
        like_button = None
        try:
            like_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Thích" or @aria-label="Like") and @role="button"]'))
            )
        except Exception:
            log_message("Không tìm thấy nút Thích/Like để tương tác.", logging.WARNING)
            return

        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
        await asyncio.sleep(2)

        selected_reaction = random.choice(REACTIONS)
        log_message(f"Selected reaction: {selected_reaction['name']}")

        # 2. Di chuột qua nút 'Like' để hiển thị các reaction options
        actions = ActionChains(browser)
        actions.move_to_element(like_button).perform()
        await asyncio.sleep(4)  # Đợi đủ thời gian cho các reaction options xuất hiện

        # 3. Tìm nút reaction cụ thể
        reaction_button = None
        # Xây dựng XPath cho nút reaction đã chọn.
        # Facebook có thể dùng aria-label chính xác hoặc aria-label có chứa số lượng người đã reaction.
        # Chúng ta sẽ thử cả hai trường hợp.
        
        # Thử XPath chính xác trước
        exact_xpath = selected_reaction['xpath']
        
        try:
            reaction_button = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, exact_xpath))
            )
            log_message(f"Found reaction button with exact xpath for {selected_reaction['name']}")
        except Exception:
            log_message(f"Không tìm thấy reaction button chính xác cho '{selected_reaction['name']}'. Thử XPath chứa từ khóa.", logging.INFO)
            # Nếu không tìm thấy bằng XPath chính xác, thử tìm bằng aria-label chứa tên reaction
            # Ví dụ: "Yêu thích: 123 người"
            containing_xpath = f'//div[@role="button" and contains(@aria-label, "{selected_reaction["name"]}")]'
            try:
                reaction_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, containing_xpath))
                )
                log_message(f"Found reaction button with containing xpath for {selected_reaction['name']}")
            except Exception:
                log_message(f"Hoàn toàn không tìm thấy reaction button cho '{selected_reaction['name']}'.", logging.WARNING)
                traceback.print_exc() # In chi tiết lỗi để debug nếu cần
                return

        if not reaction_button:
            log_message(f"Không tìm thấy reaction button với aria-label='{selected_reaction['name']}' sau khi hover.", logging.WARNING)
            return

        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
        await asyncio.sleep(1)
        
        # 4. Click vào nút reaction
        actions.move_to_element(reaction_button)
        actions.click()
        actions.perform()
        log_message(f"Đã thả cảm xúc '{selected_reaction['name']}' thành công!")
        await asyncio.sleep(random.uniform(2, 3))

    except Exception as e:
        log_message(f"Lỗi trong hàm react_post: {e}", logging.ERROR)
        traceback.print_exc()
        pass

# Hàm bình luận bài viết
async def comment_post(browser, actions):
    try:
        await asyncio.sleep(random.uniform(2, 4))
        comment_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Viết bình luận" or @aria-label="Leave a comment") and @role="button"]')
        for btn in comment_buttons:
            if btn.is_displayed() and btn.is_enabled():
                comment_button = btn
                break
        if not comment_button:
            # Không tìm thấy nút bình luận, bỏ qua
            return
        # Scroll nút bình luận vào view
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_button)
        await asyncio.sleep(2)
        actions.move_to_element(comment_button)
        actions.click()
        actions.perform()
        # Chọn ngẫu nhiên một bình luận
        comment_text = random.choice(COMMENTS)
        await asyncio.sleep(random.uniform(2, 4))
        # Tìm comment box để nhập text
        wait = WebDriverWait(browser, 10)
        comment_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
        await asyncio.sleep(1)
        # Tìm thẻ p trong comment box
        p_tag = comment_box.find_element(By.TAG_NAME, "p")
        await asyncio.sleep(2)
        actions.send_keys_to_element(p_tag, comment_text)
        await asyncio.sleep(random.uniform(2, 4))
        actions.send_keys(Keys.ENTER)
        actions.perform()  
        await asyncio.sleep(2)
        actions.send_keys(Keys.ESCAPE).perform()
    except Exception as e:
        log_message(f"Error in comment_post: {e}", logging.ERROR)
        traceback.print_exc()

# Hàm chia sẻ bài viết
async def share_post(browser, actions):
    try:
        share_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn." or @aria-label="Send this to friends or post it on your profile.") and @role="button"]')
        for btn in share_buttons:
            if btn.is_displayed() and btn.is_enabled():
                share_button = btn
                break
        if not share_button:
            return
        # Scroll nút chia sẻ vào view
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
        await asyncio.sleep(2)
        # Click vào nút chia sẻ
        actions.move_to_element(share_button)
        actions.click()
        actions.perform()

        await asyncio.sleep(5)
        # Tìm và click nút "Chia sẻ ngay"
        share_now_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Chia sẻ ngay" or @aria-label="Share now") and @role="button"]'))
        )
        actions.move_to_element(share_now_button)
        actions.click()
        actions.perform()
        log_message("Đã chia sẻ bài viết thành công!")
        await asyncio.sleep(random.uniform(2, 3))
    except Exception as e:
        log_message(f"Error in share_post: {e}", logging.ERROR)
        traceback.print_exc()

async def watch_videos(browser, actions):
    try:
        browser.get("https://www.facebook.com/watch/")
        await asyncio.sleep(random.uniform(3, 6))
        scroll_count_video = random.randint(6, 15)  # Số lần cuộn #fix
        while scroll_count_video > 0:
            # Kiểm tra flag để dừng xem video khi có tin mới từ WebSocket
            global stop_browsing
            if stop_browsing:
                log_message("Dừng xem video do nhận được tin mới từ WebSocket", logging.INFO)
                break
                
            log_message(f"scroll_count_watch_video {scroll_count_video}")

            await asyncio.sleep(random.uniform(4, 7))

            # Tìm tất cả video trên trang
            video_selected = browser.find_elements(By.XPATH, "//div[contains(@class, 'x1ey2m1c') and contains(@class, 'x9f619')]")

            # Lọc các video đang hiển thị
            visible_videos = [video for video in video_selected if video.is_displayed()]
            await asyncio.sleep(random.uniform(40, 60))

            if visible_videos:
                log_message(f"Found {len(visible_videos)} visible videos.")
                current_video = visible_videos[0]

                # Nếu scroll_count_video chia hết cho 7 hoặc 13 thì thực hiện hành động
                if scroll_count_video % 7 == 0 or scroll_count_video % 13 == 0:
                    if scroll_count_video % 7 == 0:
                        await asyncio.sleep(random.uniform(5, 7))
                        # Tìm nút like sử dụng selector đã được test thành công
                        like_buttons = browser.find_elements(By.XPATH, "//span[@data-ad-rendering-role='like_button']")
                        for btn in like_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                like_button = btn
                                break
                        if like_button:
                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
                            await asyncio.sleep(random.uniform(1, 3))
                            like_button.click()
                            log_message("Liked the post video successfully!")
                        else:
                            log_message("Like button is not visible, skipping...")

                    elif scroll_count_video % 13 == 0:
                        await share_post(browser, actions)
                        await asyncio.sleep(random.uniform(3, 5))
                        
                    await asyncio.sleep(random.uniform(2, 5))

                    # Sau khi like hoặc share, click vào video để lấy URL
                    actions.move_to_element(current_video).click().perform()
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Lấy URL video đã tương tác
                    video_url = browser.current_url
                    log_message(f"current_url: {video_url}")
            else:
                log_message("No visible videos found, continuing...")

            # Cuộn trang để xem video tiếp theo
            scroll_count_video -= 1

            # Thực hiện cuộn trang với hiệu ứng mượt mà
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 800)
            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))
                
        log_message("Đã hoàn thành xem video Facebook")
        
    except Exception as err:
        log_message(f"err watch videos {err}", logging.ERROR)
        traceback.print_exc()


# Hàm xem danh sách bạn bè + send message cho bạn bè (random)
async def list_friend(browser):
    try:
        # Kiểm tra flag ngay từ đầu
        global stop_browsing
        if stop_browsing:
            log_message("Dừng list_friend do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        # Kiểm tra xem có nội dung từ WebSocket không
        if not pending_posts:
            log_message("Không có nội dung từ WebSocket để gửi tin nhắn. Bỏ qua việc nhắn tin.", logging.WARNING)
            return
        
        # Lấy nội dung từ WebSocket
        post_data = pending_posts.pop(0)
        content = post_data.get("content", "")
        
        if not content:
            log_message("Nội dung từ WebSocket rỗng. Bỏ qua việc gửi tin nhắn.", logging.WARNING)
            return
        
        list_friend = []
        browser.get("https://www.facebook.com/friends/list")
        await asyncio.sleep(random.uniform(2, 4))
        
        # Kiểm tra flag sau khi tải trang
        if stop_browsing:
            log_message("Dừng list_friend sau khi tải trang danh sách bạn bè do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        friends_box = browser.find_element(By.XPATH, "//div[@class='x135pmgq']")
        log_message(f"friends_box: {friends_box}")
        await asyncio.sleep(random.uniform(1, 3))
        
        # Kiểm tra flag trước khi tìm link bạn bè
        if stop_browsing:
            log_message("Dừng list_friend trước khi tìm link bạn bè do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        # Có thể xóa debug log thẻ <a> nếu muốn gọn log
        friends_link = friends_box.find_elements(By.XPATH, ".//a[contains(@class, 'x1qjc9v5') and contains(@class, 'xjbqb8w') and contains(@class, 'xde0f50') and contains(@class, 'x1lliihq')]")

        for link in friends_link:
            link_friend = link.get_attribute('href')
            if link_friend:
                list_friend.append(link_friend)
        
        await asyncio.sleep(random.uniform(4, 6))
        
        # Kiểm tra flag trước khi gửi tin nhắn
        if stop_browsing:
            log_message("Dừng list_friend trước khi gửi tin nhắn do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        log_message(f"list_friend: {list_friend}")
        if not list_friend:
            log_message("Không tìm thấy bạn bè nào trong danh sách!", logging.WARNING)
            return
        await send_message(browser, random.choice(list_friend), content)
        
        
    except Exception as err:
        log_message(f"err list_friend {err}", logging.ERROR)
        traceback.print_exc()
        pass

# Hàm nhắn tin cho một bạn
async def send_message(browser, link_user, content):
    try:
        # Kiểm tra flag ngay từ đầu
        global stop_browsing
        if stop_browsing:
            log_message("Dừng send_message do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        browser.get(link_user)
        await asyncio.sleep(random.uniform(4, 6))
        
        # Kiểm tra flag sau khi tải trang
        if stop_browsing:
            log_message("Dừng send_message sau khi tải trang profile do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        actions = ActionChains(browser)
        try:
            send_button = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Nhắn tin"]')
        except:
            try:
                send_button = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Message"]')
            except:
                log_message("Không tìm thấy nút nhắn tin!", logging.ERROR)
                return
        
        # Kiểm tra flag trước khi click nút nhắn tin
        if stop_browsing:
            log_message("Dừng send_message trước khi click nút nhắn tin do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        send_button.click()
        await asyncio.sleep(random.uniform(2, 4))
        # Tìm ô nhập tin nhắn
        post_box = None
        try:
            post_box = WebDriverWait(browser, 12).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"))
            )
        except Exception as e:
            # Nếu không tìm thấy, thử lại
            try:
                post_box = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Nhắn tin'][contenteditable='true'][role='textbox']"))
                )
            except:
                post_box = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Message'][contenteditable='true'][role='textbox']"))
                )
        await asyncio.sleep(3)
        
        # Kiểm tra flag trước khi nhập tin nhắn
        if stop_browsing:
            log_message("Dừng send_message trước khi nhập tin nhắn do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        p_tag = post_box.find_element(By.TAG_NAME, "p")
        await asyncio.sleep(random.uniform(2, 4))
        if p_tag and p_tag.is_displayed():
            actions.send_keys_to_element(p_tag, content)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Kiểm tra flag trước khi gửi
            if stop_browsing:
                log_message("Dừng send_message trước khi gửi tin nhắn do nhận được tin mới từ WebSocket", logging.INFO)
                return
                
            actions.send_keys(Keys.ENTER)
            actions.perform()
            await asyncio.sleep(2)
            log_message("Tin nhắn đã được gửi thành công!")
        await asyncio.sleep(2)
        actions.send_keys(Keys.ESCAPE).perform()
    except Exception as err:
        log_message(f"err send_message {err}", logging.ERROR)
        traceback.print_exc()

async def add_friend(browser):
    try:
        # Kiểm tra flag ngay từ đầu
        global stop_browsing
        if stop_browsing:
            log_message("Dừng add_friend do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        # Kiểm tra giới hạn kết bạn trong ngày
        if not can_send_friend_request():
            log_message(f"⚠️ Đã đạt giới hạn {MAX_FRIEND_REQUESTS_PER_DAY} lời mời kết bạn trong ngày. Bỏ qua hoạt động kết bạn.", logging.WARNING)
            return
            
        log_message("Bắt đầu quy trình thêm bạn bè.", logging.INFO)

        log_message("Tìm kiếm các nhóm tuyển dụng...", logging.INFO)
        browser.get("https://www.facebook.com/search/groups?q=tuyển%20dụng")
        await asyncio.sleep(random.uniform(3, 5))
        
        # Kiểm tra flag sau khi tải trang
        if stop_browsing:
            log_message("Dừng add_friend sau khi tải trang tìm kiếm do nhận được tin mới từ WebSocket", logging.INFO)
            return
            
        groups_box = browser.find_elements(By.XPATH, '//a[contains(@href, "/groups/") and @aria-hidden="true"]')
        group_links = [g.get_attribute("href") for g in groups_box if g.is_displayed() and g.get_attribute("href")]

        link_group = random.choice(group_links)

        members_url = link_group.rstrip("/") + "/members"
        browser.get(members_url)
        await asyncio.sleep(random.uniform(5, 8))
        
        # Kiểm tra flag sau khi vào trang members
        if stop_browsing:
            log_message("Dừng add_friend sau khi vào trang thành viên do nhận được tin mới từ WebSocket", logging.INFO)
            return

        for i in range(5):
            # Kiểm tra flag trước mỗi lần cuộn
            if stop_browsing:
                log_message("Dừng add_friend trong quá trình cuộn do nhận được tin mới từ WebSocket", logging.INFO)
                return
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(random.uniform(2, 4))

        # Kiểm tra flag trước khi tìm nút add friend
        if stop_browsing:
            log_message("Dừng add_friend trước khi tìm nút kết bạn do nhận được tin mới từ WebSocket", logging.INFO)
            return

        add_friend_buttons = browser.find_elements(
            By.XPATH,
            "//div[@role='button' and (starts-with(@aria-label, 'Kết bạn với ') or starts-with(@aria-label, 'Add Friend'))]"
        )

        profile_info_to_add = []
        for idx, btn in enumerate(add_friend_buttons):
            try:
                aria_label = btn.get_attribute('aria-label')
                user_name = ''
                if aria_label:
                    if aria_label.startswith('Kết bạn với '):
                        user_name = aria_label[len('Kết bạn với '):].strip()
                    elif aria_label.startswith('Add Friend'):
                        user_name = aria_label[len('Add Friend'):].strip()
                
                profile_link_element = None
                member_card_xpath = "./ancestor::div[contains(@class, 'x1ja2u2z')][1]"
                member_card = None
                member_card = btn.find_element(By.XPATH, member_card_xpath)
                if member_card:
                    # Tìm link profile trong member_card
                    xpath_profile_link = f".//a[@role='link' and (contains(., '{user_name}') or @aria-label='{user_name}') and (contains(@href, '/user/') or contains(@href, 'profile.php?id='))]"
                    try:
                        profile_link_element = member_card.find_element(By.XPATH, xpath_profile_link)
                    except Exception:
                        # Fallback nếu không tìm thấy bằng tên chính xác
                        xpath_profile_link = ".//a[@role='link' and (contains(@href, '/user/') or contains(@href, 'profile.php?id='))]"
                        try:
                            profile_link_element = member_card.find_element(By.XPATH, xpath_profile_link)
                        except Exception:
                            pass # Không tìm thấy link profile nào trong member_card này
                if profile_link_element:
                    link_user = profile_link_element.get_attribute('href')
                    if link_user and not link_user.startswith("http"):
                        link_user = "https://www.facebook.com" + link_user
                    
                    if link_user:
                        profile_info_to_add.append((link_user, user_name, btn))
                    else:
                        log_message(f"Liên kết profile rỗng sau khi tìm thấy phần tử cho '{user_name}'.", logging.WARNING)
                else:
                    log_message(f"Không tìm thấy phần tử liên kết profile nào cho '{user_name}'.", logging.WARNING)
            except Exception as e:
                log_message(f"Lỗi khi xử lý nút Kết bạn (chung): {e}", logging.ERROR)
                traceback.print_exc()
                continue

        if not profile_info_to_add:
            return

        # Kiểm tra flag trước khi thực hiện kết bạn
        if stop_browsing:
            log_message("Dừng add_friend trước khi gửi lời mời kết bạn do nhận được tin mới từ WebSocket", logging.INFO)
            return

        link_user, user_name, add_btn = random.choice(profile_info_to_add)
        
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        await asyncio.sleep(random.uniform(1, 2))
        
        # Kiểm tra flag trước khi click
        if stop_browsing:
            log_message("Dừng add_friend trước khi click nút kết bạn do nhận được tin mới từ WebSocket", logging.INFO)
            return
        
        try:
            add_btn.click()
            log_message(f"Đã gửi lời mời kết bạn thành công tới {user_name}!", logging.INFO)
            # Tăng counter sau khi kết bạn thành công
            increment_friend_request_counter()
        except Exception as click_err:
            log_message(f"Không thể click nút 'Kết bạn': {click_err}. Thử click bằng JavaScript.", logging.WARNING)
            browser.execute_script("arguments[0].click();", add_btn)
            log_message(f"Đã gửi lời mời kết bạn thành công tới {user_name} (qua JS click)!", logging.INFO)
            # Tăng counter sau khi kết bạn thành công
            increment_friend_request_counter()

        await asyncio.sleep(random.uniform(2, 4))
        
        # Kiểm tra flag trước khi gửi tin nhắn
        if stop_browsing:
            log_message("Dừng add_friend trước khi gửi tin nhắn do nhận được tin mới từ WebSocket", logging.INFO)
            return
        
        # Sử dụng nội dung từ WebSocket nếu có, nếu không thì sử dụng tin nhắn mặc định
        message_content = "Chào bạn, mình là nhân sự bên timviec365, bạn cho mình hỏi là bạn đang đi tìm việc hay là bên tuyển dụng đó ạ? Nếu bạn đang cần tìm ứng viên hoặc đang cần tìm việc làm thì bạn lên trang web timviec365.vn tham khảo nhé."
        
        if pending_posts:
            post_data = pending_posts.pop(0)
            websocket_content = post_data.get("content", "")
            if websocket_content:
                message_content = websocket_content
                log_message("Sử dụng nội dung từ WebSocket để gửi tin nhắn kết bạn", logging.INFO)
            else:
                log_message("Sử dụng tin nhắn mặc định do nội dung WebSocket rỗng", logging.INFO)
        else:
            log_message("Sử dụng tin nhắn mặc định do không có nội dung từ WebSocket", logging.INFO)
        
        await send_message(browser, link_user, message_content)

        # Thoát khỏi trang cá nhân, quay về trang chủ Facebook
        browser.get("https://www.facebook.com")
        await asyncio.sleep(random.uniform(2, 4))
        log_message("Đã thoát khỏi trang cá nhân, quay về trang chủ Facebook", logging.INFO)

        
        # Log thông tin trạng thái kết bạn sau khi hoàn thành
        status = get_friend_request_status()
        log_message(f"📈 Trạng thái kết bạn: {status['count']}/{status['max']} (còn lại: {status['remaining']})", logging.INFO)
        
        # Gửi thông tin trạng thái kết bạn qua WebSocket
        await send_friend_request_status_to_websocket()

    except Exception as err:
        log_message(f"Lỗi tổng quát trong hàm add_friend: {err}", logging.ERROR)
        traceback.print_exc()

# hàm lướt dạo facebook
async def surf_facebook(id, title, browser):
    '''hàm này để lướt fb dạo
    trước tiên lướt fb, sau đó chọn 1 bài viết ngẫu nhiên để đọc cmt hoặc like hoặc share,
    tìm một nhóm bất kỳ và join nhóm, kết bạn với 1 thành viên trong nhóm sau đó nhắn tin với người đó,
    một ngày chỉ kết bạn với 3 người và nhắn tin nhắn chờ với 3 người đó từ 8h sáng đến 9h sáng, 12h trưa đến 1h chiều
    8h tối đến 9h tối...'''

    # check current url
    current_url = browser.current_url
    if "facebook.com" not in current_url:
        browser.get("https://www.facebook.com")
        await asyncio.sleep(random.uniform(5, 8))  # Chờ trang tải xong
    try:
        await asyncio.sleep(random.uniform(3, 5))
        scroll_count = random.randint(14, 15)  # Số lần cuộn
        actions = ActionChains(browser)
        while scroll_count > 0:
            # Kiểm tra flag để dừng lướt khi có tin mới từ WebSocket
            global stop_browsing
            if stop_browsing:
                log_message("Dừng lướt Facebook do nhận được tin mới từ WebSocket", logging.INFO)
                break
                
            # Cuộn từ từ (Mô phỏng cuộn chậm dần đều)
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 1000)

            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))            
            
            # Kiểm tra lại flag sau khi cuộn
            if stop_browsing:
                log_message("Dừng lướt Facebook ngay sau khi cuộn do nhận được tin mới từ WebSocket", logging.INFO)
                break
                
            # Thoi gian dung lai de doc tin
            await asyncio.sleep(random.uniform(4, 6))
            
            # Kiểm tra lại flag sau khi nghỉ
            if stop_browsing:
                log_message("Dừng lướt Facebook sau khi đọc tin do nhận được tin mới từ WebSocket", logging.INFO)
                break

            if scroll_count % 13 == 0:
                # await comment_post(browser, actions)
                await asyncio.sleep(random.uniform(3, 5))
                # Kiểm tra flag sau khi comment
                if stop_browsing:
                    break
            elif scroll_count % 7 == 0:
                await react_post(browser)
                await asyncio.sleep(random.uniform(3, 5))
                # Kiểm tra flag sau khi react
                if stop_browsing:
                    break

            scroll_count = scroll_count - 1

        await asyncio.sleep(random.uniform(2, 5))
        log_message("Đã hoàn thành lướt Facebook")

    except Exception as err:
        log_message(f"err {err}", logging.ERROR)

async def is_logged_in(browser):
    """Kiểm tra xem đã đăng nhập vào Facebook chưa"""
    try:
        # Tìm phần tử có ID "email" hoặc "pass" (chỉ xuất hiện khi chưa đăng nhập)
        await asyncio.sleep(3)  # Chờ trang tải
        login_elements = browser.find_elements(By.ID, "email") + browser.find_elements(By.ID, "pass")
        if login_elements:
            log_message("Chưa đăng nhập vào Facebook!")
            return False
        log_message("Đã đăng nhập vào Facebook!")
        return True
    except Exception:
        return False  # Nếu có lỗi, giả định là chưa đăng nhập

async def read_notification(browser):
    """Đọc thông báo mới trên Facebook"""

def parse_relative_time(date_text, extracted_at):
    """Chuyển các chuỗi dạng '5 giờ', '2 phút', '1 ngày' thành datetime trừ từ extracted_at"""
    now = datetime.fromisoformat(extracted_at)

    patterns = [
        (r'(\d+)\s*giây', 'seconds'),
        (r'(\d+)\s*phút', 'minutes'),
        (r'(\d+)\s*giờ', 'hours'),
        (r'(\d+)\s*ngày', 'days'),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, date_text.lower())
        if match:
            value = int(match.group(1))
            delta = timedelta(**{unit: value})
            comment_time = now - delta
            return comment_time.strftime("%Y-%m-%d")

    # nếu không khớp gì thì trả về ngày hiện tại
    return now.strftime("%Y-%m-%d")

class FacebookCommentScraper:
    def __init__(self, driver=None):
        """Khởi tạo scraper với trình duyệt đã có sẵn"""
        self.driver = driver
        
    def select_all_comments_mode(self):
        """Chọn chế độ 'Tất cả bình luận' thay vì 'Phù hợp nhất'"""
        try:
            sort_selectors = [
                # Tiếng Việt
                "//span[contains(text(), 'Phù hợp nhất')]",
                "//div[contains(text(), 'Phù hợp nhất')]",
                # Tiếng Anh 
                "//span[contains(text(), 'Most relevant')]",
                "//div[contains(text(), 'Most relevant')]"
            ]
            
            # Tìm và click vào nút dropdown
            dropdown_clicked = False
            for selector in sort_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            text = element.text.strip().lower()
                            if "phù hợp nhất" in text or "most relevant" in text:
                                if element.is_displayed() and element.is_enabled():
                                    log_message(f"Đã tìm thấy nút: {element.text}", logging.INFO)
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(1)
                                    self.driver.execute_script("arguments[0].click();", element)
                                    time.sleep(2)
                                    dropdown_clicked = True
                                    break
                        except Exception:
                            continue
                    if dropdown_clicked:
                        break
                except Exception:
                    continue
            
            if not dropdown_clicked:
                log_message("Không tìm thấy nút dropdown sắp xếp bình luận", logging.INFO)
                return True
            
            # Tìm và click "Tất cả bình luận"
            time.sleep(2)
            all_comments_selectors = [
                "//span[contains(text(), 'Tất cả bình luận')]",
                "//div[contains(text(), 'Tất cả bình luận')]",
                "//span[contains(text(), 'All comments')]",
                "//div[contains(text(), 'All comments')]"
            ]
            
            for selector in all_comments_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                self.driver.execute_script("arguments[0].click();", element)
                                log_message("Đã chọn 'Tất cả bình luận'", logging.INFO)
                                time.sleep(3)
                                return True
                        except Exception:
                            continue
                except Exception:
                    continue
            
            log_message("Không tìm thấy tùy chọn 'Tất cả bình luận'", logging.WARNING)
            return False
            
        except Exception as e:
            log_message(f"Lỗi khi chọn chế độ 'Tất cả bình luận': {e}", logging.ERROR)
            return False

    def load_all_comments(self, max_scrolls=50):
        """Cuộn trang và tải thêm bình luận"""
        scrolls = 0
        no_new_content_count = 0
        max_no_new_content = 3 

        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
        except:
            log_message("Không tìm thấy thẻ body", logging.ERROR)
            return

        while scrolls < max_scrolls and no_new_content_count < max_no_new_content:
            log_message(f"Lượt cuộn {scrolls + 1}/{max_scrolls}", logging.INFO)
            
            current_comments_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']"))
            buttons_clicked = self.click_all_expand_buttons()

            for _ in range(5): 
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.3) 
            time.sleep(3)

            new_comments_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']"))
            
            if new_comments_count == current_comments_count and buttons_clicked == 0:
                no_new_content_count += 1
                log_message(f"Không có nội dung mới - lần {no_new_content_count}/{max_no_new_content}", logging.INFO)
            else:
                no_new_content_count = 0 
                if new_comments_count > current_comments_count:
                    log_message(f"Đã tải thêm {new_comments_count - current_comments_count} comment/reply", logging.INFO)
            
            scrolls += 1
            
        # Cuộn lại từ đầu đến cuối một lần nữa để đảm bảo load hết (như trong comment_crawler_TCN)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        for i in range(5):
            self.click_all_expand_buttons()
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(2)

    def click_all_expand_buttons(self):
        """Click tất cả các nút mở rộng"""
        buttons_clicked = 0
        
        view_more_patterns = [
            "//span[contains(text(), 'Xem các bình luận trước')]", 
            "//span[contains(text(), 'bình luận khác')]",
            "//span[contains(text(), 'View more comments')]",
            "//span[contains(text(), 'See previous comments')]",
        ]
        
        reply_patterns = [
            "//span[contains(text(), 'Xem phản hồi')]",
            "//span[contains(text(), 'phản hồi')]",
            "//span[contains(text(), 'View replies')]",
            "//span[contains(text(), 'replies')]",
        ]
        
        all_patterns = view_more_patterns + reply_patterns
        
        for pattern in all_patterns:
            try:
                buttons = self.driver.find_elements(By.XPATH, pattern)
                for button in buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip().lower()
                            valid_keywords = ['xem thêm', 'bình luận', 'phản hồi', 'view more', 'comment', 'replies', 'view replies']
                            if any(keyword in button_text for keyword in valid_keywords):
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                    time.sleep(0.5)
                                    self.driver.execute_script("arguments[0].click();", button)
                                    buttons_clicked += 1
                                    time.sleep(1)
                                except Exception:
                                    continue
                    except Exception:
                        continue
            except Exception:
                continue
        
        return buttons_clicked

    def extract_comments(self, post_url):
        """Trích xuất các bình luận từ một bài đăng"""
        try:
            log_message(f"Đang cào comment từ: {post_url}", logging.INFO)
            self.driver.get(post_url)
            time.sleep(8)
            
            return self._extract_comments_from_page()
            
        except Exception as e:
            log_message(f"Lỗi khi trích xuất các bình luận: {e}", logging.ERROR)
            return []

    def extract_comments_from_current_page(self):
        """Trích xuất các bình luận từ trang hiện tại (không chuyển URL)"""
        try:
            current_url = self.driver.current_url
            log_message(f"Đang cào comment từ trang hiện tại: {current_url}", logging.INFO)
            
            return self._extract_comments_from_page()
            
        except Exception as e:
            log_message(f"Lỗi khi trích xuất các bình luận từ trang hiện tại: {e}", logging.ERROR)
            return []

    def _extract_comments_from_page(self):
        """Hàm chung để trích xuất comment từ trang hiện tại"""
        try:
            # Chọn chế độ "Tất cả bình luận"
            self.select_all_comments_mode()
            
            # Tải tất cả các bình luận và phản hồi
            self.load_all_comments()
            
            # Cuộn lại từ đầu đến cuối một lần nữa để đảm bảo load hết
            log_message("Cuộn lại để đảm bảo load đầy đủ comment...", logging.INFO)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            body = self.driver.find_element(By.TAG_NAME, 'body')
            for i in range(5):
                self.click_all_expand_buttons()
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
            
            comments_data = []
            
            # Tìm tất cả comment elements
            comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
            
            # Filter để chỉ lấy những element thực sự là comment
            valid_comments = []
            for element in comment_elements:
                try:
                    text = element.text.strip()
                    if (len(text) > 0 and 
                        not text.startswith("Hình ảnh") and 
                        not text.startswith("Video") and
                        ("bình luận" in text.lower() or "phản hồi" in text.lower() or len(text.split('\n')) >= 1)):
                        valid_comments.append(element)
                except:
                    continue
            
            log_message(f"📊 Tổng cộng tìm thấy {len(valid_comments)} comment hợp lệ, bắt đầu xử lý và lưu database...", logging.INFO)
            
            # Trích xuất dữ liệu từ mỗi comment
            for i, comment in enumerate(valid_comments):
                try:
                    comment_data = self.extract_comment_data(comment, i, self.driver.current_url)
                    if comment_data:
                        comments_data.append(comment_data)
                        
                        if (i + 1) % 10 == 0:
                            log_message(f"Đã xử lý {i + 1} comment", logging.INFO)
                except Exception as e:
                    log_message(f"Lỗi khi trích xuất comment {i}: {e}", logging.WARNING)
                    continue

            return comments_data
            
        except Exception as e:
            log_message(f"Lỗi trong _extract_comments_from_page: {e}", logging.ERROR)
            return []

    def extract_comment_data(self, comment_element, index, post_url=None):
        """Trích xuất dữ liệu của từng bình luận với improved text extraction"""
        try:
            comment_text = self.extract_comment_text(comment_element)
            commenter_name, commenter_link = self.extract_commenter_info(comment_element)
            comment_date = self.extract_comment_time(comment_element)
            comment_id, reply_comment_id, link_comment = self.extract_comment_ids(comment_element)
            now_iso = datetime.now().isoformat()
            normalized_date = parse_relative_time(comment_date or "", now_iso)
            
            # Debug log để kiểm tra data
            log_message(f"Debug comment {index}: ID={comment_id}, Reply_ID={reply_comment_id}, Text='{comment_text[:50]}...'", logging.INFO)
            
            if comment_text and len(comment_text.strip()) > 0:
                return {
                    'text': comment_text,
                    'commentor': commenter_name or "Unknown",
                    'date_comment': normalized_date or "Unknown",
                    'link_commenter': commenter_link or "None",
                    'comment_id': comment_id or "None",
                    'reply_comment_id': reply_comment_id or "None", 
                    'link_comment': link_comment or "None",
                    'post_url': post_url or "",
                    'extracted_at': now_iso
                }
            else:
                log_message(f" Comment {index} bị bỏ qua vì không có text. ID={comment_id}, Reply_ID={reply_comment_id}", logging.WARNING)
        except Exception as e:
            log_message(f"Lỗi khi trích xuất dữ liệu comment {index}: {e}", logging.ERROR)
        return None

    def is_reply_comment(self, comment_element):
        """Kiểm tra xem element có phải là reply không"""
        try:
            # Kiểm tra class hoặc structure để xác định reply
            # Reply thường có indentation hoặc class đặc biệt
            parent_div = comment_element.find_element(By.XPATH, "./ancestor::div[1]")
            parent_class = parent_div.get_attribute("class") or ""
            
            # Kiểm tra các dấu hiệu của reply
            reply_indicators = [
                "reply", "nested", "indent", "child",
                "sub-comment", "response"
            ]
            
            for indicator in reply_indicators:
                if indicator in parent_class.lower():
                    return True
            
            # Kiểm tra vị trí và cấu trúc
            # Reply thường có margin-left hoặc padding-left lớn hơn
            style = comment_element.get_attribute("style") or ""
            if "margin-left" in style or "padding-left" in style:
                return True
                
            return False
            
        except Exception:
            return False
    
    def find_parent_comment_id(self, reply_element):
        """Tìm ID của comment cha cho reply"""
        try:
            # Tìm comment cha bằng cách đi ngược lên DOM tree
            parent_containers = reply_element.find_elements(
                By.XPATH, 
                "./ancestor::div[contains(@class, 'comment') or @role='article']"
            )
            
            for container in reversed(parent_containers):
                try:
                    # Tìm link có comment_id trong container này
                    links = container.find_elements(By.CSS_SELECTOR, "a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if "comment_id=" in href:
                            comment_match = re.search(r'comment_id=(\d+)', href)
                            if comment_match:
                                return comment_match.group(1)
                except Exception:
                    continue
                    
            return None
            
        except Exception:
            return None

    def extract_comment_text(self, comment_element):
        """
        Extract comment text chính xác.
        - Loại bỏ tên người được trả lời trong reply.
        - Giữ lại các hashtag và các link khác trong nội dung comment.
        """
        try:
            js_script = """
            var element = arguments[0];
            var clone = element.cloneNode(true);
            var links = clone.querySelectorAll('a');
            links.forEach(function(link) {
                var href = link.getAttribute('href') || '';
                if (href.includes('/user/') || href.includes('profile.php')) {
                    link.parentNode.removeChild(link);
                }
            });
            return (clone.textContent || clone.innerText).trim();
            """

            comment_texts = []
            
            text_containers = comment_element.find_elements(By.CSS_SELECTOR, "div[dir='auto']")
            if text_containers:
                for container in text_containers:
                    try:
                        cleaned_text = self.driver.execute_script(js_script, container)
                        if cleaned_text and not self.is_metadata_text(cleaned_text):
                            comment_texts.append(cleaned_text)
                    except Exception:
                        continue
            
            #  Nếu không tìm thấy text từ chiến lược 1
            if not comment_texts:
                try:
                    # Tìm các link không phải là link trang cá nhân
                    all_links = comment_element.find_elements(By.TAG_NAME, 'a')
                    for link in all_links:
                        href = link.get_attribute('href') or ''
                        # Nếu link không phải là link profile, lấy text của nó
                        if not ('/user/' in href or 'profile.php' in href):
                            text = link.text.strip()
                            if text and not self.is_metadata_text(text):
                                comment_texts.append(text)
                except Exception:
                    pass

            if comment_texts:
                return '\n'.join(list(dict.fromkeys(comment_texts)))
            
            return ""
            
        except Exception as e:
            print(f"Lỗi khi trích xuất comment text: {e}")
            return ""
            

    def extract_comment_ids(self, comment_element):
        """Trích xuất comment_id, reply_comment_id và link_comment"""
        comment_id = "None"
        reply_comment_id = "None" 
        link_comment = ""
        
        try:
            link_elements = comment_element.find_elements(By.CSS_SELECTOR, "a")
            
            for link in link_elements:
                try:
                    href = link.get_attribute("href") or ""
                    if "comment_id=" in href:
                        # Extract comment_id
                        comment_match = re.search(r'comment_id=(\d+)', href)
                        if comment_match:
                            comment_id = comment_match.group(1)
                            link_comment = href
                            
                            # Extract reply_comment_id nếu có
                            reply_match = re.search(r'reply_comment_id=(\d+)', href)
                            if reply_match:
                                reply_comment_id = reply_match.group(1)
                                log_message(f"Tìm thấy reply_comment_id: {reply_comment_id} cho comment_id: {comment_id}", logging.INFO)
                            
                            break
                except:
                    continue
                    
        except Exception as e:
            log_message(f"Lỗi khi trích xuất comment IDs: {e}", logging.WARNING)
        
        return comment_id, reply_comment_id, link_comment

    def extract_commenter_info(self, comment_element):
        """Extract commenter name and link"""
        commenter_name = ""
        commenter_link = ""

        try:
            link_elements = comment_element.find_elements(By.CSS_SELECTOR, "a[role='link']")
            
            for link in link_elements:
                try:
                    href = link.get_attribute("href") or ""
                    if "facebook.com" in href and ("profile.php" in href or "/user/" in href or href.count('/') >= 3):
                        name = link.text.strip()
                        if name and len(name) > 0 and not any(char.isdigit() for char in name):
                            commenter_name = name
                            commenter_link = href
                            break
                except:
                    continue
                            
        except Exception as e:
            log_message(f"Lỗi khi trích xuất thông tin commenter: {e}", logging.WARNING)
        
        return commenter_name, commenter_link

    def extract_comment_time(self, comment_element):
        """Extract comment timestamp"""
        comment_date = ""
        
        try:
            link_elements = comment_element.find_elements(By.CSS_SELECTOR, "a")
            for link in link_elements:
                try:
                    text = link.text.strip()
                    if self.is_time_text(text):
                        comment_date = text
                        break
                except:
                    continue
        except:
            pass
        
        return comment_date

    def is_metadata_text(self, text):
        """Kiểm tra xem text có phải là metadata (tên, thời gian, action) không"""
        text_lower = text.lower()
        metadata_keywords = [
            'giờ', 'phút', 'ngày', 'tháng', 'năm',
            'theo dõi', 'thích', 'trả lời', 'chia sẻ',
            'like', 'reply', 'share', 'follow',
            'ago', 'hour', 'minute', 'day', 'month', 'year',
            'just now', 'bây giờ', 'vừa xong'
        ]
        
        # Nếu text quá ngắn (có thể là tên) hoặc chứa metadata keywords
        if len(text) <5 and any(keyword in text_lower for keyword in metadata_keywords):
            return True
            
        return False

    def is_time_text(self, text):
        """Kiểm tra xem text có phải là thời gian không"""
        if not text:
            return False
            
        text_lower = text.lower()
        time_keywords = [
            'giờ', 'phút', 'ngày', 'tháng', 'năm',
            'ago', 'hour', 'minute', 'day', 'month', 'year',
            'h', 'm', 'd', ':', 'just now', 'bây giờ','giây'
        ]
        
        return any(keyword in text_lower for keyword in time_keywords)
    
    def extract_post_id_from_url(self, url):
        """Extract post ID from Facebook URL"""
        try:
            # Các pattern để extract post_id từ URL Facebook
            patterns = [
                r'/posts/(\d+)',
                r'/permalink\.php.*story_fbid=(\d+)',
                r'story_fbid=(\d+)',
                r'/(\d+)/posts/(\d+)',
                r'fbid=(\d+)',
                r'post_id=(\d+)',
                r'/(\d+)/?$'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    # Lấy group cuối cùng (thường là post_id)
                    post_id = match.group(-1)
                    if post_id and len(post_id) > 5:  # Post ID thường dài hơn 5 ký tự
                        log_message(f"Extract được post_id: {post_id} từ URL: {url}", logging.INFO)
                        return post_id
            
            log_message(f"Không extract được post_id từ URL: {url}", logging.WARNING)
            return None
            
        except Exception as e:
            log_message(f" Lỗi khi extract post_id từ URL: {e}", logging.ERROR)
            return None

    def save_to_csv(self, comments_data, filename=None):
        """Lưu dữ liệu bình luận vào file CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_comments_{timestamp}.csv"
        
        if not comments_data:
            log_message("Không có dữ liệu để lưu", logging.WARNING)
            return None
            
        try:
            df = pd.DataFrame(comments_data)
            # Bỏ cột extracted_at nếu có (giống comment_crawler_TCN.py)
            if 'extracted_at' in df.columns:
                df = df.drop(columns=['extracted_at'])
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            log_message(f"Đã lưu {len(comments_data)} bình luận vào file {filename}", logging.INFO)
            return filename
        except Exception as e:
            log_message(f"Lỗi khi lưu file CSV: {e}", logging.ERROR)
            return None

    def scrape_post_comments(self, post_url, cookies_file=None, output_file=None):
        """Phương thức chính để crawl bình luận từ một bài đăng bằng cookie"""
        try:
            if cookies_file and not self.load_cookies(cookies_file):
                log_message("Đăng nhập bằng cookie thất bại. Vui lòng kiểm tra lại file cookie.", logging.ERROR)
                return None
            
            # Trích xuất bình luận
            comments = self.extract_comments(post_url)
            
            if comments:
                # Lưu vào file CSV
                filename = self.save_to_csv(comments, output_file)
                return filename
            else:
                log_message("Không trích xuất được bình luận nào.", logging.WARNING)
                return None
                
        except Exception as e:
            log_message(f"Quá trình crawl thất bại: {e}", logging.ERROR)
            return None

    def close(self):
        """Đóng trình duyệt"""
        if self.driver:
            self.driver.quit()


# Hàm cào comment tự động theo yêu cầu từ CRM
async def crawl_comments_by_crm_request(browser):
    """Xử lý yêu cầu cào comment tự động từ CRM - cào các bài mới nhất như tự động"""
    try:
        global pending_posts
        
        if not pending_posts:
            log_message(" Không có yêu cầu cào comment từ CRM", logging.WARNING)
            await send_crawl_status_to_websocket('error', 'Không có yêu cầu cào comment từ CRM')
            return
            
        request_data = pending_posts.pop(0)
        facebook_id = request_data.get("facebookId", "")
        author_id = request_data.get("authorId", "")
        
        log_message(f"Bắt đầu cào comment tự động theo yêu cầu CRM", logging.INFO)
        log_message(f"FacebookId: {facebook_id}, AuthorId: {author_id}", logging.INFO)
        
        # **GỬI THÔNG BÁO BẮT ĐẦU CÀO COMMENT TỪ CRM**
        start_message = f'Bắt đầu cào comment {MAX_POSTS_TO_CRAWL} bài mới nhất theo yêu cầu CRM (FacebookId: {facebook_id})'
        await send_crawl_status_to_websocket('started', start_message)
        
        # Sử dụng hàm cào comment tự động từ các bài mới nhất (giống như tự động)
        await auto_crawl_comments_from_structure(browser)
        
        # **GỬI THÔNG BÁO HOÀN THÀNH CÀO COMMENT TỪ CRM**
        finish_message = f'Hoàn thành cào comment {MAX_POSTS_TO_CRAWL} bài mới nhất theo yêu cầu CRM (FacebookId: {facebook_id})'
        await send_crawl_status_to_websocket('finished', finish_message)
        log_message("Hoàn thành cào comment tự động theo yêu cầu CRM", logging.INFO)
        
    except Exception as e:
        # **GỬI THÔNG BÁO LỖI CÀO COMMENT TỪ CRM**
        error_message = f"Lỗi khi cào comment theo yêu cầu CRM: {e}"
        await send_crawl_status_to_websocket('error', error_message)
        log_message(f" {error_message}", logging.ERROR)
        traceback.print_exc()

# Hàm cào comment và tự động thêm vào structure
async def crawl_comments_and_update_structure(browser, post_url=None, target_post_id=None):
    """Cào comment từ URL hiện tại hoặc URL cụ thể và tự động thêm vào structure"""
    try:
        # Chỉ chuyển trang nếu post_url khác với trang hiện tại
        if post_url:
            current_url = browser.current_url
            if post_url != current_url:
                log_message(f"Đang chuyển đến URL: {post_url}", logging.INFO)
                browser.get(post_url)
                await asyncio.sleep(3)
            else:
                log_message(f"Đã ở đúng trang: {post_url}", logging.INFO)
        else:
            post_url = browser.current_url
            log_message(f"Đang cào comment từ URL hiện tại: {post_url}", logging.INFO)
        
        # Sử dụng post_id được cung cấp hoặc mặc định
        post_id = target_post_id or "default_post"
        log_message(f"🆔 Sử dụng Post ID: {post_id}", logging.INFO)
        
        # Thêm post vào structure nếu chưa có
        add_post_to_structure(post_url, post_id)
        
        # Khởi tạo scraper với browser hiện tại
        scraper = FacebookCommentScraper(driver=browser)
        
        # Cào comment - KHÔNG truyền post_url để tránh mở link lần 2
        comments = scraper.extract_comments_from_current_page()
        
        if comments:
            log_message(f" Cào được {len(comments)} comment", logging.INFO)
            
            # Phân loại comment và reply
            root_comments = []  # Comments gốc (không có reply_comment_id)
            reply_comments = []  # Replies (có reply_comment_id)
            
            for comment_data in comments:
                reply_comment_id = comment_data.get('reply_comment_id', 'None')
                if reply_comment_id and reply_comment_id != 'None':
                    reply_comments.append(comment_data)
                else:
                    root_comments.append(comment_data)
            
            log_message(f" Phân loại: {len(root_comments)} comment gốc, {len(reply_comments)} reply", logging.INFO)
            
            # Sử dụng hàm update_post_structure_with_new_comments đã cải tiến
            new_comments_added, new_replies_added = await update_post_structure_with_new_comments(post_id, comments)
            
            # Thông báo kết quả
            if new_comments_added > 0 or new_replies_added > 0:
                log_message(f"Đã thêm {new_comments_added} comment mới và {new_replies_added} reply mới vào structure", logging.INFO)
            else:
                log_message("ℹ️ Không có comment/reply mới để thêm", logging.INFO)
                
        else:
            log_message(" Không cào được comment nào", logging.WARNING)
        
        # **THÊM: Đóng popup/modal sau khi cào xong**
        try:
            log_message("🔒 Đóng popup/modal sau khi cào comment...", logging.INFO)
            
            # Thử các cách đóng popup khác nhau
            close_methods = [
                # Nhấn ESC
                lambda: browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE),
                # Tìm nút X đóng
                lambda: browser.find_element(By.CSS_SELECTOR, "[aria-label='Đóng'], [aria-label='Close']").click(),
                # Tìm nút đóng khác
                lambda: browser.find_element(By.CSS_SELECTOR, "div[role='button'][aria-label*='Đóng'], div[role='button'][aria-label*='Close']").click(),
                # Click outside modal
                lambda: browser.execute_script("document.querySelector('[role=dialog]') && document.querySelector('[role=dialog]').parentElement.click()"),
            ]
            
            for i, method in enumerate(close_methods):
                try:
                    method()
                    await asyncio.sleep(1)
                    log_message(f"Đã đóng popup bằng phương pháp {i+1}", logging.INFO)
                    break
                except:
                    continue
                    
        except Exception as close_error:
            log_message(f"Không thể đóng popup: {close_error}", logging.WARNING)
            
    except Exception as e:
        log_message(f" Lỗi trong hàm crawl_comments_and_update_structure: {e}", logging.ERROR)
        traceback.print_exc()

# Hàm cập nhật comment/reply mới vào post structure
async def update_post_structure_with_new_comments(post_id, scraped_comments):
    """Cập nhật những comment/reply mới vào cấu trúc post hiện có"""
    try:
        data = load_post_structure()
        
        if post_id not in data["posts"]:
            log_message(f" Post ID {post_id} không tồn tại trong structure", logging.WARNING)
            return 0, 0
        
        existing_comment_ids = set(data["posts"][post_id]["comments"].keys())
        new_comments_count = 0
        new_replies_count = 0
        
        log_message(f"Đang xử lý {len(scraped_comments)} comment/reply được cào", logging.INFO)
        
        # Tách comment và reply dựa trên reply_comment_id
        comments = []
        replies = []
        
        for c in scraped_comments:
            reply_comment_id = c.get('reply_comment_id', 'None')
            comment_id = c.get('comment_id', 'None')
            
            if reply_comment_id and reply_comment_id != 'None':
                # Có reply_comment_id => đây là reply
                # comment_id là ID của parent comment, reply_comment_id là ID của reply
                replies.append(c)
                log_message(f"📝 Phân loại là REPLY: reply_id={reply_comment_id} (parent: {comment_id})", logging.INFO)
            else:
                # Không có reply_comment_id => đây là comment gốc
                comments.append(c)
                log_message(f" Phân loại là COMMENT: {comment_id}", logging.INFO)
        
        log_message(f" Phân loại: {len(comments)} comment gốc, {len(replies)} reply", logging.INFO)
        
        # **BƯỚC 1: Xử lý comment gốc trước để đảm bảo parent tồn tại**
        new_comments_to_send = []  # Danh sách comment mới để gửi qua WebSocket
        
        for comment in comments:
            comment_id = comment.get('comment_id', 'None')
            comment_text = comment.get('text', '')  # Sửa từ 'comment_text' thành 'text'
            
            if comment_id == 'None' or not comment_text:
                log_message(f"Bỏ qua comment thiếu ID hoặc content: {comment_id}", logging.WARNING)
                continue
                
            # Kiểm tra comment mới hoặc cập nhật placeholder
            if comment_id not in existing_comment_ids:
                # Thêm comment mới
                data["posts"][post_id]["comments"][comment_id] = {
                    "comment_fb_id": comment_id,
                    "content": comment_text,
                    "commenter_name": comment.get('commentor', ''), 
                    "commenter_link": comment.get('link_commenter', ''), 
                    "comment_date": comment.get('date_comment', ''),  
                    "link_comment": comment.get('link_comment', ''),
                    "replies": {},
                    "created_at": datetime.now().isoformat(),
                    "scraped_at": datetime.now().isoformat()
                }
                new_comments_count += 1
                log_message(f"➕ Thêm comment mới: {comment_id} - {comment_text[:50]}...", logging.INFO)
                
                # Thêm vào danh sách để gửi qua WebSocket
                new_comments_to_send.append({
                    'type': 'comment_byB',
                    'postId': post_id,
                    'content': comment_text,
                    'authorId': get_websocket_role(),  # Sử dụng roleWebSocket làm authorId
                    'authorName': comment.get('commentor', 'Anonymous'),
                    'URL': comment.get('link_comment', ''),
                    'commentFbId': comment_id,
                    'linkUserComment': comment.get('link_commenter', ''),  # Link profile người comment
                    'timestamp': datetime.now().isoformat()
                })
                
                # LƯU COMMENT CÀO ĐƯỢC VÀO DATABASE
                try:
                    # Lấy database_post_id từ structure
                    database_post_id = get_database_post_id(post_id)
                    if not database_post_id:
                        log_message(f"Không tìm thấy database_post_id cho post_id: {post_id}", logging.WARNING)
                        database_post_id = post_id  # Fallback
                    
                    payloadScrapedComment = {
                        "post_id": database_post_id,  # Sử dụng _id từ MongoDB
                        "facebookId": get_websocket_role(),
                        "userId": get_id_tosend_websocket(),
                        "userNameFacebook": comment.get('commentor', 'Anonymous'),
                        "content": comment_text,
                        "postId": post_id,  # Facebook post ID
                        "userLinkFb": comment.get('link_commenter', ''),  # Link profile người comment
                        "facebookCommentUrl": comment.get('link_comment', ''),
                        "facebookCommentId": comment_id,
                        "createdAt": int(time.time()),
                        "updatedAt": int(time.time()),
                        "scraped": True,  # Đánh dấu là comment cào được
                        "scrapedAt": datetime.now().isoformat(),
                        "originalDate": comment.get('date_comment', '')
                    }
                    
                    # Gọi API để lưu comment cào được (async)
                    response = await create_comment(payloadScrapedComment)
                    if response:
                        log_message(f"✅ Đã lưu scraped comment {comment_id} vào database thành công!", logging.INFO)
                    else:
                        log_message(f"⚠️ Lỗi khi lưu scraped comment {comment_id} vào database", logging.WARNING)
                        
                except Exception as db_error:
                    log_message(f"❌ Lỗi database khi lưu scraped comment {comment_id}: {db_error}", logging.ERROR)
                
            else:
                # Kiểm tra nếu comment hiện tại là placeholder thì cập nhật
                existing_comment = data["posts"][post_id]["comments"][comment_id]
                if existing_comment.get("content", "") == "[Comment gốc chưa được cào]":
                    existing_comment.update({
                        "content": comment_text,
                        "commenter_name": comment.get('commentor', ''),
                        "commenter_link": comment.get('link_commenter', ''),
                        "comment_date": comment.get('date_comment', ''),
                        "link_comment": comment.get('link_comment', ''),
                        "scraped_at": datetime.now().isoformat()
                    })
                    log_message(f"Cập nhật placeholder comment: {comment_id} - {comment_text[:50]}...", logging.INFO)
                else:
                    log_message(f"ℹ️ Comment đã tồn tại: {comment_id}", logging.INFO)
        
        # **BƯỚC 2: Xử lý reply sau khi đã có comment gốc**
        new_replies_to_send = []  # Danh sách reply mới để gửi qua WebSocket
        
        for reply in replies:
            parent_comment_id = reply.get('comment_id', 'None')  # ID của comment cha
            reply_id = reply.get('reply_comment_id', 'None')  # ID của reply
            reply_text = reply.get('text', '')  # Sửa từ 'comment_text' thành 'text'
            
            if reply_id == 'None' or not reply_text:
                log_message(f"Bỏ qua reply thiếu ID hoặc content: {reply_id}", logging.WARNING)
                continue
            
            if parent_comment_id == 'None':
                log_message(f"Reply {reply_id} không có parent comment ID", logging.WARNING)
                continue
            
            # Đảm bảo parent comment tồn tại (nếu không có thì tạo placeholder)
            if parent_comment_id not in data["posts"][post_id]["comments"]:
                log_message(f"Parent comment {parent_comment_id} chưa tồn tại, tạo placeholder", logging.WARNING)
                data["posts"][post_id]["comments"][parent_comment_id] = {
                    "comment_fb_id": parent_comment_id,
                    "content": "[Comment gốc chưa được cào]",
                    "commenter_name": "",
                    "commenter_link": "",
                    "comment_date": "",
                    "link_comment": "",
                    "replies": {},
                    "created_at": datetime.now().isoformat(),
                    "scraped_at": datetime.now().isoformat()
                }
            
            # Kiểm tra reply đã tồn tại chưa
            existing_reply_ids = set(data["posts"][post_id]["comments"][parent_comment_id]["replies"].keys())
            
            if reply_id not in existing_reply_ids:
                # Thêm reply mới
                data["posts"][post_id]["comments"][parent_comment_id]["replies"][reply_id] = {
                    "reply_fb_id": reply_id,
                    "content": reply_text,
                    "commenter_name": reply.get('commentor', ''),  # Sửa key
                    "commenter_link": reply.get('link_commenter', ''),  # Sửa key
                    "comment_date": reply.get('date_comment', ''),  # Sửa key
                    "link_comment": reply.get('link_comment', ''),
                    "created_at": datetime.now().isoformat(),
                    "scraped_at": datetime.now().isoformat()
                }
                new_replies_count += 1
                log_message(f"➕ Thêm reply mới: {reply_id} cho comment {parent_comment_id} - {reply_text[:50]}...", logging.INFO)
                
                # Thêm vào danh sách để gửi qua WebSocket
                new_replies_to_send.append({
                    'type': 'reply_comment_byB',
                    'postId': post_id,
                    'commentId': parent_comment_id,
                    'replyId': reply_id,
                    'content': reply_text,
                    'authorId': get_websocket_role(),  # Sử dụng roleWebSocket làm authorId
                    'authorName': reply.get('commentor', 'Anonymous'),
                    'URL': reply.get('link_comment', ''),
                    'linkUserReply': reply.get('link_commenter', ''),  # Link profile người reply
                    'timestamp': datetime.now().isoformat()
                })
                
                # LƯU REPLY CÀO ĐƯỢC VÀO DATABASE
                try:
                    # Lấy tên người chủ comment, fallback về tên Facebook của account hiện tại nếu không có
                    reply_to_author = data["posts"][post_id]["comments"][parent_comment_id].get("commenter_name", "")
                    if not reply_to_author:
                        reply_to_author = get_facebook_name()
                    
                    payloadScrapedReply = {
                        "userId": get_id_tosend_websocket(),
                        "userNameFacebook": reply.get('commentor', 'Anonymous'),
                        "content": reply_text,
                        "userLinkFb": reply.get('link_commenter', ''),  # Link profile người reply
                        "facebookReplyUrl": reply.get('link_comment', ''),
                        "id_facebookReply": reply_id,
                        "replyToAuthor": reply_to_author,
                        "createdAt": int(time.time()),
                        "updatedAt": int(time.time()),
                        "scraped": True,  # Đánh dấu là reply cào được
                        "scrapedAt": datetime.now().isoformat(),
                        "originalDate": reply.get('date_comment', '')
                    }
                    
                    # Gọi API để lưu reply cào được (async) - sử dụng parent_comment_id làm facebook_comment_id
                    response = await create_reply_comment(parent_comment_id, payloadScrapedReply)
                    if response:
                        log_message(f"✅ Đã lưu scraped reply {reply_id} vào database thành công!", logging.INFO)
                    else:
                        log_message(f"⚠️ Lỗi khi lưu scraped reply {reply_id} vào database", logging.WARNING)
                        
                except Exception as db_error:
                    log_message(f"❌ Lỗi database khi lưu scraped reply {reply_id}: {db_error}", logging.ERROR)
                
            else:
                log_message(f"ℹ️ Reply đã tồn tại: {reply_id} trong comment {parent_comment_id}", logging.INFO)
                continue
            
            # Đảm bảo parent comment tồn tại (nếu không có thì tạo placeholder)
            if parent_comment_id not in data["posts"][post_id]["comments"]:
                log_message(f"Parent comment {parent_comment_id} chưa tồn tại, tạo placeholder", logging.WARNING)
                data["posts"][post_id]["comments"][parent_comment_id] = {
                    "comment_fb_id": parent_comment_id,
                    "content": "[Comment gốc chưa được cào]",
                    "commenter_name": "",
                    "commenter_link": "",
                    "comment_date": "",
                    "link_comment": "",
                    "replies": {},
                    "created_at": datetime.now().isoformat(),
                    "scraped_at": datetime.now().isoformat()
                }
            
            # Kiểm tra reply đã tồn tại chưa
            existing_reply_ids = set(data["posts"][post_id]["comments"][parent_comment_id]["replies"].keys())
            
            if reply_id not in existing_reply_ids:
                # Thêm reply mới
                data["posts"][post_id]["comments"][parent_comment_id]["replies"][reply_id] = {
                    "reply_fb_id": reply_id,
                    "content": reply_text,
                    "commenter_name": reply.get('commentor', ''),  # Sửa key
                    "commenter_link": reply.get('link_commenter', ''),  # Sửa key
                    "comment_date": reply.get('date_comment', ''),  # Sửa key
                    "link_comment": reply.get('link_comment', ''),
                    "created_at": datetime.now().isoformat(),
                    "scraped_at": datetime.now().isoformat()
                }
                new_replies_count += 1
                log_message(f"➕ Thêm reply mới: {reply_id} cho comment {parent_comment_id} - {reply_text[:50]}...", logging.INFO)
            else: 
                log_message(f"ℹ️ Reply đã tồn tại: {reply_id} trong comment {parent_comment_id}", logging.INFO)
        
        # Lưu structure đã cập nhật
        if new_comments_count > 0 or new_replies_count > 0:
            save_post_structure(data)
            log_message(f"Đã cập nhật {new_comments_count} comment mới và {new_replies_count} reply mới cho post {post_id}", logging.INFO)
            
            # **GỬI DỮ LIỆU QUA WEBSOCKET**
            async def send_new_data_to_websocket():
                """Gửi comment và reply mới qua WebSocket"""
                try:
                    async with websockets.connect(WEBSOCKET_URL) as websocket:
                        # Gửi các comment mới
                        for comment_data in new_comments_to_send:
                            # Thêm thông tin user_id từ tài khoản hiện tại
                            user_ids = get_id_tosend_websocket()
                            comment_data["to"] = user_ids
                            
                            await websocket.send(json.dumps(comment_data))
                            log_message(f"Đã gửi comment mới qua WebSocket: {comment_data['commentFbId']}", logging.INFO)
                            await asyncio.sleep(0.1)  # Delay nhỏ giữa các message
                        
                        # Gửi các reply mới
                        for reply_data in new_replies_to_send:
                            # Thêm thông tin user_id từ tài khoản hiện tại
                            user_ids = get_id_tosend_websocket()
                            reply_data["to"] = user_ids
                            
                            await websocket.send(json.dumps(reply_data))
                            log_message(f"Đã gửi reply mới qua WebSocket: {reply_data['replyId']} cho comment {reply_data['commentId']}", logging.INFO)
                            await asyncio.sleep(0.1)  # Delay nhỏ giữa các message
                            
                except Exception as ws_error:
                    log_message(f" Lỗi khi gửi dữ liệu qua WebSocket: {ws_error}", logging.ERROR)
            
            # Chạy gửi WebSocket (nếu có data mới)
            if new_comments_to_send or new_replies_to_send:
                try:
                    import asyncio
                    # Kiểm tra xem có event loop đang chạy không
                    try:
                        loop = asyncio.get_running_loop()
                        # Nếu có loop đang chạy, tạo task
                        asyncio.create_task(send_new_data_to_websocket())
                    except RuntimeError:
                        # Nếu không có loop, chạy trực tiếp
                        asyncio.run(send_new_data_to_websocket())
                except Exception as async_error:
                    log_message(f" Lỗi khi chạy async WebSocket: {async_error}", logging.ERROR)
        else:
            log_message(f"ℹ️ Không có comment/reply mới cho post {post_id}", logging.INFO)
        
        return new_comments_count, new_replies_count
        
    except Exception as e:
        log_message(f" Lỗi khi cập nhật post structure: {e}", logging.ERROR)
        traceback.print_exc()
        return 0, 0

# Hàm cào comment tự động từ các bài mới nhất trong structure
async def auto_crawl_comments_from_structure(browser):
    """Tự động cào comment từ các bài post mới nhất trong post_structure.json và tự động cập nhật structure"""
    try:
        data = load_post_structure()
        posts = data.get("posts", {})
        
        if not posts:
            log_message("📝 Không có post nào trong structure để cào comment", logging.INFO)
            await send_crawl_status_to_websocket('finished', 'Không có post nào để cào comment', 0, 0)
            return
        
        # **SẮP XẾP CÁC POST THEO THỜI GIAN TẠO (MỚI NHẤT TRƯỚC)**
        posts_with_time = []
        for post_id, post_data in posts.items():
            created_at = post_data.get("created_at", "1970-01-01T00:00:00")
            posts_with_time.append((post_id, post_data, created_at))
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        posts_with_time.sort(key=lambda x: x[2], reverse=True)
        
        # **CHỈ LẤY SỐ BÀI TỐI ĐA THEO CẤU HÌNH**
        latest_posts = posts_with_time[:MAX_POSTS_TO_CRAWL]
        
        total_posts = len(latest_posts)
        total_all_posts = len(posts)
        
        log_message(f"Bắt đầu cào comment tự động từ {total_posts} bài post mới nhất (tổng cộng {total_all_posts} bài)", logging.INFO)
        
        total_processed = 0
        
        for post_id, post_data, created_at in latest_posts:
            try:
                post_url = post_data.get("url", "")
                if not post_url:
                    log_message(f"Post {post_id} không có URL, bỏ qua", logging.WARNING)
                    continue
                
                total_processed += 1
                
                # **GỬI THÔNG BÁO TIẾN TRÌNH CÀO COMMENT**
                progress_message = f"Đang cào comment từ post mới nhất {total_processed}/{total_posts}: {post_id}"
                await send_crawl_status_to_websocket('progress', progress_message, total_posts, total_processed)
                
                log_message(f"Đang cào comment từ post mới nhất: {post_id} ({total_processed}/{total_posts})", logging.INFO)
                log_message(f"URL: {post_url}", logging.INFO)
                log_message(f"📅 Tạo lúc: {created_at}", logging.INFO)
                
                # Sử dụng hàm cào comment và tự động cập nhật structure với post_id cụ thể
                await crawl_comments_and_update_structure(browser, post_url, post_id)
                
                # Nghỉ giữa các post để tránh spam
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception as post_error:
                log_message(f" Lỗi khi cào post {post_id}: {post_error}", logging.ERROR)
                # **GỬI THÔNG BÁO LỖI CHO POST CỤ THỂ**
                error_message = f"Lỗi khi cào post {post_id}: {post_error}"
                await send_crawl_status_to_websocket('error', error_message, total_posts, total_processed)
                continue
        
        # **GỬI THÔNG BÁO HOÀN THÀNH TẤT CẢ POST**
        final_message = f"Hoàn thành cào comment tự động! Đã xử lý {total_processed}/{total_posts} bài post mới nhất"
        await send_crawl_status_to_websocket('finished', final_message, total_posts, total_processed)
        
        log_message(f"🎉 Hoàn thành cào comment tự động từ {MAX_POSTS_TO_CRAWL} bài mới nhất!", logging.INFO)
        log_message(f"📈 Đã xử lý {total_processed}/{total_posts} bài post mới nhất (tổng cộng {total_all_posts} bài)", logging.INFO)
            
    except Exception as e:
        # **GỬI THÔNG BÁO LỖI TỔNG QUÁT**
        error_message = f"Lỗi nghiêm trọng trong auto_crawl_comments_from_structure: {e}"
        await send_crawl_status_to_websocket('error', error_message)
        log_message(f" Lỗi trong hàm auto_crawl_comments_from_structure: {e}", logging.ERROR)
        traceback.print_exc()

# Hàm cào comment thủ công từ URL hiện tại
async def manual_crawl_current_page(browser):
    """Cào comment từ trang hiện tại và thêm vào structure"""
    try:
        current_url = browser.current_url
        log_message(f"Cào comment thủ công từ trang hiện tại: {current_url}", logging.INFO)
        
        # **GỬI THÔNG BÁO BẮT ĐẦU CÀO COMMENT THỦ CÔNG**
        await send_crawl_status_to_websocket('started', f'Bắt đầu cào comment thủ công: {current_url}', 1, 0)
        
        await crawl_comments_and_update_structure(browser)
        
        # **GỬI THÔNG BÁO HOÀN THÀNH CÀO COMMENT THỦ CÔNG**
        await send_crawl_status_to_websocket('finished', f'Hoàn thành cào comment thủ công: {current_url}', 1, 1)
        
    except Exception as e:
        # **GỬI THÔNG BÁO LỖI CÀO COMMENT THỦ CÔNG**
        error_message = f"Lỗi trong manual_crawl_current_page: {e}"
        await send_crawl_status_to_websocket('error', error_message)
        log_message(f" {error_message}", logging.ERROR)


# Hàm gửi thông báo trạng thái cào comment qua WebSocket
async def send_crawl_status_to_websocket(status, message="", post_count=0, current_post=0):
    """Gửi thông báo trạng thái cào comment qua WebSocket"""
    user_ids = get_id_tosend_websocket()
    try:
        # Tạo message thông báo trạng thái
        status_message = {
            'type': 'crawl_comment',
            'status': status,  # 'started', 'progress', 'completed', 'error'
            'message': message,
            'postCount': post_count,
            'currentPost': current_post,
            'timestamp': datetime.now().isoformat(),
            'authorId': get_websocket_role(),
            'facebookId': get_websocket_role(),  # facebookId = roleWebSocket
            'to': user_ids,
        }
        
        # Gửi qua WebSocket
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                await websocket.send(json.dumps(status_message))
                log_message(f"📡 Đã gửi thông báo trạng thái cào comment: {status} - {message} (facebookId: {get_websocket_role()})", logging.INFO)
        except Exception as ws_error:
            log_message(f" Lỗi khi gửi thông báo trạng thái qua WebSocket: {ws_error}", logging.WARNING)
            
    except Exception as e:
        log_message(f" Lỗi trong send_crawl_status_to_websocket: {e}", logging.ERROR)


# Hàm kiểm tra và thực hiện cào comment tự động theo chu kỳ
async def check_and_run_auto_crawl(browser):
    """Kiểm tra và chạy cào comment tự động """
    global last_auto_crawl_time
    
    try:
        current_time = time.time()
        
        # Lần đầu chạy hoặc đã qua
        if last_auto_crawl_time is None or (current_time - last_auto_crawl_time) >= AUTO_CRAWL_INTERVAL:
            log_message(f"⏰ Đến lúc cào comment tự động từ {MAX_POSTS_TO_CRAWL} bài mới nhất", logging.INFO)
            
            # **GỬI THÔNG BÁO BẮT ĐẦU CÀO COMMENT**
            await send_crawl_status_to_websocket('started', f'Bắt đầu cào comment tự động từ {MAX_POSTS_TO_CRAWL} bài mới nhất')
            
            # Dừng tất cả hoạt động khác
            global stop_browsing
            original_stop_browsing = stop_browsing
            stop_browsing = True
            
            try:
                await auto_crawl_comments_from_structure(browser)
                last_auto_crawl_time = current_time
                
                # **GỬI THÔNG BÁO HOÀN THÀNH CÀO COMMENT**
                completion_message = f"Hoàn thành chu kỳ cào comment tự động từ {MAX_POSTS_TO_CRAWL} bài mới nhất lúc {datetime.now().strftime('%H:%M:%S')}"
                await send_crawl_status_to_websocket('finished', completion_message)
                log_message(f"{completion_message}", logging.INFO)
                
            except Exception as crawl_error:
                # **GỬI THÔNG BÁO LỖI CÀO COMMENT**
                error_message = f"Lỗi khi cào comment: {crawl_error}"
                await send_crawl_status_to_websocket('error', error_message)
                log_message(f" {error_message}", logging.ERROR)
                raise crawl_error
            finally:
                # Khôi phục trạng thái ban đầu
                stop_browsing = original_stop_browsing
        
    except Exception as e:
        log_message(f" Lỗi trong hàm check_and_run_auto_crawl: {e}", logging.ERROR)


def kill_existing_process():
    """Tắt tất cả các tiến trình toolfacebook.exe đang chạy"""
    current_pid = os.getpid()
    for process in psutil.process_iter(['pid', 'name']):
        if process.name() == 'toolfacebook.exe' and process.pid != current_pid:
            print(f"Đang tắt tiến trình cũ: {process.pid}")
            try:
                process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

# **Hàm main() để chạy chương trình**
async def main(client_user_id_chat):
    kill_existing_process()
    browser = None
    try:
        # Kiểm tra tham số đầu vào
        if not client_user_id_chat:
            return
        initialize()
        #Lấy data từ file user_accounts.json
        account_data = None
        global current_account_data  # Khai báo sử dụng biến global
        try:
            with open("user_accounts.json", "r", encoding="utf-8") as file:
                accounts = json.load(file)
                
                for acc in accounts:
                    acc_user_id = str(acc.get("user_id_chat")) # Đảm bảo cùng kiểu dữ liệu
                    log_message(f"Kiểm tra tài khoản: user_id_chat={acc_user_id}, note={acc.get('note', 'N/A')}", logging.DEBUG)
                    if acc_user_id == client_user_id_chat:
                        account_data = acc
                        current_account_data = acc  # Gán vào biến global
                        break
        except FileNotFoundError:
            log_message("File user_accounts.json không tồn tại, chương trình sẽ dừng lại.", logging.ERROR)
            return
        except json.JSONDecodeError:
            log_message("File user_accounts.json bị hỏng, chương trình sẽ dừng lại.", logging.ERROR)
            return
        if not account_data:
            log_message(f"Tài khoản với user_id_chat '{client_user_id_chat}' không được tìm thấy trong user_accounts.json. Chương trình sẽ không chạy.", logging.ERROR)
            return
        facebook_username = account_data.get("facebook_username")
        facebook_password = account_data.get("facebook_password")
        facebook_2fa_code = account_data.get("facebook_2fa_code", "")
        if not facebook_username or not facebook_password:
            log_message("Thông tin đăng nhập Facebook không đầy đủ trong user_accounts.json. Chương trình sẽ dừng lại.", logging.ERROR)
            return
        
        log_message(f"Đang chạy tool cho tài khoản: {facebook_username} (User ID Chat: {client_user_id_chat})", logging.INFO)

        chrome_options = Options()
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")

        # chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        screen_width = 1920  # Adjust this value based on your screen resolution
        screen_height = 1050  # Adjust this value based on your screen resolution
        chrome_options.add_argument(f"--window-position={screen_width // 2},0")
        chrome_options.add_argument(f"--window-size={screen_width // 2},{screen_height}")
        service = webdriver.ChromeService(version_main=122)
        browser = webdriver.Chrome(service=service, options=chrome_options)
        browser.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)
        # dang nhap tren fb
        actions = ActionChains(browser)
        browser.get("https://facebook.com")
        await asyncio.sleep(3)
        
        if os.path.exists(COOKIE_FILE):
            # load_cookies trả về True/False, nên có thể dùng trực tiếp
            if await load_cookies(browser):
                browser.refresh()
                await asyncio.sleep(4)
            else:
                log_message("Tải cookies thất bại hoặc không có cookies hợp lệ. Tiến hành đăng nhập mới.", logging.INFO)

        # Kiểm tra nếu vẫn cần đăng nhập
        if not await is_logged_in(browser):
            log_message("Cookies không hợp lệ hoặc hết hạn, cần đăng nhập lại.")
            # Hàm login gốc không trả về giá trị, giả định nó thành công nếu không có ngoại lệ
            await login(facebook_username, facebook_password, facebook_2fa_code, browser)
            # Sau khi login, kiểm tra lại trạng thái đăng nhập
            if not await is_logged_in(browser):
                log_message("Đăng nhập thất bại sau khi thử. Chương trình sẽ dừng lại.", logging.ERROR)
                return
            
        await asyncio.sleep(3)

        page_source = browser.page_source
        if '"userID":' in page_source:
            start = page_source.find('"userID":') + len('"userID":')
            end = page_source.find(',', start)
            id_fb = page_source[start:end].strip('"')  # Loại bỏ dấu nháy nếu có
            log_message(f'Facebook ID thực tế: {id_fb}', logging.INFO)

        # Khởi động WebSocket task
        websocket_task = asyncio.create_task(connect_websocket())
        log_message("🚀 Đã khởi động WebSocket task để nhận nội dung", logging.INFO)

        while True:
            try:
                # KIỂM TRA VÀ RESTART WEBSOCKET TASK NẾU CẦN
                if websocket_task.done():
                    # WebSocket task đã dừng, cần restart
                    log_message("WebSocket task đã dừng, đang restart...", logging.WARNING)
                    try:
                        # Lấy exception nếu có để log
                        websocket_exception = websocket_task.exception()
                        if websocket_exception:
                            log_message(f" WebSocket task lỗi: {websocket_exception}", logging.ERROR)
                    except:
                        pass
                    
                    # Restart WebSocket task
                    websocket_task = asyncio.create_task(connect_websocket())
                    log_message("Đã restart WebSocket task thành công", logging.INFO)
                    await asyncio.sleep(2)  # Đợi một chút để task khởi động
                
                # Kiểm tra và chạy cào comment tự động
                # await check_and_run_auto_crawl(browser)
                
                # Kiểm tra nếu có tin mới từ WebSocket thì ưu tiên xử lý ngay
                global stop_browsing
                if stop_browsing and pending_posts:
                    # Kiểm tra type của dữ liệu để quyết định hành động
                    if pending_posts[0].get("type") == "new_post":
                        log_message("Có bài viết mới từ WebSocket, dừng TẤT CẢ hoạt động và đăng bài ngay lập tức", logging.INFO)
                        await post_news_feed(browser,pending_posts, get_facebook_name(), get_websocket_role(), get_id_tosend_websocket())
                    elif pending_posts[0].get("type") == "comment":
                        log_message("Có yêu cầu bình luận từ WebSocket, dừng TẤT CẢ hoạt động và bình luận ngay lập tức", logging.INFO)
                        await comment_on_post_url(browser,pending_posts,get_facebook_name(), get_websocket_role(), get_id_tosend_websocket())
                    elif pending_posts[0].get("type") == "reply_comment":
                        log_message("Có yêu cầu trả lời bình luận từ WebSocket, dừng TẤT CẢ hoạt động và trả lời ngay lập tức", logging.INFO)
                        await reply_to_comment(browser, pending_posts, get_facebook_name(), get_websocket_role(), get_id_tosend_websocket())
                    elif pending_posts[0].get("type") == "reply_reply_comment":
                        log_message("Có yêu cầu trả lời reply comment từ WebSocket, dừng TẤT CẢ hoạt động và trả lời reply ngay lập tức", logging.INFO)
                        await reply_to_reply_comment(browser, pending_posts, get_facebook_name(), get_websocket_role(), get_id_tosend_websocket())
                    elif pending_posts[0].get("type") == "crawl_comment_by_CRM":
                        log_message("Có yêu cầu cào comment từ CRM, dừng TẤT CẢ hoạt động và cào comment tự động từ bài mới nhất", logging.INFO)
                        await crawl_comments_by_crm_request(browser)
                    else:
                        log_message(f"Loại dữ liệu không xác định từ WebSocket: {pending_posts[0].get('type')}", logging.WARNING)
                        pending_posts.pop(0)  # Xóa dữ liệu không xác định
                    
                    stop_browsing = False  # Reset flag sau khi xử lý
                    await asyncio.sleep(random.uniform(2, 4))
                    continue
                
                # Thực hiện các hoạt động theo thứ tự nhưng luôn kiểm tra flag
                # 1. Lướt Facebook
                if not stop_browsing:
                    await surf_facebook("", random.choice(COMMENTS), browser)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Cào data thông minh sau khi lướt Facebook
                    if not stop_browsing:
                        await check_and_run_auto_crawl(browser)
                
                # Kiểm tra lại flag trước khi tiếp tục
                if stop_browsing and pending_posts:
                    log_message("Dừng hoạt động sau surf_facebook để xử lý WebSocket", logging.INFO)
                    continue
                
                # 2. Xem video
                if not stop_browsing:
                    await watch_videos(browser, actions = ActionChains(browser))
                    
                    # Cào data thông minh sau khi xem video
                    if not stop_browsing:
                        await check_and_run_auto_crawl(browser)
                
                # Kiểm tra lại flag trước khi tiếp tục
                if stop_browsing and pending_posts:
                    log_message("Dừng hoạt động sau watch_videos để xử lý WebSocket", logging.INFO)
                    continue
                
                # 3. Đăng bài (chỉ nếu có nội dung từ WebSocket)
                if not stop_browsing:
                    await post_news_feed(browser)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Cào data thông minh sau khi đăng bài
                    if not stop_browsing:
                        await check_and_run_auto_crawl(browser)
                
                # Kiểm tra lại flag trước khi tiếp tục
                if stop_browsing and pending_posts:
                    log_message("Dừng hoạt động sau post_news_feed để xử lý WebSocket", logging.INFO)
                    continue
                
                # 4. Nhắn tin bạn bè
                if not stop_browsing:
                    await list_friend(browser)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Cào data thông minh sau khi nhắn tin bạn bè  
                    if not stop_browsing:
                        await check_and_run_auto_crawl(browser)
                
                # Kiểm tra lại flag trước khi tiếp tục
                if stop_browsing and pending_posts:
                    log_message("Dừng hoạt động sau list_friend để xử lý WebSocket", logging.INFO)
                    continue
                
                # 5. Kết bạn
                if not stop_browsing:
                    # Kiểm tra trạng thái kết bạn trước khi thực hiện
                    status = get_friend_request_status()
                    if status['remaining'] > 0:
                        await add_friend(browser)
                        await asyncio.sleep(random.uniform(2, 3))
                        
                        # Cào data thông minh sau khi kết bạn
                        if not stop_browsing:
                            await check_and_run_auto_crawl(browser)
                    else:
                        log_message(f"⏸️ Bỏ qua kết bạn - đã đạt giới hạn {MAX_FRIEND_REQUESTS_PER_DAY}/ngày", logging.INFO)
                        await asyncio.sleep(random.uniform(60, 120))  # Nghỉ ngắn thay vì kết bạn
                
            except Exception as err:
                log_message(f'err:{err}', logging.ERROR)
                traceback.print_exc()
                log_message("Có lỗi xảy ra, chương trình sẽ dừng lại.", logging.ERROR)
                break

    except Exception as err:
        traceback.print_exc()
    finally:
        if browser:
            try:
                browser.quit()
                log_message("Đã đóng browser.", logging.INFO)
            except:
                pass
        log_message("Chương trình đã kết thúc.", logging.INFO)


if __name__ == "__main__":
    # Lấy user_id_chat từ command line arguments
    if len(sys.argv) > 1:
        client_user_id_chat = sys.argv[1]
        print(f"Starting tool with user_id_chat: {client_user_id_chat}")
    else:
        print("Usage: python toolfacebook.py <user_id_chat>")
        sys.exit(1)
    
    asyncio.run(main(client_user_id_chat))