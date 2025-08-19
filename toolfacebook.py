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
import shutil
import pandas as pd
from datetime import timedelta
from api import create_post, create_comment, create_reply_comment
from seleniumwire import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from utils import hide_process, initialize, log_message, run_as_trusted, smooth_scroll, type_text_input
import logging
logging.getLogger('seleniumwire').setLevel(logging.WARNING)

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
# WEBSOCKET_URL = "ws://localhost:4000"
WEBSOCKET_URL = "wss://socket.hungha365.com:4000"
# URL_IMAGE = "http://192.168.0.116:4000"
URL_IMAGE = "https://socket.hungha365.com:4000"

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

# Hàm quản lý cấu trúc bài viết
def load_post_structure():
    """Load cấu trúc bài viết từ file JSON"""
    try:
        if os.path.exists(POST_STRUCTURE_FILE):
            with open(POST_STRUCTURE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"posts": {}}
    except Exception as e:
        log_message(f"Lỗi khi load post structure: {e}", logging.ERROR)
        return {"posts": {}}

def load_user_accounts():
    """Load thông tin user accounts từ file JSON"""
    try:
        if os.path.exists("user_accounts.json"):
            with open("user_accounts.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Nếu data là array, convert thành dict với key là user_id_QLC
                if isinstance(data, list):
                    result = {}
                    for account in data:
                        if isinstance(account, dict) and "user_id_QLC" in account:
                            result[account["user_id_QLC"]] = account
                    return result
                return data
        return {}
    except Exception as e:
        log_message(f"Lỗi khi load user accounts: {e}", logging.ERROR)
        return {}

def save_post_structure(data):
    """Lưu cấu trúc bài viết vào file JSON"""
    try:
        with open(POST_STRUCTURE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message("Đã lưu post structure thành công", logging.INFO)
    except Exception as e:
        log_message(f"Lỗi khi lưu post structure: {e}", logging.ERROR)

def add_post_to_structure(post_url, post_id=None, database_post_id=None):
    """Thêm post mới vào cấu trúc"""
    try:
        data = load_post_structure()
        
        # Extract post ID from URL if not provided
        if not post_id:
            post_id_match = re.search(r'posts/(\d+)', post_url)
            if post_id_match:
                post_id = post_id_match.group(1)
            else:
                post_id = post_url  # Use full URL as fallback
        
        if post_id not in data["posts"]:
            data["posts"][post_id] = {
                "url": post_url,
                "post_id": post_id,
                "database_post_id": database_post_id,  # Lưu _id từ database để sử dụng sau
                "comments": {},
                "created_at": datetime.now().isoformat()
            }
            save_post_structure(data)
            log_message(f"Đã thêm post mới vào structure: {post_id}", logging.INFO)
            if database_post_id:
                log_message(f"Lưu database_post_id trong structure: {database_post_id}", logging.INFO)
        
        return post_id
    except Exception as e:
        log_message(f"Lỗi khi thêm post vào structure: {e}", logging.ERROR)
        return None

def add_comment_to_structure(post_id,comment_fb_id=None, comment_content=""):
    """Thêm comment vào cấu trúc post"""
    try:
        data = load_post_structure()
        
        if post_id in data["posts"]:
            if comment_fb_id not in data["posts"][post_id]["comments"]:
                data["posts"][post_id]["comments"][comment_fb_id] = {
                    "comment_fb_id": comment_fb_id,
                    "content": comment_content,
                    "replies": {},
                    "created_at": datetime.now().isoformat()
                }
                save_post_structure(data)
                log_message(f"Đã thêm comment vào structure: {comment_fb_id}", logging.INFO)
        
        return comment_fb_id
    except Exception as e:
        log_message(f"Lỗi khi thêm comment vào structure: {e}", logging.ERROR)
        return None

def add_reply_to_structure(post_id, comment_id, reply_fb_id, reply_content=""):
    """Thêm reply vào cấu trúc comment"""
    try:
        data = load_post_structure()
        
        if post_id in data["posts"] and comment_id in data["posts"][post_id]["comments"]:
            if reply_fb_id not in data["posts"][post_id]["comments"][comment_id]["replies"]:
                data["posts"][post_id]["comments"][comment_id]["replies"][reply_fb_id] = {
                    "reply_fb_id": reply_fb_id,
                    "content": reply_content,
                    "created_at": datetime.now().isoformat()
                }
                save_post_structure(data)
                log_message(f"Đã thêm reply vào structure: {reply_fb_id}", logging.INFO)
        
        return reply_fb_id
    except Exception as e:
        log_message(f"Lỗi khi thêm reply vào structure: {e}", logging.ERROR)
        return None

def check_comment_exists(post_id, comment_id):
    """Kiểm tra comment đã tồn tại trong post chưa (chỉ kiểm tra theo ID)"""
    try:
        data = load_post_structure()
        
        if post_id in data["posts"]:
            if comment_id in data["posts"][post_id]["comments"]:
                log_message(f"Comment đã tồn tại: {comment_id}", logging.WARNING)
                return True
        
        return False
    except Exception as e:
        log_message(f"Lỗi khi kiểm tra comment: {e}", logging.ERROR)
        return False

def check_reply_exists(post_id, comment_id, reply_id):
    """Kiểm tra reply đã tồn tại trong comment chưa (chỉ kiểm tra theo ID)"""
    try:
        data = load_post_structure()
        
        if post_id in data["posts"] and comment_id in data["posts"][post_id]["comments"]:
            if reply_id in data["posts"][post_id]["comments"][comment_id]["replies"]:
                log_message(f"Reply đã tồn tại: {reply_id}", logging.WARNING)
                return True
        
        return False
    except Exception as e:
        log_message(f"Lỗi khi kiểm tra reply: {e}", logging.ERROR)
        return False

def get_post_structure_info(post_id):
    """Lấy thông tin cấu trúc của post"""
    try:
        data = load_post_structure()
        return data["posts"].get(post_id, None)
    except Exception as e:
        log_message(f"Lỗi khi lấy thông tin post structure: {e}", logging.ERROR)
        return None

def get_database_post_id(post_id):
    """Lấy database_post_id từ post structure"""
    try:
        post_info = get_post_structure_info(post_id)
        if post_info and "database_post_id" in post_info:
            return post_info["database_post_id"]
        return None
    except Exception as e:
        log_message(f"Lỗi khi lấy database_post_id: {e}", logging.ERROR)
        return None

def get_commenter_name(post_id, comment_id, reply_id=None):
    """Lấy tên của người bình luận từ post_structure hoặc user_accounts
    
    Args:
        post_id: ID của post
        comment_id: ID của comment
        reply_id: ID của reply (nếu có)
    
    Returns:
        str: Tên người bình luận hoặc None nếu không tìm thấy
    """
    try:
        # Load post structure
        data = load_post_structure()
        post_info = data["posts"].get(post_id, {})
        
        commenter_name = None
        
        # Kiểm tra trong reply trước nếu có reply_id
        if reply_id and "comments" in post_info:
            for comment_key, comment_data in post_info["comments"].items():
                if isinstance(comment_data, dict) and "replies" in comment_data:
                    for reply_key, reply_data in comment_data["replies"].items():
                        if isinstance(reply_data, dict) and reply_key == reply_id:
                            commenter_name = reply_data.get("commenter_name")
                            if commenter_name:
                                log_message(f"Tìm thấy commenter_name trong reply: {commenter_name}", logging.INFO)
                                return commenter_name
        
        # Kiểm tra trong comments
        if "comments" in post_info:
            for comment_key, comment_data in post_info["comments"].items():
                if isinstance(comment_data, dict) and comment_key == comment_id:
                    commenter_name = comment_data.get("commenter_name")
                    if commenter_name:
                        log_message(f"Tìm thấy commenter_name trong comment: {commenter_name}", logging.INFO)
                        return commenter_name
        
        if not commenter_name:
            log_message(f"Không tìm thấy commenter_name cho post_id={post_id}, comment_id={comment_id}, reply_id={reply_id}", logging.WARNING)
        
        return commenter_name
        
    except Exception as e:
        log_message(f"Lỗi khi lấy commenter name: {e}", logging.ERROR)
        return None

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

# Hàm xóa file ảnh
def delete_image(file_path):
    """Xóa file ảnh sau khi đăng bài"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            log_message(f"Đã xóa ảnh: {file_path}", logging.INFO)
        else:
            log_message(f"File không tồn tại để xóa: {file_path}", logging.WARNING)
    except Exception as e:
        log_message(f"Lỗi khi xóa ảnh {file_path}: {e}", logging.ERROR)

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

# Hàm bình luận vào bài viết theo URL cụ thể
async def comment_on_post_url(browser):
    """Bình luận vào bài viết theo URL từ WebSocket"""
    try:
        # Kiểm tra xem có yêu cầu bình luận từ WebSocket không
        if not pending_posts:
            log_message("Không có yêu cầu bình luận từ WebSocket. Bỏ qua việc bình luận.", logging.WARNING)
            return
        
        # Lấy dữ liệu bình luận từ WebSocket
        comment_data = pending_posts.pop(0)
        userId = comment_data.get("authorId", "")
        
        # Kiểm tra type có phải là comment không
        if comment_data.get("type") != "comment":
            log_message(f"Dữ liệu không phải là comment. Type: {comment_data.get('type')}", logging.WARNING)
            return
            
        post_url = comment_data.get("URL", "")
        comment_content = comment_data.get("content", "")
        post_id_from_websocket = comment_data.get("postId", None)
        
        if not post_url:
            log_message("Không có URL bài viết để bình luận. Bỏ qua.", logging.WARNING)
            return
            
        if not comment_content:
            log_message("Không có nội dung bình luận. Bỏ qua.", logging.WARNING)
            return
        
        log_message(f"Đang truy cập URL bài viết để bình luận: {post_url}", logging.INFO)
        log_message(f"Nội dung bình luận: {comment_content[:50]}...", logging.INFO)
        if post_id_from_websocket:
            log_message(f"PostId từ WebSocket: {post_id_from_websocket}", logging.INFO)
        
        # Sử dụng post_id từ WebSocket hoặc extract từ URL
        extracted_post_id = post_id_from_websocket
        if not extracted_post_id:
            # Thử extract post_id từ URL nếu không có từ WebSocket
            post_id_match = re.search(r'posts/(\d+)', post_url)
            if post_id_match:
                extracted_post_id = post_id_match.group(1)
            else:
                extracted_post_id = post_url  # Use full URL as fallback
        
        # Truy cập URL bài viết
        browser.get(post_url)
        await asyncio.sleep(random.uniform(3, 5))
        
        # Đợi trang load hoàn toàn
        log_message("Đợi trang load hoàn toàn...", logging.INFO)
        await asyncio.sleep(3)
        
        # Tìm nút bình luận (tránh click vào ảnh)
        comment_button = None
        try:
            log_message("Bắt đầu tìm nút bình luận...", logging.INFO)
            
            # Cuộn xuống một chút để tìm nút bình luận thật sự
            browser.execute_script("window.scrollBy(0, 300);")
            await asyncio.sleep(1)
            
            # Tìm tất cả nút bình luận
            comment_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Viết bình luận" or @aria-label="Leave a comment" or @aria-label="Write a comment") and @role="button"]')
            log_message(f"Tìm thấy {len(comment_buttons)} nút có aria-label bình luận", logging.INFO)
            
            # Nếu có ít nhất 2 nút, chọn nút thứ 2 luôn
            if len(comment_buttons) >= 2:
                log_message("Có ít nhất 2 nút, chọn nút thứ 2 luôn", logging.INFO)
                comment_button = comment_buttons[1]  # Chọn nút thứ 2 (index 1)
                log_message("Đã chọn nút bình luận thứ 2", logging.INFO)
            else:
                # Nếu chỉ có 1 nút hoặc không có nút nào, giữ logic cũ
                for i, btn in enumerate(comment_buttons):
                    if btn.is_displayed() and btn.is_enabled():
                        log_message(f"Kiểm tra nút {i+1}/{len(comment_buttons)}", logging.INFO)
                        
                        # Cuộn nút vào view để kiểm tra
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        await asyncio.sleep(0.5)
                        
                        # Kiểm tra không phải nút ảnh
                        is_valid = True
                        try:
                            # Kiểm tra nút có chứa ảnh không
                            img_elements = btn.find_elements(By.TAG_NAME, "img")
                            if img_elements:
                                log_message(f"Nút {i+1} có chứa {len(img_elements)} ảnh - bỏ qua", logging.INFO)
                                is_valid = False
                                continue
                                
                            # Kiểm tra class name
                            btn_class = btn.get_attribute("class") or ""
                            if any(img_class in btn_class.lower() for img_class in ["image", "photo", "picture", "media", "attachment"]):
                                log_message(f"Nút {i+1} có class liên quan đến ảnh - bỏ qua", logging.INFO)
                                is_valid = False
                                continue
                                
                            # Kiểm tra text content của nút
                            btn_text = btn.get_attribute("textContent") or ""
                            if "bình luận" in btn_text.lower() or "comment" in btn_text.lower():
                                log_message(f"Nút {i+1} có text bình luận hợp lệ", logging.INFO)
                                comment_button = btn
                                break
                                
                            # Nếu không có text, kiểm tra aria-label chi tiết hơn
                            aria_label = btn.get_attribute("aria-label") or ""
                            if ("viết bình luận" in aria_label.lower() or 
                                "leave a comment" in aria_label.lower() or 
                                "write a comment" in aria_label.lower()):
                                # Kiểm tra xem có phải nút trong vùng bài viết chính không
                                parent_elements = btn.find_elements(By.XPATH, "./ancestor::*[contains(@class, 'post') or contains(@class, 'story') or contains(@data-pagelet, 'FeedUnit')]")
                                if parent_elements:
                                    log_message(f"Nút {i+1} nằm trong container bài viết - lưu làm ứng cử viên", logging.INFO)
                                    comment_button = btn  # Lưu nút này, có thể sẽ bị ghi đè bởi nút sau
                                    # Không break ở đây, tiếp tục tìm để lấy nút cuối cùng
                                
                        except Exception as check_error:
                            log_message(f"Lỗi khi kiểm tra nút {i+1}: {check_error}", logging.WARNING)
                            continue
                
                # Nếu tìm thấy comment_button qua vòng lặp trên, đó sẽ là nút cuối cùng
                if comment_button:
                    log_message("Đã chọn nút bình luận cuối cùng hợp lệ", logging.INFO)
                    
            # Nếu vẫn chưa tìm thấy, thử tìm theo text
            if not comment_button:
                log_message("Không tìm thấy nút bằng aria-label, thử tìm theo text...", logging.INFO)
                comment_buttons = browser.find_elements(By.XPATH, '//div[@role="button" and (contains(text(), "Bình luận") or contains(text(), "Comment"))]')
                
                # Nếu có ít nhất 2 nút, chọn nút thứ 2 luôn
                if len(comment_buttons) >= 2:
                    log_message("Có ít nhất 2 nút text, chọn nút thứ 2 luôn", logging.INFO)
                    comment_button = comment_buttons[1]  # Chọn nút thứ 2 (index 1)
                    log_message("Đã chọn nút bình luận text thứ 2", logging.INFO)
                else:
                    # Nếu chỉ có 1 nút hoặc không có nút nào, giữ logic cũ
                    for i, btn in enumerate(comment_buttons):
                        if btn.is_displayed() and btn.is_enabled():
                            # Cuộn vào view
                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            await asyncio.sleep(0.5)
                            
                            # Kiểm tra không có ảnh
                            img_elements = btn.find_elements(By.TAG_NAME, "img")
                            if not img_elements:
                                log_message(f"Nút text {i+1} không có ảnh - lưu làm ứng cử viên", logging.INFO)
                                comment_button = btn  # Lưu nút này, tiếp tục tìm để lấy nút cuối cùng
                            else:
                                log_message(f"Nút text {i+1} có {len(img_elements)} ảnh - bỏ qua", logging.INFO)
                    
                    if comment_button:
                        log_message("Đã chọn nút bình luận cuối cùng theo text", logging.INFO)
                            
        except Exception as e:
            log_message(f"Lỗi khi tìm nút bình luận: {e}", logging.WARNING)
        
        if not comment_button:
            log_message("Không tìm thấy nút bình luận trên trang này", logging.ERROR)
            return
        
        # Scroll nút bình luận vào view và click
        log_message(" Đã tìm thấy nút bình luận, chuẩn bị click...", logging.INFO)
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_button)
        await asyncio.sleep(2)
        
        # Click nút bình luận
        actions = ActionChains(browser)
        try:
            comment_button.click()
            log_message("Đã click nút bình luận thành công", logging.INFO)
        except:
            try:
                actions.move_to_element(comment_button).click().perform()
                log_message("Đã click nút bình luận bằng ActionChains", logging.INFO)
            except:
                browser.execute_script("arguments[0].click();", comment_button)
                log_message("Đã click nút bình luận bằng JavaScript", logging.INFO)
        
        await asyncio.sleep(random.uniform(2, 4))
        
        # Tìm comment box để nhập nội dung
        comment_box = None
        try:
            wait = WebDriverWait(browser, 10)
            comment_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
            log_message("Đã tìm thấy comment box", logging.INFO)
        except:
            try:
                # Thử cách khác
                comment_box = browser.find_element(By.XPATH, '//div[@contenteditable="true" and @role="textbox"]')
                log_message(" Đã tìm thấy comment box (cách 2)", logging.INFO)
            except:
                log_message("Không tìm thấy comment box", logging.ERROR)
                return
        
        if not comment_box:
            log_message(" Không thể tìm thấy comment box", logging.ERROR)
            return
        
        await asyncio.sleep(1)
        
        # Tìm thẻ p trong comment box và nhập nội dung
        try:
            p_tag = comment_box.find_element(By.TAG_NAME, "p")
            if p_tag and p_tag.is_displayed():
                log_message(" Đang nhập nội dung bình luận...", logging.INFO)
                
                # Click vào p_tag trước khi nhập
                p_tag.click()
                await asyncio.sleep(1)
                
                # Nhập nội dung bình luận
                actions = ActionChains(browser)
                actions.send_keys_to_element(p_tag, comment_content)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Gửi bình luận bằng cách nhấn Enter
                actions.send_keys(Keys.ENTER)
                actions.perform()
                
                log_message("Đã gửi bình luận thành công!", logging.INFO)
                await asyncio.sleep(2)
                
                # LẤY COMMENT_ID SAU KHI BÌNH LUẬN THÀNH CÔNG
                comment_id = None
                try:
                    log_message("Đang tìm thời gian bình luận để lấy comment_id...", logging.INFO)
                    
                    # Đợi bình luận xuất hiện và trang reload
                    await asyncio.sleep(3)
                    
                    # Tìm bình luận vừa đăng (thường là bình luận cuối cùng hoặc mới nhất)
                    # Tìm tất cả timestamp của bình luận
                    comment_timestamps = browser.find_elements(By.XPATH, "//a[contains(@href, 'comment_id=')]")
                    
                    if comment_timestamps:
                        log_message(f"Tìm thấy {len(comment_timestamps)} timestamp bình luận:", logging.INFO)
                        
                        # # In ra tất cả các link timestamp để debug
                        # for i, timestamp in enumerate(comment_timestamps):
                        #     try:
                        #         href = timestamp.get_attribute("href")
                        #         text = timestamp.get_attribute("textContent") or "No text"
                        #         log_message(f"  Link {i+1}: {href} - Text: '{text.strip()}'", logging.INFO)
                        #     except Exception as e:
                        #         log_message(f"  Link {i+1}: Lỗi khi lấy thông tin - {e}", logging.WARNING)
                        
                        # Lấy timestamp bình luận cuối cùng (mới nhất)
                        latest_comment_timestamp = comment_timestamps[-1]
                        log_message(f"Chọn timestamp cuối cùng (link {len(comment_timestamps)})", logging.INFO)
                        
                        # Lấy href của timestamp cuối cùng (không cần click)
                        timestamp_href = None
                        try:
                            timestamp_href = latest_comment_timestamp.get_attribute("href")
                            log_message(f"Lấy href của timestamp cuối cùng: {timestamp_href}", logging.INFO)
                        except Exception as href_error:
                            log_message(f"Lỗi khi lấy href: {href_error}", logging.WARNING)
                        
                        # Trích xuất comment_id trực tiếp từ href
                        if timestamp_href:
                            comment_id_match = re.search(r'comment_id=(\d+)', timestamp_href)
                            if comment_id_match:
                                comment_id = comment_id_match.group(1)
                                current_url = timestamp_href  # Sử dụng href làm URL
                                log_message(f"THÀNH CÔNG - Comment ID từ href: {comment_id}", logging.INFO)
                            else:
                                log_message("Không tìm thấy comment_id trong href", logging.ERROR)
                        else:
                            log_message("Không lấy được href của timestamp", logging.ERROR)
                        
                        # Chỉ tiếp tục nếu đã có comment_id
                        if comment_id:
                            # Lưu comment vào cấu trúc dữ liệu
                            add_comment_to_structure(extracted_post_id, comment_id, comment_content)
                            
                            # Lưu comment vào database thông qua API
                            try:
                                log_message("Đang lưu comment vào database...", logging.INFO)
                                
                                # Lấy database_post_id từ structure thay vì dùng extracted_post_id
                                database_post_id = get_database_post_id(extracted_post_id)
                                if not database_post_id:
                                    log_message(f"Không tìm thấy database_post_id cho post_id: {extracted_post_id}", logging.WARNING)
                                    database_post_id = extracted_post_id  # Fallback
                                
                                # Lấy commenter name từ post structure hoặc user accounts
                                commenter_name = get_commenter_name(extracted_post_id, comment_id)
                                if not commenter_name:
                                    commenter_name = get_facebook_name()  # Fallback về tên Facebook hiện tại
                                
                                # Lấy link commenter từ post structure nếu có
                                commenter_link = ""
                                try:
                                    post_info = get_post_structure_info(extracted_post_id)
                                    if post_info and "comments" in post_info:
                                        for comment_key, comment_data in post_info["comments"].items():
                                            if isinstance(comment_data, dict) and comment_key == comment_id:
                                                commenter_link = comment_data.get("commenter_link", "")
                                                break
                                except Exception as e:
                                    log_message(f"Lỗi khi lấy commenter_link: {e}", logging.WARNING)
                                
                                payloadComment = {
                                    "post_id": database_post_id,  # Sử dụng _id từ MongoDB
                                    "facebookId": get_websocket_role(),
                                    "userId": userId,
                                    "userNameFacebook": commenter_name,  # Sử dụng tên từ post structure hoặc user accounts
                                    "content": comment_content,
                                    "postId": post_id_from_websocket,
                                    "userLinkFb": commenter_link,  # Link profile người comment
                                    "facebookCommentUrl": current_url,
                                    "facebookCommentId": comment_id,
                                    "createdAt": int(time.time()),  
                                    "updatedAt": int(time.time())   
                                }
                                
                                # Gọi API để lưu comment (async)
                                api_response = await create_comment(payloadComment)
                                log_message(f"Đã lưu comment vào database thành công: {api_response}", logging.INFO)
                                
                            except Exception as api_error:
                                log_message(f"Lỗi khi lưu comment vào database: {api_error}", logging.ERROR)
                        else:
                            log_message("Không thể lấy được comment_id từ bất kỳ nguồn nào", logging.ERROR)
                    else:
                        log_message(" Không tìm thấy timestamp bình luận nào", logging.WARNING)
                        
                except Exception as comment_id_error:
                    log_message(f" Lỗi khi lấy comment_id: {comment_id_error}", logging.ERROR)
                
                # Gửi thông báo thành công về bên A qua WebSocket
                try:
                    
                    comment_result = {
                        "type": "comment_result",   
                        "status": "success",
                        "URL": current_url,
                        "content": comment_content,
                        "authorName": get_facebook_name(),
                        "timestamp": datetime.now().isoformat()
                    }   
                    
                    # Thêm comment_id nếu lấy được
                    if comment_id:
                        comment_result["comment_id"] = comment_id
                        log_message(f"Thêm comment_id vào kết quả: {comment_id}", logging.INFO)
                    
                    # Thêm postId nếu có từ WebSocket
                    if post_id_from_websocket:
                        comment_result["postId"] = post_id_from_websocket
                        log_message(f"Đã thêm postId vào kết quả: {post_id_from_websocket}", logging.INFO)
                    
                    # Thêm thông tin user_id từ tài khoản hiện tại
                    user_ids = get_id_tosend_websocket()
                    comment_result["to"] = user_ids
                    
                    # Gửi kết quả qua WebSocket
                    async def send_comment_result():
                        try:
                            async with websockets.connect(WEBSOCKET_URL) as websocket:
                                # Gửi kết quả bình luận
                                await websocket.send(json.dumps(comment_result))
                                log_message("Đã gửi kết quả bình luận (có comment_id) về bên A!", logging.INFO)
                        except Exception as ws_error:
                            log_message(f" Lỗi khi gửi kết quả qua WebSocket: {ws_error}", logging.ERROR)
                    
                    await send_comment_result()
                    
                except Exception as result_error:
                    log_message(f" Lỗi khi chuẩn bị gửi kết quả: {result_error}", logging.ERROR)
            else:
                log_message(" Không tìm thấy thẻ p trong comment box", logging.ERROR)
        except Exception as input_error:
            log_message(f" Lỗi khi nhập nội dung bình luận: {input_error}", logging.ERROR)
        
        # Nhấn ESC để thoát
        try:
            actions.send_keys(Keys.ESCAPE).perform()
        except:
            pass
            
    except Exception as e:
        log_message(f" Lỗi trong hàm comment_on_post_url: {e}", logging.ERROR)
        traceback.print_exc()
        
        # Gửi thông báo lỗi về bên A
        try:
            if 'post_url' in locals() and 'comment_content' in locals():
                error_result = {
                    "type": "comment_result",
                    "status": "error",
                    "URL": current_url,
                    "content": comment_content,
                    "authorName": get_facebook_name(),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                if 'post_id_from_websocket' in locals() and post_id_from_websocket:
                    error_result["postId"] = post_id_from_websocket
                
                # Thêm thông tin user_id từ tài khoản hiện tại
                user_ids = get_id_tosend_websocket()
                error_result["to"] = user_ids
                
                async def send_error_result():
                    try:
                        async with websockets.connect(WEBSOCKET_URL) as websocket:
                            
                            await websocket.send(json.dumps(error_result))
                            log_message("Đã gửi thông báo lỗi về bên A", logging.INFO)
                    except:
                        pass
                
                await send_error_result()
        except:
            pass

# Hàm tìm container chứa comment cụ thể
async def find_comment_container(browser, comment_id):
    """
    Tìm container chứa comment với ID cụ thể
    """
    
    try:
        log_message(f"Đang tìm container chứa commentId: {comment_id}", logging.INFO)
        
        # Tìm theo href chứa comment_id
        comment_links = browser.find_elements(By.XPATH, f"//a[contains(@href, 'comment_id={comment_id}')]")
        
        log_message(f"Tìm thấy {len(comment_links)} link chứa comment_id={comment_id}:", logging.INFO)
        for i, link in enumerate(comment_links):
            try:
                href = link.get_attribute("href")
                text = link.get_attribute("textContent") or "No text"
                log_message(f"  Container Link {i+1}: {href} - Text: '{text.strip()}'", logging.INFO)
            except Exception as e:
                log_message(f"  Container Link {i+1}: Lỗi khi lấy thông tin - {e}", logging.WARNING)
        
        if comment_links:
            # Tìm container cha chứa link này
            for link in comment_links:
                try:
                    # Tìm container cha có class chính xác là x18xomjl xbcz3fp chứa bình luận
                    container = link.find_element(By.XPATH, "./ancestor::div[@class='x18xomjl xbcz3fp'][1]")
                    if container:
                        log_message(f"Tìm thấy container cha có class chính xác x18xomjl xbcz3fp chứa commentId", logging.INFO)
                        return container
                except Exception:
                    continue
        
            log_message(f" Không tìm thấy container chứa commentId: {comment_id}", logging.ERROR)
        return None
        
    except Exception as e:
        log_message(f" Lỗi khi tìm container bình luận: {e}", logging.ERROR)
        return None

# Hàm trả lời bình luận
async def reply_to_comment(browser):
    """
    Hàm trả lời bình luận cụ thể dựa vào URL và aria-label
    """
    try:
        global pending_posts, current_client_id
        
        # Khởi tạo biến để tránh lỗi UnboundLocalError
        reply_url = None
        reply_id = None
        comment_url = ""
        reply_content = ""
        comment_id_from_websocket = ""
        post_id_from_websocket = None
        
        if not pending_posts:
            log_message(" Không có dữ liệu reply_comment trong pending_posts", logging.ERROR)
            return
        
        # Lấy dữ liệu từ WebSocket
        reply_data = pending_posts[0]
        pending_posts.pop(0)
        userId = reply_data.get("authorId", "")
        
        comment_url = reply_data.get("URL", "")
        reply_content = reply_data.get("content", "")
        comment_id_from_websocket = reply_data.get("commentId", "")
        post_id_from_websocket = reply_data.get("postId", None)
        
        log_message(f"Bắt đầu trả lời bình luận có ID: {comment_id_from_websocket}", logging.INFO)
        log_message(f"URL: {comment_url}", logging.INFO)
        log_message(f" Nội dung trả lời: {reply_content}", logging.INFO)
        if post_id_from_websocket:
            log_message(f"PostId từ WebSocket: {post_id_from_websocket}", logging.INFO)
        
        if not comment_url or not reply_content:
            log_message(" Thiếu URL hoặc nội dung trả lời", logging.ERROR)
            return
        
        # Sử dụng post_id từ WebSocket hoặc extract từ URL
        extracted_post_id = post_id_from_websocket
        if not extracted_post_id:
            # Thử extract post_id từ URL nếu không có từ WebSocket
            post_id_match = re.search(r'posts/(\d+)', comment_url)
            if post_id_match:
                extracted_post_id = post_id_match.group(1)
            else:
                extracted_post_id = comment_url  # Use full URL as fallback
        
        # Điều hướng đến URL bình luận
        log_message("Đang điều hướng đến URL bình luận...", logging.INFO)
        browser.get(comment_url)
        await asyncio.sleep(random.uniform(3, 5))
        
        # Tìm container chứa commentId cần reply
        log_message(f"Đang tìm container chứa commentId: {comment_id_from_websocket}", logging.INFO)
        comment_container = None
        
        try:
            # Tìm theo href chứa comment_id, sau đó mở rộng đến container cha có class x18xomjl xbcz3fp
            comment_links = browser.find_elements(By.XPATH, f"//a[contains(@href, 'comment_id={comment_id_from_websocket}')]")
            
            log_message(f"Tìm thấy {len(comment_links)} link chứa comment_id={comment_id_from_websocket}:", logging.INFO)
            for i, link in enumerate(comment_links):
                try:
                    href = link.get_attribute("href")
                    text = link.get_attribute("textContent") or "No text"
                    log_message(f"  Comment Link {i+1}: {href} - Text: '{text.strip()}'", logging.INFO)
                except Exception as e:
                    log_message(f"  Comment Link {i+1}: Lỗi khi lấy thông tin - {e}", logging.WARNING)
            
            if comment_links:
                # Tìm container cha chứa link này
                for link in comment_links:
                    try:
                        # Tìm container cha có class chính xác là x18xomjl xbcz3fp (chứa cả comment và replies)
                        container = link.find_element(By.XPATH, "./ancestor::div[@class='x18xomjl xbcz3fp'][1]")
                        if container:
                            comment_container = container
                            log_message(f"Tìm thấy container cha có class chính xác x18xomjl xbcz3fp chứa commentId", logging.INFO)
                            break
                    except Exception:
                        continue
            
                        
        except Exception as e:
            log_message(f" Lỗi khi tìm container bình luận: {e}", logging.ERROR)
        
        if not comment_container:
            log_message(f" Không tìm thấy container chứa commentId: {comment_id_from_websocket}", logging.ERROR)
            return
        
        # Tìm nút Trả lời trong container đó
        reply_button = None
        try:
            # Tìm nút Trả lời cụ thể trong container này
            reply_selectors = [
                ".//div[@role='button' and normalize-space(text())='Trả lời']",
                ".//div[@role='button' and contains(@aria-label, 'Trả lời')]",
                ".//div[@role='button' and contains(text(), 'Trả lời')]",
                ".//span[normalize-space(text())='Trả lời']/ancestor::div[@role='button'][1]"
            ]
            
            for selector in reply_selectors:
                try:
                    reply_buttons = comment_container.find_elements(By.XPATH, selector)
                    for btn in reply_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            reply_button = btn
                            btn_text = btn.text.strip() if btn.text else ""
                            btn_aria_label = btn.get_attribute('aria-label') or ""
                            log_message(f"Tìm thấy nút Trả lời trong container - Text: '{btn_text}', Aria-label: '{btn_aria_label}'", logging.INFO)
                            break
                    if reply_button:
                        break
                except Exception:
                    continue
                        
        except Exception as e:
            log_message(f" Lỗi khi tìm nút Trả lời trong container: {e}", logging.ERROR)
        
        if not reply_button:
            log_message(" Không tìm thấy nút Trả lời trong container bình luận", logging.ERROR)
            return
        
        # Click vào nút trả lời
        log_message("Đang click nút Trả lời trong container...", logging.INFO)
        try:
            # Scroll vào view trước
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_button)
            await asyncio.sleep(1)
            
            # Thử nhiều cách click
            click_success = False
            for attempt in range(3):
                try:
                    if attempt == 0:
                        reply_button.click()
                    elif attempt == 1:
                        browser.execute_script("arguments[0].click();", reply_button)
                    elif attempt == 2:
                        ActionChains(browser).move_to_element(reply_button).click().perform()
                    
                    click_success = True
                    log_message(f"Click nút Trả lời thành công (cách {attempt + 1})", logging.INFO)
                    break
                except Exception as click_err:
                    log_message(f" Click attempt {attempt + 1} thất bại: {click_err}", logging.WARNING)
                    await asyncio.sleep(0.5)
            
            if not click_success:
                log_message(" Không thể click nút Trả lời sau 3 lần thử", logging.ERROR)
                return
                
        except Exception as e:
            log_message(f" Lỗi khi click nút Trả lời: {e}", logging.ERROR)
            return
        
        await asyncio.sleep(2)
        
        # Tìm reply box (comment box mới xuất hiện)
        log_message("Đang tìm reply box...", logging.INFO)
        reply_box = None
        try:
            wait = WebDriverWait(browser, 10)
            reply_boxes = browser.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"]')
            
            # Lấy reply box đầu tiên (thay vì cuối cùng)
            for box in reply_boxes:
                if box.is_displayed():
                    reply_box = box
                    log_message("Đã tìm thấy reply box đầu tiên", logging.INFO)
                    break
            
            if not reply_box:
                # Thử cách khác
                reply_box = browser.find_element(By.XPATH, '//div[@contenteditable="true" and @role="textbox"]')
                log_message("Đã tìm thấy reply box (cách 2)", logging.INFO)
        except:
            log_message(" Không tìm thấy reply box", logging.ERROR)
            return
        
        if not reply_box:
            log_message(" Không thể tìm thấy reply box", logging.ERROR)
            return
        
        await asyncio.sleep(1)
        
        # Nhập nội dung trả lời
        try:
            p_tag = reply_box.find_element(By.TAG_NAME, "p")
            if p_tag and p_tag.is_displayed():
                log_message(" Đang nhập nội dung trả lời...", logging.INFO)
                
                # Click vào p_tag trước khi nhập
                p_tag.click()
                await asyncio.sleep(1)
                
                # Nhập nội dung trả lời
                actions = ActionChains(browser)
                actions.send_keys_to_element(p_tag, reply_content)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Gửi trả lời bằng cách nhấn Enter
                actions.send_keys(Keys.ENTER)
                actions.perform()
                
                log_message("Đã gửi trả lời thành công!", logging.INFO)
                await asyncio.sleep(3)
                
                # Tìm timestamp của reply trong container cụ thể
                try:
                    log_message("Đang tìm timestamp của reply trong container...", logging.INFO)
                    
                    # Khởi tạo biến reply_url và reply_id
                    reply_url = None
                    reply_id = None
                    
                    # Đợi một chút để reply xuất hiện trong DOM
                    await asyncio.sleep(2)
                    
                    # Tìm lại comment container để có phần tử mới
                    comment_container = await find_comment_container(browser, comment_id_from_websocket)
                    if not comment_container:
                        log_message(" Không tìm thấy comment container sau khi reply", logging.WARNING)
                        return
                    
                    # Tìm tất cả timestamp, ưu tiên reply_comment_id
                    reply_timestamps = comment_container.find_elements(By.XPATH, ".//a[contains(@href, 'reply_comment_id')]")

                    if reply_timestamps:
                        # Lấy timestamp reply mới nhất và lấy href trực tiếp
                        timestamp_element = reply_timestamps[-1]
                        reply_url = timestamp_element.get_attribute('href')
                        log_message(f"Lấy link từ reply timestamp mới nhất: {reply_url}", logging.INFO)
                        
                        # Trích xuất reply_id từ href
                        reply_id_patterns = [
                            r'reply_comment_id=(\d+)',
                            r'comment_id=(\d+)',
                            r'cft\[0\]=(\d+)'
                        ]
                        
                        for pattern in reply_id_patterns:
                            try:
                                reply_id_match = re.search(pattern, reply_url)
                                if reply_id_match:
                                    reply_id = reply_id_match.group(1)
                                    log_message(f"Lấy được Reply ID từ href: {reply_id}", logging.INFO)
                                    break
                            except Exception as pattern_err:
                                log_message(f" Lỗi pattern {pattern}: {pattern_err}", logging.WARNING)
                    else:
                        # Nếu không có reply_comment_id, tìm tất cả timestamp và lấy mới nhất
                        all_timestamps = comment_container.find_elements(By.XPATH, ".//a[contains(@href, 'comment_id')]")
                        
                        # # Debug: In ra tất cả timestamps
                        # log_message(f"DEBUG: Tìm thấy {len(all_timestamps)} timestamps chứa comment_id:", logging.INFO)
                        # for i, ts in enumerate(all_timestamps):
                        #     href = ts.get_attribute('href')
                        #     text = ts.text.strip() if ts.text else "No text"
                        #     log_message(f"  {i+1}. Timestamp: {href} | Text: '{text}'", logging.INFO)
                        
                        if all_timestamps:
                            timestamp_element = all_timestamps[-1]
                            reply_url = timestamp_element.get_attribute('href')
                            log_message(f"Lấy link từ timestamp (fallback): {reply_url}", logging.INFO)
                            
                            # Trích xuất reply_id từ href
                            reply_id_patterns = [
                                r'reply_comment_id=(\d+)',
                                r'comment_id=(\d+)',
                                r'cft\[0\]=(\d+)'
                            ]
                            
                            for pattern in reply_id_patterns:
                                try:
                                    reply_id_match = re.search(pattern, reply_url)
                                    if reply_id_match:
                                        reply_id = reply_id_match.group(1)
                                        log_message(f"Lấy được Reply ID từ href (fallback): {reply_id}", logging.INFO)
                                        break
                                except Exception as pattern_err:
                                    log_message(f" Lỗi pattern {pattern}: {pattern_err}", logging.WARNING)
                        else:
                            log_message(" Không tìm thấy timestamp nào", logging.WARNING)
                            return
                        
                except Exception as reply_id_error:
                    log_message(f" Lỗi khi lấy reply_id: {reply_id_error}", logging.ERROR)
                
                # Lưu reply vào cấu trúc dữ liệu nếu có đủ thông tin
                if extracted_post_id and comment_id_from_websocket and reply_id:
                    add_reply_to_structure(extracted_post_id, comment_id_from_websocket, reply_id, reply_content)
                elif extracted_post_id and comment_id_from_websocket:
                    # Lưu với reply_id tạm thời nếu không lấy được reply_id từ URL
                    temp_reply_id = f"temp_reply_{int(time.time() * 1000)}"
                    add_reply_to_structure(extracted_post_id, comment_id_from_websocket, temp_reply_id, reply_content)
                
                # Lưu reply comment vào database trước khi gửi qua WebSocket
                try:
                    user_ids = get_id_tosend_websocket()
                    user_name = get_facebook_name()
                    
                    # Lấy commenter name từ post structure hoặc user accounts
                    commenter_name = get_commenter_name(extracted_post_id, comment_id_from_websocket, reply_id)
                    if not commenter_name:
                        commenter_name = user_name  # Fallback về tên Facebook hiện tại
                    
                    # Lấy link commenter từ post structure nếu có
                    commenter_link = ""
                    try:
                        post_info = get_post_structure_info(extracted_post_id)
                        if post_info and "comments" in post_info:
                            for comment_key, comment_data in post_info["comments"].items():
                                if isinstance(comment_data, dict) and comment_key == comment_id_from_websocket:
                                    if "replies" in comment_data and reply_id:
                                        for reply_key, reply_data in comment_data["replies"].items():
                                            if isinstance(reply_data, dict) and reply_key == reply_id:
                                                commenter_link = reply_data.get("commenter_link", "")
                                                break
                                    break
                    except Exception as e:
                        log_message(f"Lỗi khi lấy reply commenter_link: {e}", logging.WARNING)
                    
                    payloadReplyComment = {
                        "userId": userId,
                        "userNameFacebook": user_name,  
                        "content": reply_content,
                        "userLinkFb": commenter_link,  # Link profile người reply
                        "facebookReplyUrl": reply_url if reply_url else "",
                        "id_facebookReply": reply_id if reply_id else f"temp_reply_{int(time.time() * 1000)}",
                        "replyToAuthor": commenter_name,
                        "createdAt": int(time.time()),  
                        "updatedAt": int(time.time())  
                    }
                    
                    # Gọi API để lưu reply comment (async)
                    # Cần có comment_id_from_websocket làm facebook_comment_id
                    if comment_id_from_websocket:
                        response = await create_reply_comment(comment_id_from_websocket, payloadReplyComment)
                        if response:
                            log_message("Đã lưu reply comment vào database thành công!", logging.INFO)
                        else:
                            log_message("Lỗi khi lưu reply comment vào database", logging.WARNING)
                    else:
                        log_message("Không có comment_id_from_websocket để gọi API reply comment", logging.WARNING)
                        
                except Exception as db_error:
                    log_message(f"Lỗi khi lưu reply comment vào database: {db_error}", logging.ERROR)
                
                # Gửi thông báo thành công về bên A qua WebSocket
                try:
                    reply_comment_result = {
                        "type": "reply_comment_result",
                        "status": "success",
                        "URL": reply_url,
                        "reply_content": reply_content,
                        "authorName": get_facebook_name(),
                        "timestamp": datetime.now().isoformat()
                    }

                    
                    if reply_id:
                        reply_comment_result["replyId"] = reply_id
                        log_message(f"Thêm replyId vào kết quả: {reply_id}", logging.INFO)
                    
                    # Thêm commentId nếu có từ WebSocket
                    if comment_id_from_websocket:
                        reply_comment_result["commentId"] = comment_id_from_websocket
                        log_message(f"Đã thêm commentId vào kết quả: {comment_id_from_websocket}", logging.INFO)
                    
                    # Thêm postId nếu có từ WebSocket
                    if post_id_from_websocket:
                        reply_comment_result["postId"] = post_id_from_websocket
                        log_message(f"Đã thêm postId vào kết quả: {post_id_from_websocket}", logging.INFO)
                    
                    # Thêm thông tin user_id từ tài khoản hiện tại
                    user_ids = get_id_tosend_websocket()
                    reply_comment_result["to"] = user_ids
                    
                    # Gửi kết quả qua WebSocket
                    async def send_reply_result():
                        try:
                            async with websockets.connect(WEBSOCKET_URL) as websocket:
                                
                                # Gửi kết quả trả lời
                                await websocket.send(json.dumps(reply_comment_result))
                                log_message("Đã gửi kết quả trả lời về bên A!", logging.INFO)
                        except Exception as ws_error:
                            log_message(f" Lỗi khi gửi kết quả qua WebSocket: {ws_error}", logging.ERROR)
                    
                    await send_reply_result()
                    
                except Exception as result_error:
                    log_message(f" Lỗi khi chuẩn bị gửi kết quả: {result_error}", logging.ERROR)
            else:
                log_message(" Không tìm thấy thẻ p trong reply box", logging.ERROR)
        except Exception as input_error:
            log_message(f" Lỗi khi nhập nội dung trả lời: {input_error}", logging.ERROR)
        
        # Nhấn ESC để thoát
        try:
            actions.send_keys(Keys.ESCAPE).perform()
        except:
            pass
            
    except Exception as e:
        log_message(f" Lỗi trong hàm reply_to_comment: {e}", logging.ERROR)
        traceback.print_exc()
        
        # Gửi thông báo lỗi về bên A
        try:
            if 'comment_url' in locals() and 'reply_content' in locals():
                error_result = {
                    "type": "reply_comment_result",
                    "status": "error",
                    "URL": comment_url,
                    "reply_content": reply_content,
                    "authorName": get_facebook_name(),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                if 'comment_id_from_websocket' in locals() and comment_id_from_websocket:
                    error_result["commentId"] = comment_id_from_websocket
                
                if 'post_id_from_websocket' in locals() and post_id_from_websocket:
                    error_result["postId"] = post_id_from_websocket
                
                # Thêm thông tin user_id từ tài khoản hiện tại
                user_ids = get_id_tosend_websocket()
                error_result["to"] = user_ids
                
                async def send_error_result():
                    try:
                        async with websockets.connect(WEBSOCKET_URL) as websocket:
                            await websocket.send(json.dumps(error_result))
                            log_message("Đã gửi thông báo lỗi về bên A", logging.INFO)
                    except:
                        pass
                
                await send_error_result()
        except:
            pass


# Hàm trả lời reply comment (reply to reply)
async def reply_to_reply_comment(browser):
    """
    Hàm trả lời reply comment cụ thể dựa vào URL, commentId và replyId
    """
    try:
        global pending_posts, current_client_id
        
        # Khởi tạo biến để tránh lỗi UnboundLocalError
        reply_to_reply_url = None
        reply_to_reply_id = None
        comment_url = ""
        reply_content = ""
        comment_id_from_websocket = ""
        reply_id_from_websocket = ""
        post_id_from_websocket = None
        
        if not pending_posts:
            log_message(" Không có dữ liệu reply_reply_comment trong pending_posts", logging.ERROR)
            return
        
        # Lấy dữ liệu từ WebSocket
        reply_data = pending_posts[0]
        pending_posts.pop(0)
        
        comment_url = reply_data.get("URL", "")
        reply_content = reply_data.get("content", "")
        comment_id_from_websocket = reply_data.get("commentId", "")
        reply_id_from_websocket = reply_data.get("replyId", "")
        post_id_from_websocket = reply_data.get("postId", None)
        
        log_message(f"Bắt đầu trả lời reply comment có CommentID: {comment_id_from_websocket}, ReplyID: {reply_id_from_websocket}", logging.INFO)
        log_message(f"URL: {comment_url}", logging.INFO)
        log_message(f" Nội dung trả lời: {reply_content}", logging.INFO)
        if post_id_from_websocket:
            log_message(f"PostId từ WebSocket: {post_id_from_websocket}", logging.INFO)
        
        if not comment_url or not reply_content or not comment_id_from_websocket or not reply_id_from_websocket:
            log_message(" Thiếu URL, nội dung trả lời, commentId hoặc replyId", logging.ERROR)
            return
        
        # Sử dụng post_id từ WebSocket hoặc extract từ URL
        extracted_post_id = post_id_from_websocket
        if not extracted_post_id:
            # Thử extract post_id từ URL nếu không có từ WebSocket
            post_id_match = re.search(r'posts/(\d+)', comment_url)
            if post_id_match:
                extracted_post_id = post_id_match.group(1)
            else:
                extracted_post_id = comment_url  # Use full URL as fallback
        
        # Điều hướng đến URL
        log_message("Đang điều hướng đến URL...", logging.INFO)
        browser.get(comment_url)
        await asyncio.sleep(random.uniform(3, 5))
        
        # Tìm container chứa commentId và replyId cần trả lời
        log_message(f"Đang tìm container chứa CommentId: {comment_id_from_websocket} và ReplyId: {reply_id_from_websocket}", logging.INFO)
        reply_container = None
        
        try:
            # Tìm theo href chứa reply_comment_id và mở rộng đến container có class cụ thể
            reply_links = browser.find_elements(By.XPATH, f"//a[contains(@href, 'reply_comment_id={reply_id_from_websocket}')]")
            
            log_message(f"Tìm thấy {len(reply_links)} link chứa reply_comment_id={reply_id_from_websocket}:", logging.INFO)
            for i, link in enumerate(reply_links):
                try:
                    href = link.get_attribute("href")
                    text = link.get_attribute("textContent") or "No text"
                    log_message(f"  Reply Link {i+1}: {href} - Text: '{text.strip()}'", logging.INFO)
                except Exception as e:
                    log_message(f"  Reply Link {i+1}: Lỗi khi lấy thông tin - {e}", logging.WARNING)
            
            if reply_links:
                # Tìm container cha có class 'x6s0dn4 x3nfvp2'
                for link in reply_links:
                    try:
                        # Mở rộng từ thẻ a đến khi gặp container có class cụ thể
                        container = link.find_element(By.XPATH, "./ancestor::div[@class='x6s0dn4 x3nfvp2'][1]")
                        if container:
                            # Kiểm tra container này có chứa reply link không
                            check_links = container.find_elements(By.XPATH, f".//a[contains(@href, 'reply_comment_id={reply_id_from_websocket}')]")
                            if check_links:
                                reply_container = container
                                log_message(f"Tìm thấy reply container với class cụ thể cho replyId: {reply_id_from_websocket}", logging.INFO)
                                break
                    except Exception as e:
                        log_message(f"Lỗi khi tìm container với class cụ thể: {e}", logging.WARNING)
                        continue
                
                # Nếu không tìm được container với class cụ thể, thử fallback
                if not reply_container:
                    for link in reply_links:
                        try:
                            # Fallback: tìm container cha gần nhất có chứa nút button
                            container = link.find_element(By.XPATH, "./ancestor::div[.//div[@role='button']][1]")
                            if container:
                                check_links = container.find_elements(By.XPATH, f".//a[contains(@href, 'reply_comment_id={reply_id_from_websocket}')]")
                                if check_links:
                                    reply_container = container
                                    log_message(f"Tìm thấy reply container fallback cho ReplyId: {reply_id_from_websocket}", logging.INFO)
                                    break
                        except Exception:
                            continue
    
                        
        except Exception as e:
            log_message(f" Lỗi khi tìm container reply: {e}", logging.ERROR)
        
        if not reply_container:
            log_message(f" Không tìm thấy container chứa CommentId: {comment_id_from_websocket} và ReplyId: {reply_id_from_websocket}", logging.ERROR)
            return
        
        # Tìm nút Trả lời trong reply container
        reply_button = None
        try:
            # Tìm nút Trả lời đơn giản trong reply container
            reply_selectors = [
                ".//div[@role='button' and normalize-space(text())='Trả lời']",
                ".//div[@role='button' and contains(@aria-label, 'Trả lời')]",
                ".//div[@role='button' and contains(text(), 'Trả lời')]",
                ".//span[normalize-space(text())='Trả lời']/ancestor::div[@role='button'][1]"
            ]
            
            for selector in reply_selectors:
                try:
                    reply_buttons = reply_container.find_elements(By.XPATH, selector)
                    for btn in reply_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            reply_button = btn
                            btn_text = btn.text.strip() if btn.text else ""
                            btn_aria_label = btn.get_attribute('aria-label') or ""
                            log_message(f"Tìm thấy nút Trả lời trong reply container - Text: '{btn_text}', Aria-label: '{btn_aria_label}'", logging.INFO)
                            break
                    if reply_button:
                        break
                except Exception:
                    continue
                        
        except Exception as e:
            log_message(f" Lỗi khi tìm nút Trả lời trong container: {e}", logging.ERROR)
        
        if not reply_button:
            log_message(" Không tìm thấy nút Trả lời trong container reply", logging.ERROR)
            return
        
        # Click vào nút trả lời
        log_message("Đang click nút Trả lời cho reply...", logging.INFO)
        try:
            # Scroll vào view trước
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_button)
            await asyncio.sleep(1)
            
            # Thử nhiều cách click
            click_success = False
            for attempt in range(3):
                try:
                    if attempt == 0:
                        reply_button.click()
                    elif attempt == 1:
                        browser.execute_script("arguments[0].click();", reply_button)
                    elif attempt == 2:
                        ActionChains(browser).move_to_element(reply_button).click().perform()
                    
                    click_success = True
                    log_message(f"Click nút Trả lời thành công (cách {attempt + 1})", logging.INFO)
                    break
                except Exception as click_err:
                    log_message(f" Click attempt {attempt + 1} thất bại: {click_err}", logging.WARNING)
                    await asyncio.sleep(0.5)
            
            if not click_success:
                log_message(" Không thể click nút Trả lời sau 3 lần thử", logging.ERROR)
                return
                
        except Exception as e:
            log_message(f" Lỗi khi click nút Trả lời: {e}", logging.ERROR)
            return
        
        await asyncio.sleep(2)
        
        # Tìm reply box (comment box mới xuất hiện)
        log_message("Đang tìm reply box...", logging.INFO)
        reply_box = None
        try:
            wait = WebDriverWait(browser, 10)
            reply_boxes = browser.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"]')
            
            # Lấy reply box đầu tiên (thay vì cuối cùng)
            for box in reply_boxes:
                if box.is_displayed():
                    reply_box = box
                    log_message("Đã tìm thấy reply box đầu tiên", logging.INFO)
                    break
            
            if not reply_box:
                # Thử cách khác
                reply_box = browser.find_element(By.XPATH, '//div[@contenteditable="true" and @role="textbox"]')
                log_message("Đã tìm thấy reply box (cách 2)", logging.INFO)
        except:
            log_message(" Không tìm thấy reply box", logging.ERROR)
            return
        
        if not reply_box:
            log_message(" Không thể tìm thấy reply box", logging.ERROR)
            return
        
        await asyncio.sleep(1)
        
        # Nhập nội dung trả lời
        try:
            p_tag = reply_box.find_element(By.TAG_NAME, "p")
            if p_tag and p_tag.is_displayed():
                log_message(" Đang nhập nội dung trả lời reply...", logging.INFO)
                
                # Click vào p_tag trước khi nhập
                p_tag.click()
                await asyncio.sleep(1)
                
                # Nhập nội dung trả lời
                actions = ActionChains(browser)
                actions.send_keys_to_element(p_tag, reply_content)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Gửi trả lời bằng cách nhấn Enter
                actions.send_keys(Keys.ENTER)
                actions.perform()
                
                log_message("Đã gửi trả lời reply thành công!", logging.INFO)
                await asyncio.sleep(3)
                
                # Tìm timestamp của reply to reply trong comment container (sử dụng logic giống reply_to_comment)
                try:
                    log_message("Đang tìm timestamp của reply to reply trong comment container...", logging.INFO)
                    
                    # Khởi tạo biến reply_to_reply_url và reply_to_reply_id
                    reply_to_reply_url = None
                    reply_to_reply_id = None
                    
                    # Đợi một chút để reply xuất hiện trong DOM
                    await asyncio.sleep(2)
                    
                    # Tìm lại comment container để có phần tử mới (giống như trong reply_to_comment)
                    comment_container_for_timestamp = await find_comment_container(browser, comment_id_from_websocket)
                    if not comment_container_for_timestamp:
                        log_message(" Không tìm thấy comment container sau khi reply to reply", logging.WARNING)
                        return
                    
                    # Tìm tất cả timestamp, ưu tiên reply_comment_id (giống logic reply_to_comment)
                    reply_timestamps = comment_container_for_timestamp.find_elements(By.XPATH, ".//a[contains(@href, 'reply_comment_id')]")

                    if reply_timestamps:
                        # Lấy timestamp reply mới nhất và lấy href trực tiếp
                        timestamp_element = reply_timestamps[-1]
                        reply_to_reply_url = timestamp_element.get_attribute('href')
                        log_message(f"Lấy link từ reply to reply timestamp mới nhất: {reply_to_reply_url}", logging.INFO)
                        
                        # Trích xuất reply_to_reply_id từ href
                        reply_id_patterns = [
                            r'reply_comment_id=(\d+)',
                            r'comment_id=(\d+)',
                            r'cft\[0\]=(\d+)'
                        ]
                        
                        for pattern in reply_id_patterns:
                            try:
                                reply_id_match = re.search(pattern, reply_to_reply_url)
                                if reply_id_match:
                                    reply_to_reply_id = reply_id_match.group(1)
                                    log_message(f"Lấy được Reply to Reply ID từ href: {reply_to_reply_id}", logging.INFO)
                                    break
                            except Exception as pattern_err:
                                log_message(f" Lỗi pattern {pattern}: {pattern_err}", logging.WARNING)
                    else:
                        # Nếu không có reply_comment_id, tìm tất cả timestamp và lấy mới nhất
                        all_timestamps = comment_container_for_timestamp.find_elements(By.XPATH, ".//a[contains(@href, 'comment_id')]")
                        
                        # # Debug: In ra tất cả timestamps
                        # log_message(f"DEBUG: Tìm thấy {len(all_timestamps)} timestamps chứa comment_id:", logging.INFO)
                        # for i, ts in enumerate(all_timestamps):
                        #     href = ts.get_attribute('href')
                        #     text = ts.text.strip() if ts.text else "No text"
                        #     log_message(f"  {i+1}. Timestamp: {href} | Text: '{text}'", logging.INFO)
                        
                        if all_timestamps:
                            timestamp_element = all_timestamps[-1]
                            reply_to_reply_url = timestamp_element.get_attribute('href')
                            log_message(f"Lấy link từ timestamp (fallback): {reply_to_reply_url}", logging.INFO)
                            
                            # Trích xuất reply_to_reply_id từ href
                            reply_id_patterns = [
                                r'reply_comment_id=(\d+)',
                                r'comment_id=(\d+)',
                                r'cft\[0\]=(\d+)'
                            ]
                            
                            for pattern in reply_id_patterns:
                                try:
                                    reply_id_match = re.search(pattern, reply_to_reply_url)
                                    if reply_id_match:
                                        reply_to_reply_id = reply_id_match.group(1)
                                        log_message(f"Lấy được Reply to Reply ID từ href (fallback): {reply_to_reply_id}", logging.INFO)
                                        break
                                except Exception as pattern_err:
                                    log_message(f" Lỗi pattern {pattern}: {pattern_err}", logging.WARNING)
                        else:
                            log_message(" Không tìm thấy timestamp nào", logging.WARNING)
                            return
                        
                except Exception as reply_id_error:
                    log_message(f"Lỗi khi lấy reply to reply id: {reply_id_error}", logging.ERROR)
                
                # Lưu reply vào cấu trúc dữ liệu nếu có đủ thông tin
                if extracted_post_id and comment_id_from_websocket and reply_to_reply_id:
                    add_reply_to_structure(extracted_post_id, comment_id_from_websocket, reply_to_reply_id, reply_content)
                elif extracted_post_id and comment_id_from_websocket:
                    # Lưu với reply_id tạm thời nếu không lấy được reply_to_reply_id từ URL
                    temp_reply_id = f"temp_reply_to_reply_{int(time.time() * 1000)}"
                    add_reply_to_structure(extracted_post_id, comment_id_from_websocket, temp_reply_id, reply_content)
                
                # Lưu reply to reply comment vào database trước khi gửi qua WebSocket
                try:
                    user_ids = get_id_tosend_websocket()
                    user_name = get_facebook_name()
                    userId = reply_data.get("authorId", "")
                    
                    # Lấy commenter name từ post structure hoặc user accounts
                    commenter_name = reply_data.get("replyToAuthor")
                    if not commenter_name:
                        commenter_name = get_commenter_name(extracted_post_id, comment_id_from_websocket, reply_to_reply_id)
                    if not commenter_name:
                        commenter_name = user_name  # Fallback về tên Facebook hiện tại
                    
                    # Lấy link commenter từ post structure nếu có
                    commenter_link = ""
                    try:
                        post_info = get_post_structure_info(extracted_post_id)
                        if post_info and "comments" in post_info:
                            for comment_key, comment_data in post_info["comments"].items():
                                if isinstance(comment_data, dict) and comment_key == comment_id_from_websocket:
                                    if "replies" in comment_data and reply_to_reply_id:
                                        for reply_key, reply_data_struct in comment_data["replies"].items():
                                            if isinstance(reply_data_struct, dict) and reply_key == reply_to_reply_id:
                                                commenter_link = reply_data_struct.get("commenter_link", "")
                                                break
                                    break
                    except Exception as e:
                        log_message(f"Lỗi khi lấy reply to reply commenter_link: {e}", logging.WARNING)
                    
                    payloadReplyComment = {
                        "userId": userId,
                        "userNameFacebook": user_name,  
                        "content": reply_content,
                        "userLinkFb": commenter_link,  # Link profile người reply
                        "facebookReplyUrl": reply_to_reply_url if reply_to_reply_url else "",
                        "id_facebookReply": reply_to_reply_id if reply_to_reply_id else f"temp_reply_{int(time.time() * 1000)}",
                        "replyToAuthor": commenter_name,
                        "createdAt": int(time.time()),  
                        "updatedAt": int(time.time())  
                    }
                    
                    # Gọi API để lưu reply comment (async) - sử dụng comment_id_from_websocket làm facebook_comment_id
                    if comment_id_from_websocket:
                        response = await create_reply_comment(comment_id_from_websocket, payloadReplyComment)
                        if response:
                            log_message("Đã lưu reply to reply comment vào database thành công!", logging.INFO)
                        else:
                            log_message("Lỗi khi lưu reply to reply comment vào database", logging.WARNING)
                    else:
                        log_message("Không có comment_id_from_websocket để gọi API reply to reply comment", logging.WARNING)
                        
                except Exception as db_error:
                    log_message(f"Lỗi khi lưu reply to reply comment vào database: {db_error}", logging.ERROR)
                
                # Gửi thông báo thành công về bên A qua WebSocket
                try:
                    reply_to_reply_result = {
                        "type": "reply_reply_comment_result",
                        "status": "success",
                        "URL": reply_to_reply_url,
                        "reply_content": reply_content,
                        "authorName": get_facebook_name(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Thêm và reply_to_reply_id nếu lấy được
                    
                    if reply_to_reply_id:
                        reply_to_reply_result["reply_to_reply_id"] = reply_to_reply_id
                        log_message(f"Thêm reply_to_reply_id vào kết quả: {reply_to_reply_id}", logging.INFO)
                    
                    # Thêm các ID từ WebSocket
                    if comment_id_from_websocket:
                        reply_to_reply_result["commentId"] = comment_id_from_websocket
                        log_message(f"Đã thêm commentId vào kết quả: {comment_id_from_websocket}", logging.INFO)
                    
                    if reply_id_from_websocket:
                        reply_to_reply_result["replyId"] = reply_id_from_websocket
                        log_message(f"Đã thêm replyId vào kết quả: {reply_id_from_websocket}", logging.INFO)
                    
                    if post_id_from_websocket:
                        reply_to_reply_result["postId"] = post_id_from_websocket
                        log_message(f"Đã thêm postId vào kết quả: {post_id_from_websocket}", logging.INFO)
                    
                    # Thêm thông tin user_id từ tài khoản hiện tại
                    user_ids = get_id_tosend_websocket()
                    reply_to_reply_result["to"] = user_ids
                    
                    # Gửi kết quả qua WebSocket
                    async def send_reply_to_reply_result():
                        try:
                            async with websockets.connect(WEBSOCKET_URL) as websocket:
                                
                                # # Gửi kết quả trả lời reply
                                await websocket.send(json.dumps(reply_to_reply_result))
                                log_message("Đã gửi kết quả trả lời reply về bên A!", logging.INFO)
                        except Exception as ws_error:
                            log_message(f" Lỗi khi gửi kết quả qua WebSocket: {ws_error}", logging.ERROR)
                    
                    await send_reply_to_reply_result()
                    
                except Exception as result_error:
                    log_message(f" Lỗi khi chuẩn bị gửi kết quả: {result_error}", logging.ERROR)
            else:
                log_message(" Không tìm thấy thẻ p trong reply box", logging.ERROR)
        except Exception as input_error:
            log_message(f" Lỗi khi nhập nội dung trả lời reply: {input_error}", logging.ERROR)
        
        # Nhấn ESC để thoát
        try:
            actions.send_keys(Keys.ESCAPE).perform()
        except:
            pass
            
    except Exception as e:
        log_message(f" Lỗi trong hàm reply_to_reply_comment: {e}", logging.ERROR)
        traceback.print_exc()
        
        # Gửi thông báo lỗi về bên A
        try:
            if 'comment_url' in locals() and 'reply_content' in locals():
                error_result = {
                    "type": "reply_reply_comment_result",
                    "status": "error",
                    "URL": comment_url,
                    "reply_content": reply_content,
                    "authorName": get_facebook_name(),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                if 'comment_id_from_websocket' in locals() and comment_id_from_websocket:
                    error_result["commentId"] = comment_id_from_websocket
                
                if 'reply_id_from_websocket' in locals() and reply_id_from_websocket:
                    error_result["replyId"] = reply_id_from_websocket
                
                if 'post_id_from_websocket' in locals() and post_id_from_websocket:
                    error_result["postId"] = post_id_from_websocket
                
                # Thêm thông tin user_id từ tài khoản hiện tại
                user_ids = get_id_tosend_websocket()
                error_result["to"] = user_ids
                
                async def send_error_result():
                    try:
                        async with websockets.connect(WEBSOCKET_URL) as websocket:
                            
                            await websocket.send(json.dumps(error_result))
                            log_message("Đã gửi thông báo lỗi về bên A", logging.INFO)
                    except:
                        pass
                
                await send_error_result()
        except:
            pass


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

# Hàm tạo bài viết mới
async def post_news_feed(browser):
    try:
        # Kiểm tra xem có nội dung từ WebSocket không
        if not pending_posts:
            log_message("Không có nội dung từ WebSocket để đăng bài. Bỏ qua việc đăng bài.", logging.WARNING)
            return
        
        # Lấy nội dung từ WebSocket
        post_data = pending_posts.pop(0)
        content = post_data.get("content", "")
        userId = post_data.get("authorId", "")
        downloaded_images = post_data.get("downloaded_images", [])
        original_attachments = post_data.get("attachments", [])  # Lấy attachments gốc từ WebSocket
        post_id_from_websocket = post_data.get("postId", None)  # Lưu postId từ WebSocket
        
        if not content:
            log_message("Nội dung từ WebSocket rỗng. Bỏ qua việc đăng bài.", logging.WARNING)
            # Xóa ảnh nếu có
            for image_path in downloaded_images:
                delete_image(image_path)
            return
        
        log_message(f"Đang đăng bài với nội dung từ WebSocket: {content[:50]}...", logging.INFO)
        if post_id_from_websocket:
            log_message(f"PostId từ WebSocket: {post_id_from_websocket}", logging.INFO)
        if downloaded_images:
            log_message(f"Sẽ đính kèm {len(downloaded_images)} ảnh (đã tải về)", logging.INFO)
        if original_attachments:
            log_message(f"Attachments gốc từ WebSocket: {len(original_attachments)} files", logging.INFO)
            for idx, attachment in enumerate(original_attachments):
                if attachment.get("type", "").startswith("image"):
                    log_message(f"  - Ảnh {idx + 1}: {attachment.get('name', 'N/A')} -> URL: {attachment.get('url', 'N/A')}", logging.INFO)

        await asyncio.sleep(random.uniform(5, 8))
        actions = ActionChains(browser)
        # Thử tìm nút Home, nếu không có thì tải lại trang chủ Facebook
        home = None
        try:
            home = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Home' or @aria-label='Trang chủ' or @aria-label='Facebook']"))
            )
        except Exception:
            log_message("Không tìm thấy nút Home hoặc nút Home không thể click, sẽ tải lại trang chủ Facebook để đăng bài.", logging.INFO)
            # Tải lại trang chủ Facebook
            browser.get("https://www.facebook.com")
            await asyncio.sleep(random.uniform(5, 8))

    
        if home:
            try:
                # Scroll nút Home vào view trước khi click
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", home)
                await asyncio.sleep(1)
                home.click()
                await asyncio.sleep(random.uniform(5, 8))
                log_message("Đã click nút Home thành công", logging.INFO)
            except Exception as e:
                log_message(f"Không thể click nút Home: {e}. Thử click bằng JavaScript hoặc tải lại trang chủ.", logging.WARNING)
                try:
                    # Thử click bằng JavaScript
                    browser.execute_script("arguments[0].click();", home)
                    await asyncio.sleep(random.uniform(5, 8))
                    log_message("Đã click nút Home bằng JavaScript", logging.INFO)
                except Exception as js_err:
                    log_message(f"Click JavaScript cũng thất bại: {js_err}. Tải lại trang chủ Facebook để đăng bài.", logging.WARNING)
                    # Tải lại trang chủ Facebook làm phương án cuối cùng
                    browser.get("https://www.facebook.com")
                    await asyncio.sleep(random.uniform(5, 8))

        # Tìm nút tạo bài viết mới (phải dùng @class) - Chỉ dùng cho trường hợp không có ảnh
        h3_post = None
        try:
            h3_post = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='xi81zsa x1lkfr7t xkjl1po x1mzt3pk xh8yej3 x13faqbe']"))
            )
        except Exception:
            log_message("Không tìm thấy nút tạo bài viết mới sau khi về trang chủ.", logging.ERROR)
            return

        # Phân biệt có ảnh và không có ảnh
        if downloaded_images:
            # TRƯỜNG HỢP CÓ ẢNH: Bấm vào button upload ảnh có class cụ thể
            log_message(f"Phát hiện {len(downloaded_images)} ảnh, sẽ bấm button upload ảnh", logging.INFO)
            try:
                # Tìm button upload ảnh có class cụ thể (dùng @class như h3_post)
                try:
                    # Cách 1: Dùng class
                    photo_button = WebDriverWait(browser, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@class='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft']"))
                    )
                    print("Tìm thấy bằng class.")
                except TimeoutException:
                    try:
                        # Cách 2: Dùng text tiếng Việt / tiếng Anh
                        photo_button = WebDriverWait(browser, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//span[text()='Ảnh/video' or text()='Photo/video']"))
                        )
                        print("Tìm thấy bằng text.")
                    except TimeoutException:
                        print("Không tìm thấy nút Ảnh/video bằng cả hai cách.")
                        photo_button = None

                # Click nếu tìm được
                if photo_button:
                    photo_button.click()
                log_message("Tìm thấy button upload ảnh với class cụ thể", logging.INFO)
                photo_button.click()
                await asyncio.sleep(2)
                
                # Tìm input file để upload ảnh
                file_input = None
                try:
                    file_input = browser.find_element(By.CSS_SELECTOR, 'input[type="file"][accept*="image"]')
                    log_message("Tìm thấy input file sau khi click nút ảnh", logging.INFO)
                except:
                    log_message("Không thể tìm thấy input file", logging.WARNING)
                
                if file_input:
                    # Upload tất cả ảnh cùng lúc
                    all_images_path = '\n'.join(downloaded_images)
                    file_input.send_keys(all_images_path)
                    log_message(f"Đã upload ảnh: {all_images_path}", logging.INFO)
                    
                    # ĐỢI DOM ỔN ĐỊNH - Chờ ảnh load và preview render hoàn tất
                    await asyncio.sleep(5)
                    log_message("Đợi 5s để ảnh upload và DOM ổn định", logging.INFO)
                    
                    # Kiểm tra preview đã load xong chưa
                    preview_loaded = False
                    for attempt in range(10):
                        try:
                            preview_elements = browser.find_elements(By.XPATH, "//div[contains(@class, 'x1n2onr6') or contains(@role, 'img') or contains(@class, 'x1ey2m1c')]")
                            if preview_elements and len(preview_elements) > 0:
                                log_message(f"Phát hiện {len(preview_elements)} preview elements - ảnh đã load xong!", logging.INFO)
                                preview_loaded = True
                                break
                            else:
                                log_message(f"Lần {attempt + 1}/10: Chưa phát hiện preview, đợi thêm 1s...", logging.INFO)
                                await asyncio.sleep(1)
                        except:
                            log_message(f"Lần {attempt + 1}/10: Lỗi khi kiểm tra preview, đợi thêm 1s...", logging.INFO)
                            await asyncio.sleep(1)
                    
                    if not preview_loaded:
                        log_message("Không phát hiện preview sau 10s, nhưng tiếp tục đăng bài", logging.WARNING)
                    
                    # Chờ thêm 2s để đảm bảo UI hoàn toàn ổn định
                    await asyncio.sleep(2)
                    log_message(f"Đã hoàn thành upload {len(downloaded_images)} ảnh", logging.INFO)
            except Exception as img_err:
                log_message(f"Lỗi khi upload ảnh: {img_err}", logging.ERROR)
                traceback.print_exc()
            
            # SAU KHI UPLOAD ẢNH: Nhập nội dung
            post_box = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='xzsf02u x1a2a7pz x1n2onr6 x14wi4xw x9f619 x1lliihq x5yr21d xh8yej3 notranslate']")))
            await asyncio.sleep(1)
            p_tag = post_box.find_element(By.TAG_NAME, "p")
            if p_tag and p_tag.is_displayed():
                p_tag.click()
                await asyncio.sleep(random.uniform(0.5, 1))
                await asyncio.sleep(2)
                actions.send_keys_to_element(p_tag, content)
                await asyncio.sleep(random.uniform(2, 4))
                actions.perform()
                await asyncio.sleep(2)
                log_message("Đã nhập nội dung sau khi upload ảnh", logging.INFO)
                browser.execute_script("document.activeElement.blur();")
                await asyncio.sleep(1)
        else:
            # TRƯỜNG HỢP KHÔNG CÓ ẢNH: Bấm h3_post để nhập nội dung
            log_message("Không có ảnh, sẽ bấm h3_post để nhập nội dung", logging.INFO)
            h3_post.click()
            # Chờ cho hộp thoại tạo bài viết mới xuất hiện
            await asyncio.sleep(random.uniform(2, 4))
            
            # Nhập nội dung
            # post_box = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
            post_box = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='xzsf02u x1a2a7pz x1n2onr6 x14wi4xw x9f619 x1lliihq x5yr21d xh8yej3 notranslate']")))
            await asyncio.sleep(1)
            p_tag = post_box.find_element(By.TAG_NAME, "p")
            if p_tag and p_tag.is_displayed():
                p_tag.click()
                await asyncio.sleep(random.uniform(0.5, 1))
                await asyncio.sleep(2)
                actions.send_keys_to_element(p_tag, content)
                await asyncio.sleep(random.uniform(2, 4))
                actions.perform()
                await asyncio.sleep(2)
                log_message("Đã nhập nội dung (không có ảnh)", logging.INFO)
                browser.execute_script("document.activeElement.blur();")
                await asyncio.sleep(1)
        
        # Đăng bài sau khi mọi thứ đã ổn định hoàn toàn
        log_message("Bắt đầu tìm nút Đăng...", logging.INFO)
        
        # Tìm nút đăng trong popup hiện tại
        try:
            post_new_button = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đăng']")
        except:
            try:
                post_new_button = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Post']")
            except:
                log_message("Không tìm thấy nút Đăng/Post", logging.ERROR)
                raise Exception("Không tìm thấy nút Đăng")
        
        log_message("Đã tìm thấy nút Đăng", logging.INFO)
        
        # Scroll nút đăng vào view để đảm bảo có thể click
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_new_button)
        await asyncio.sleep(1)
        
        # Thử click bằng nhiều cách khác nhau với retry mechanism
        click_success = False
        for attempt in range(3):
            try:
                if attempt == 0:
                    # Thử click thông thường trước
                    post_new_button.click()
                    log_message("Đã đăng bài viết thành công (click thông thường)!")
                    click_success = True
                    break
                elif attempt == 1:
                    # Thử click bằng JavaScript
                    browser.execute_script("arguments[0].click();", post_new_button)
                    log_message("Đã đăng bài viết thành công (JavaScript click)!")
                    click_success = True
                    break
                elif attempt == 2:
                    # Thử dùng ActionChains
                    actions = ActionChains(browser)
                    actions.move_to_element(post_new_button).click().perform()
                    log_message("Đã đăng bài viết thành công (ActionChains)!")
                    click_success = True
                    break
            except Exception as e:
                log_message(f" Lần thử {attempt + 1}/3 thất bại: {e}", logging.WARNING)
                await asyncio.sleep(1)  # Chờ 1s trước khi thử lại
        
        if not click_success:
            log_message(" Tất cả cách thức click đều thất bại!", logging.ERROR)
            raise Exception("Không thể click nút Đăng sau 3 lần thử")
        
        # Đợi bài viết được đăng thành công và lấy link bài viết
        await asyncio.sleep(random.uniform(4, 6))
        
        try:
            post_url = None
            post_id = None

            log_message("📝 Đang xác định bài viết vừa đăng...", logging.INFO)

            # Tìm bài viết đầu tiên trên trang theo `aria-posinset`
            first_post = None
            try:
                first_post = browser.find_element(By.XPATH, "//div[@aria-posinset='1']")
                log_message("Đã xác định bài viết đầu tiên bằng aria-posinset", logging.INFO)
            except Exception as e:
                log_message(" Không tìm thấy bài viết đầu tiên: " + str(e), logging.WARNING)

            # Tìm timestamp trong bài viết đầu tiên (lấy cái thứ 3, không phải tên người đăng)
            time_link = None
            if first_post:
                try:
                    # Tìm tất cả link có __cft__ trong bài viết, lấy cái thứ 3 (index 2)
                    time_links = first_post.find_elements(By.XPATH, ".//a[contains(@href, '__cft__')]")
                    if len(time_links) >= 3:
                        time_link = time_links[2]  # Lấy cái thứ 3 (timestamp)
                        log_message("Tìm thấy timestamp trong bài viết (link thứ 3)", logging.INFO)
                    elif len(time_links) >= 2:
                        time_link = time_links[1]  # Fallback nếu chỉ có 2 link
                        log_message("Chỉ tìm thấy 2 link __cft__, sử dụng link thứ 2 làm timestamp", logging.INFO)
                    elif len(time_links) == 1:
                        time_link = time_links[0]  # Fallback nếu chỉ có 1 link
                        log_message("Chỉ tìm thấy 1 link __cft__, sử dụng làm timestamp", logging.INFO)
                    else:
                        log_message(" Không tìm thấy link __cft__ nào trong bài viết", logging.WARNING)
                except Exception as e:
                    log_message(" Không tìm thấy timestamp trong bài viết: " + str(e), logging.WARNING)

            # Nếu không thấy timestamp trong bài viết, tìm toàn trang (fallback, lấy link thứ 3)
            if not time_link:
                try:
                    time_links = browser.find_elements(By.XPATH, "//a[contains(@href, '__cft__')]")
                    if len(time_links) >= 3:
                        time_link = time_links[2]  # Lấy cái thứ 3
                        log_message("Sử dụng fallback: tìm timestamp toàn trang (link thứ 3)", logging.INFO)
                    elif len(time_links) >= 2:
                        time_link = time_links[1]  # Fallback nếu chỉ có 2 link
                        log_message("Sử dụng fallback: chỉ có 2 link __cft__, sử dụng link thứ 2 làm timestamp", logging.INFO)
                    elif len(time_links) == 1:
                        time_link = time_links[0]  # Fallback nếu chỉ có 1 link
                        log_message("Sử dụng fallback: chỉ có 1 link __cft__, sử dụng làm timestamp", logging.INFO)
                    else:
                        log_message(" Không tìm thấy link __cft__ nào trên trang", logging.ERROR)
                except Exception as e:
                    log_message(" Không tìm thấy timestamp toàn trang: " + str(e), logging.ERROR)

            # Nếu tìm được timestamp → click → lấy URL thật
            if time_link:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", time_link)
                await asyncio.sleep(2)  # Tăng thời gian chờ để element ổn định

                # Thử nhiều phương pháp click khác nhau
                click_success = False
                post_url = None
                
                for attempt in range(5):  # Tăng số lần thử
                    try:
                        if attempt == 0:
                            # Phương pháp 1: Click thông thường
                            log_message(f"Lần thử {attempt + 1}: Click thông thường", logging.INFO)
                            time_link.click()
                            click_success = True
                            break
                            
                        elif attempt == 1:
                            # Phương pháp 2: JavaScript click
                            log_message(f"Lần thử {attempt + 1}: JavaScript click", logging.INFO)
                            browser.execute_script("arguments[0].click();", time_link)
                            click_success = True
                            break
                            
                        elif attempt == 2:
                            # Phương pháp 3: ActionChains click
                            log_message(f"Lần thử {attempt + 1}: ActionChains click", logging.INFO)
                            actions = ActionChains(browser)
                            actions.move_to_element(time_link).click().perform()
                            click_success = True
                            break
                        
                    except Exception as click_error:
                        log_message(f" Lần thử {attempt + 1} thất bại: {click_error}", logging.WARNING)
                        await asyncio.sleep(1)  # Chờ 1s trước khi thử lại
                        
                        # Kiểm tra lại element có còn tồn tại không
                        try:
                            time_link.is_displayed()
                        except:
                            log_message("Element timestamp bị mất, thử tìm lại...", logging.WARNING)
                            try:
                                if first_post:
                                    time_links = first_post.find_elements(By.XPATH, ".//a[contains(@href, '__cft__')]")
                                    if len(time_links) >= 3:
                                        time_link = time_links[2]  # Lấy cái thứ 3
                                    elif len(time_links) >= 2:
                                        time_link = time_links[1]  # Fallback link thứ 2
                                    elif len(time_links) == 1:
                                        time_link = time_links[0]  # Fallback link đầu tiên
                                else:
                                    time_links = browser.find_elements(By.XPATH, "//a[contains(@href, '__cft__')]")
                                    if len(time_links) >= 3:
                                        time_link = time_links[2]  # Lấy cái thứ 3
                                    elif len(time_links) >= 2:
                                        time_link = time_links[1]  # Fallback link thứ 2
                                    elif len(time_links) == 1:
                                        time_link = time_links[0]  # Fallback link đầu tiên
                                log_message("Đã tìm lại timestamp", logging.INFO)
                            except:
                                log_message(" Không thể tìm lại timestamp", logging.ERROR)
                                break
                        continue

                if click_success:
                    log_message("Đã click timestamp thành công!", logging.INFO)
                    await asyncio.sleep(3)  # Đợi trang load
                    post_url = browser.current_url
                    log_message(f"URL sau khi click timestamp: {post_url}", logging.INFO)
                else:
                    log_message(" Tất cả phương pháp click đều thất bại, thử lấy href thay thế", logging.WARNING)
                    try:
                        post_url = time_link.get_attribute("href")
                        if post_url:
                            log_message(f"Lấy URL từ href thay vì click: {post_url}", logging.INFO)
                        else:
                            log_message(" Không thể lấy href từ timestamp", logging.ERROR)
                    except Exception as href_error:
                        log_message(f" Lỗi khi lấy href: {href_error}", logging.ERROR)

            # Lấy URL bài viết
            if post_url:
                log_message(f"THÀNH CÔNG - Post URL: {post_url}", logging.INFO)
                
                # Lưu post vào database thông qua API TRƯỚC
                try:
                    log_message("Đang lưu post vào database...", logging.INFO)
                    
                    # Lấy current account để có thông tin user
                    current_account = get_current_account()
                    user_id = current_account.get("user_id_QLC", "") if current_account else ""
                    
    
                    
                    payloadPost = {
                        "facebookId": get_websocket_role(),
                        "userId": userId,
                        "userNameFacebook": get_facebook_name(),
                        "content": content,
                        "facebookPostId": post_id_from_websocket,
                        "facebookPostUrl": post_url,
                        "createdAt": int(time.time()), 
                        "updatedAt": int(time.time()),  
                        "attachments": [
                            {
                                "name": attachment.get("name", f"image_{idx}.png"),
                                "type": attachment.get("type", "image"),
                                "url": attachment.get("url", "")  # Sử dụng link ảnh từ WebSocket
                            } for idx, attachment in enumerate(original_attachments) if attachment.get("type", "").startswith("image")
                        ] if original_attachments else []
                    }
                    
                    # Gọi API để lưu post (async)
                    api_response = await create_post(payloadPost)
                    log_message(f"Đã lưu post vào database thành công: {api_response}", logging.INFO)
                    
                    # Log thông tin attachments đã gửi
                    if original_attachments:
                        log_message(f"📎 Đã lưu {len([att for att in original_attachments if att.get('type', '').startswith('image')])} ảnh với link gốc từ WebSocket", logging.INFO)
                    
                    # Lưu _id từ response để sử dụng sau này
                    database_post_id = None
                    if api_response and isinstance(api_response, dict):
                        database_post_id = api_response.get('_id') or api_response.get('id')
                        if database_post_id:
                            log_message(f"Lưu database_post_id: {database_post_id}", logging.INFO)
                        else:
                            log_message("Không tìm thấy _id trong API response", logging.WARNING)
                    
                except Exception as api_error:
                    log_message(f"Lỗi khi lưu post vào database: {api_error}", logging.ERROR)
                    database_post_id = None
                
                # SAU KHI có database_post_id, mới lưu post vào cấu trúc dữ liệu
                try:
                    saved_post_id = add_post_to_structure(post_url, post_id_from_websocket, database_post_id)
                    if saved_post_id:
                        log_message(f"Đã lưu post vào cấu trúc dữ liệu với ID: {saved_post_id}", logging.INFO)
                        if database_post_id:
                            log_message(f"Cấu trúc đã có database_post_id: {database_post_id}", logging.INFO)
                    else:
                        log_message("Không thể lưu post vào cấu trúc dữ liệu", logging.WARNING)
                except Exception as save_error:
                    log_message(f" Lỗi khi lưu post vào cấu trúc dữ liệu: {save_error}", logging.ERROR)
                
                # Gửi thông tin URL về cho bên A qua WebSocket
                try:
                    
                    # Tạo dữ liệu để gửi
                    url_data = {
                        "type": "URL_post",
                        "URL": post_url,
                        "authorName": get_facebook_name(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Thêm postId nếu có từ WebSocket
                    if post_id_from_websocket:
                        url_data["postId"] = post_id_from_websocket
                        log_message(f"Đã thêm postId vào dữ liệu gửi: {post_id_from_websocket}", logging.INFO)
                    
                    # Thêm thông tin user_id từ tài khoản hiện tại
                    user_ids = get_id_tosend_websocket()
                    url_data["to"] = user_ids
                    
                    log_message(f"Chuẩn bị gửi dữ liệu URL qua WebSocket: {url_data}", logging.INFO)
                    
                    # Gửi dữ liệu qua WebSocket
                    async def send_url_to_websocket():
                        try:
                            async with websockets.connect(WEBSOCKET_URL) as websocket:
                                # # Sử dụng lại clientId đã đăng ký từ connect_websocket()
                                # global current_client_id
                                # if current_client_id:
                                #     register_message = {
                                #         "type": "register",
                                #         "clientId": current_client_id
                                #     }
                                    
                                #     await websocket.send(json.dumps(register_message))
                                #     log_message(f"📝 Sử dụng lại clientId đã đăng ký: {current_client_id}", logging.INFO)
                                # else:
                                #     # Fallback nếu chưa có clientId
                                #     import time
                                #     current_client_id = f"clientB_{int(time.time() * 1000)}"
                                #     register_message = {
                                #         "type": "register",
                                #         "clientId": current_client_id
                                #     }
                                    
                                #     await websocket.send(json.dumps(register_message))
                                #     log_message(f"📝 Tạo clientId mới: {current_client_id}", logging.INFO)
                                
                                # # Đợi phản hồi đăng ký thành công (tùy chọn)
                                # await asyncio.sleep(0.5)
                                
                                # Gửi dữ liệu URL
                                await websocket.send(json.dumps(url_data))
                                log_message("Đã gửi thông tin URL thành công qua WebSocket!", logging.INFO)
                        except Exception as ws_error:
                            log_message(f" Lỗi khi gửi qua WebSocket: {ws_error}", logging.ERROR)
                    
                    # Chạy task gửi WebSocket
                    await send_url_to_websocket()
                    
                except Exception as send_error:
                    log_message(f" Lỗi khi chuẩn bị gửi dữ liệu URL: {send_error}", logging.ERROR)
                
                # Đóng popup sau khi lấy được link thành công
                try:
                    # Tìm nút đóng popup
                    close_buttons = browser.find_elements(By.CSS_SELECTOR, 'div[aria-label="Đóng"]')
                    if not close_buttons:
                        close_buttons = browser.find_elements(By.CSS_SELECTOR, 'div[aria-label="Close"]')
                    
                    if close_buttons:
                        close_button = close_buttons[0]
                        # Scroll nút đóng vào view
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
                        await asyncio.sleep(1)
                        
                        # Thử click nút đóng bằng nhiều cách
                        try:
                            close_button.click()
                            log_message("Đã đóng popup thành công (click thông thường)", logging.INFO)
                        except:
                            try:
                                browser.execute_script("arguments[0].click();", close_button)
                                log_message("Đã đóng popup thành công (JavaScript click)", logging.INFO)
                            except:
                                log_message(" Không thể click nút đóng popup", logging.WARNING)
                        
                        await asyncio.sleep(1)
                    else:
                        log_message(" Không tìm thấy nút đóng popup", logging.WARNING)
                        # Thử nhấn ESC để đóng popup
                        try:
                            browser.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                            log_message("Đã thử đóng popup bằng phím ESC", logging.INFO)
                        except:
                            pass
                            
                except Exception as close_error:
                    log_message(f" Lỗi khi đóng popup: {close_error}", logging.WARNING)
                    
            else:
                log_message("Không thể lấy được URL bài viết", logging.WARNING)
                current_url = browser.current_url
                log_message(f"📍 Current URL: {current_url}", logging.INFO)
            
        except Exception as e:
            log_message(f"Lỗi khi lấy thông tin bài viết: {e}", logging.ERROR)
            traceback.print_exc()
        
        # Xóa ảnh sau khi đăng thành công
        for image_path in downloaded_images:
            delete_image(image_path)
                
        await asyncio.sleep(random.uniform(2, 4))
    except Exception as err:
        log_message(f"err post new feed {err}", logging.ERROR)
        traceback.print_exc()
        
        # Xóa ảnh nếu có lỗi xảy ra
        if 'downloaded_images' in locals():
            for image_path in downloaded_images:
                delete_image(image_path)
        pass

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
        scroll_count = random.randint(20, 30)  # Số lần cuộn
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
                await comment_post(browser, actions)
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
            elif scroll_count % 17 == 0:
                await share_post(browser, actions)
                await asyncio.sleep(random.uniform(3, 5))
                # Kiểm tra flag sau khi share
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
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        # chrome_options.add_argument("--headless")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        screen_width = 1920
        screen_height = 1050
        chrome_options.add_argument(f"--window-position={screen_width // 2},0")
        chrome_options.add_argument(f"--window-size={screen_width // 2},{screen_height}")
        service = ChromeService(version_main=122)
        proxy_ip = account_data.get("proxy_ip")
        proxy_port = account_data.get("proxy_port")
        proxy_username = account_data.get("proxy_user")
        proxy_password = account_data.get("proxy_pass")
        if proxy_ip and proxy_port and proxy_username and proxy_password:
            log_message(f"Sử dụng proxy: {proxy_ip}:{proxy_port} với user {proxy_username}", logging.INFO)
            seleniumwire_options = {
                'proxy': {
                    'http': f'http://{proxy_username}:{proxy_password}@{proxy_ip}:{proxy_port}',
                    'https': f'https://{proxy_username}:{proxy_password}@{proxy_ip}:{proxy_port}',
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
            browser = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=seleniumwire_options)
        else:
            log_message("Không sử dụng proxy, tài khoản này sử dụng IP mặc định", logging.INFO)
            browser = webdriver.Chrome(service=service, options=chrome_options)
        browser.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)
        # Lấy IP hiển thị trên trình duyệt
        log_message("Đang lấy IP hiển thị trên trình duyệt...", logging.INFO)
        browser.get("https://ipv4.icanhazip.com/")
        page_content = browser.find_element(By.TAG_NAME, "pre").text
        displayed_ip = page_content.strip()
        print(f"IP hiển thị trên trình duyệt: {displayed_ip}")
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
                        await post_news_feed(browser)
                    elif pending_posts[0].get("type") == "comment":
                        log_message("Có yêu cầu bình luận từ WebSocket, dừng TẤT CẢ hoạt động và bình luận ngay lập tức", logging.INFO)
                        await comment_on_post_url(browser)
                    elif pending_posts[0].get("type") == "reply_comment":
                        log_message("Có yêu cầu trả lời bình luận từ WebSocket, dừng TẤT CẢ hoạt động và trả lời ngay lập tức", logging.INFO)
                        await reply_to_comment(browser)
                    elif pending_posts[0].get("type") == "reply_reply_comment":
                        log_message("Có yêu cầu trả lời reply comment từ WebSocket, dừng TẤT CẢ hoạt động và trả lời reply ngay lập tức", logging.INFO)
                        await reply_to_reply_comment(browser)
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
        await asyncio.sleep(15)  # Đảm bảo WebSocket có thời gian để dừng
        log_message("Chương trình đã kết thúc.", logging.INFO)

if __name__ == "__main__":
    # Lấy user_id_chat từ command line arguments
    delay = random.randint(30, 60)  # Delay ngẫu nhiên từ 30-60 giây
    print(f"[DELAY] Đợi {delay} giây trước khi khởi động toolfacebook.py...")
    time.sleep(delay)
    if len(sys.argv) > 1:
        client_user_id_chat = sys.argv[1]
        print(f"Starting tool with user_id_chat: {client_user_id_chat}")
    else:
        print("Usage: python toolfacebook.py <user_id_chat>")
        sys.exit(1)
    asyncio.run(main(client_user_id_chat))