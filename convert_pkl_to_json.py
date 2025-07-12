import pickle
import json
import os
import re

def convert_pkl_to_json(pkl_file, json_file):
    """
    Chuyển đổi file cookies.pkl thành fb_cookies.json
    """
    try:
        # Đọc file pickle
        with open(pkl_file, 'rb') as f:
            cookies_data = pickle.load(f)
        
        print(f"✅ Đã đọc file {pkl_file} thành công!")
        print(f"📊 Loại dữ liệu: {type(cookies_data)}")
        
        # Kiểm tra cấu trúc dữ liệu
        if isinstance(cookies_data, list):
            print(f"📋 Số lượng cookies: {len(cookies_data)}")
            cookies_list = cookies_data
        elif isinstance(cookies_data, dict):
            print(f"📋 Số lượng cookies: {len(cookies_data)}")
            cookies_list = list(cookies_data.values())
        else:
            print(f"❌ Không nhận diện được cấu trúc dữ liệu: {type(cookies_data)}")
            return None
        
        # Chuyển đổi thành format JSON chuẩn cho Selenium
        selenium_cookies = []
        
        for i, cookie in enumerate(cookies_list):
            if isinstance(cookie, dict):
                # Kiểm tra và chuyển đổi cookie
                selenium_cookie = {
                    "name": cookie.get("name", ""),
                    "value": cookie.get("value", ""),
                    "domain": cookie.get("domain", ".facebook.com"),
                    "path": cookie.get("path", "/"),
                    "secure": cookie.get("secure", True),
                    "httpOnly": cookie.get("httpOnly", False)
                }
                
                # Thêm expiry nếu có
                if "expiry" in cookie:
                    selenium_cookie["expiry"] = cookie["expiry"]
                
                selenium_cookies.append(selenium_cookie)
                
                # In thông tin cookie quan trọng
                if cookie.get("name") in ["c_user", "xs", "fr", "datr"]:
                    print(f"🔍 Cookie {cookie.get('name')}: {cookie.get('value', '')[:20]}...")
        
        # Lưu vào file JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(selenium_cookies, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Đã tạo file {json_file} với {len(selenium_cookies)} cookies")
        
        return selenium_cookies
        
    except Exception as e:
        print(f"❌ Lỗi khi chuyển đổi: {e}")
        return None

def extract_user_info_from_cookies(cookies):
    """
    Trích xuất thông tin user từ cookies
    """
    user_info = {}
    
    for cookie in cookies:
        if cookie.get("name") == "c_user":
            user_info["user_id"] = cookie.get("value", "")
        elif cookie.get("name") == "xs":
            user_info["xs_token"] = cookie.get("value", "")
        elif cookie.get("name") == "fr":
            user_info["fr_token"] = cookie.get("value", "")
        elif cookie.get("name") == "datr":
            user_info["datr_token"] = cookie.get("value", "")
    
    return user_info

def compare_with_previous_cookies():
    """
    So sánh với cookies trước đó
    """
    if os.path.exists("fb_cookies.json"):
        try:
            with open("fb_cookies.json", "r", encoding="utf-8") as f:
                old_cookies = json.load(f)
            
            print("\n🔄 So sánh với cookies hiện tại:")
            
            old_user_info = extract_user_info_from_cookies(old_cookies)
            print(f"📱 User ID cũ: {old_user_info.get('user_id', 'Không tìm thấy')}")
            print(f"🔑 XS Token cũ: {old_user_info.get('xs_token', 'Không tìm thấy')[:20]}...")
            
            return old_user_info
            
        except Exception as e:
            print(f"❌ Lỗi khi đọc cookies cũ: {e}")
    
    return None

def main():
    """
    Hàm chính để chuyển đổi và kiểm tra
    """
    print("🔄 Bắt đầu chuyển đổi cookies9.pkl...")
    
    # Chuyển đổi file
    new_cookies = convert_pkl_to_json("cookies9.pkl", "fb_cookies_new.json")
    
    if new_cookies:
        # Trích xuất thông tin user
        user_info = extract_user_info_from_cookies(new_cookies)
        
        print(f"\n👤 Thông tin tài khoản từ cookies mới:")
        print(f"   User ID: {user_info.get('user_id', 'Không tìm thấy')}")
        print(f"   XS Token: {user_info.get('xs_token', 'Không tìm thấy')[:30]}...")
        print(f"   FR Token: {user_info.get('fr_token', 'Không tìm thấy')[:30]}...")
        print(f"   DATR Token: {user_info.get('datr_token', 'Không tìm thấy')[:20]}...")
        
        # So sánh với cookies cũ
        old_user_info = compare_with_previous_cookies()
        
        if old_user_info:
            print(f"\n🔍 Kết quả so sánh:")
            if user_info.get('user_id') == old_user_info.get('user_id'):
                print("✅ Cùng một tài khoản Facebook!")
                print(f"   User ID: {user_info.get('user_id')}")
            else:
                print("❌ Khác tài khoản Facebook!")
                print(f"   User ID cũ: {old_user_info.get('user_id')}")
                print(f"   User ID mới: {user_info.get('user_id')}")
        
        # Tạo chuỗi Facebook format
        if user_info.get('user_id') and user_info.get('xs_token'):
            fb_string = f"{user_info.get('user_id')}|password|access_token|"
            fb_string += f"c_user={user_info.get('user_id')}; xs={user_info.get('xs_token')}; fr={user_info.get('fr_token', '')}; datr={user_info.get('datr_token', '')}"
            fb_string += "|app_secret|email"
            
            print(f"\n📝 Chuỗi Facebook format:")
            print(fb_string)
        
        # Hỏi người dùng có muốn thay thế cookies cũ không
        print(f"\n❓ Bạn có muốn thay thế file fb_cookies.json hiện tại không? (y/n): ", end="")
        choice = input().lower().strip()
        
        if choice == 'y' or choice == 'yes':
            # Backup file cũ
            if os.path.exists("fb_cookies.json"):
                os.rename("fb_cookies.json", "fb_cookies_backup.json")
                print("✅ Đã backup file cũ thành fb_cookies_backup.json")
            
            # Thay thế bằng file mới
            os.rename("fb_cookies_new.json", "fb_cookies.json")
            print("✅ Đã thay thế fb_cookies.json bằng cookies mới!")
        else:
            print("ℹ️ Giữ nguyên file fb_cookies.json hiện tại")
            print("📁 File mới được lưu tại: fb_cookies_new.json")
    
    else:
        print("❌ Không thể chuyển đổi file cookies!")

if __name__ == "__main__":
    main() 