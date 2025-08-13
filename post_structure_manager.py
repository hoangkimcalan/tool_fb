import os
import json
import logging
from datetime import datetime
from utils import log_message

POST_STRUCTURE_FILE = "post_structure.json"

def load_post_structure():
    try:
        if os.path.exists(POST_STRUCTURE_FILE):
            with open(POST_STRUCTURE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"posts": {}}
    except Exception as e:
        log_message(f"Lỗi khi load post structure: {e}", logging.ERROR)
        return {"posts": {}}

def load_user_accounts():
    try:
        if os.path.exists("user_accounts.json"):
            with open("user_accounts.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
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
    try:
        with open(POST_STRUCTURE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message("Đã lưu post structure thành công", logging.INFO)
    except Exception as e:
        log_message(f"Lỗi khi lưu post structure: {e}", logging.ERROR)

def add_post_to_structure(post_url, post_id=None, database_post_id=None):
    try:
        data = load_post_structure()
        if not post_id:
            import re
            post_id_match = re.search(r'posts/(\d+)', post_url)
            if post_id_match:
                post_id = post_id_match.group(1)
            else:
                post_id = post_url
        if post_id not in data["posts"]:
            data["posts"][post_id] = {
                "url": post_url,
                "post_id": post_id,
                "database_post_id": database_post_id,
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

def add_comment_to_structure(post_id, comment_fb_id=None, comment_content=""):
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
    try:
        data = load_post_structure()
        return data["posts"].get(post_id, None)
    except Exception as e:
        log_message(f"Lỗi khi lấy thông tin post structure: {e}", logging.ERROR)
        return None

def get_database_post_id(post_id):
    try:
        post_info = get_post_structure_info(post_id)
        if post_info and "database_post_id" in post_info:
            return post_info["database_post_id"]
        return None
    except Exception as e:
        log_message(f"Lỗi khi lấy database_post_id: {e}", logging.ERROR)
        return None

def get_commenter_name(post_id, comment_id, reply_id=None):
    try:
        data = load_post_structure()
        post_info = data["posts"].get(post_id, {})
        commenter_name = None
        if reply_id and "comments" in post_info:
            for comment_key, comment_data in post_info["comments"].items():
                if isinstance(comment_data, dict) and "replies" in comment_data:
                    for reply_key, reply_data in comment_data["replies"].items():
                        if isinstance(reply_data, dict) and reply_key == reply_id:
                            commenter_name = reply_data.get("commenter_name")
                            if commenter_name:
                                log_message(f"Tìm thấy commenter_name trong reply: {commenter_name}", logging.INFO)
                                return commenter_name
        if "comments" in post_info:
            for comment_key, comment_data in post_info["comments"].items():
                if isinstance(comment_data, dict) and comment_key == comment_id:
                    commenter_name = comment_data.get("commenter_name")
                    if commenter_name:
                        log_message(f"Tìm thấy commenter_name trong comment: {commenter_name}", logging.INFO)
                        return commenter_name
        if not commenter_name:
            user_accounts = load_user_accounts()
            for account_key, account_info in user_accounts.items():
                if isinstance(account_info, dict):
                    if "nameFb" in account_info and account_info["nameFb"]:
                        commenter_name = account_info["nameFb"]
                        log_message(f"Tìm thấy commenter_name trong user_accounts (nameFb): {commenter_name}", logging.INFO)
                        break
                    elif "note" in account_info and account_info["note"]:
                        commenter_name = account_info["note"]
                        log_message(f"Tìm thấy commenter_name trong user_accounts (note): {commenter_name}", logging.INFO)
                        break
                    elif "facebook_name" in account_info and account_info["facebook_name"]:
                        commenter_name = account_info["facebook_name"]
                        log_message(f"Tìm thấy commenter_name trong user_accounts (facebook_name): {commenter_name}", logging.INFO)
                        break
        if not commenter_name:
            log_message(f"Không tìm thấy commenter_name cho post_id={post_id}, comment_id={comment_id}, reply_id={reply_id}", logging.WARNING)
        return commenter_name
    except Exception as e:
        log_message(f"Lỗi khi lấy commenter name: {e}", logging.ERROR)
        return None
