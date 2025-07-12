import json
import re

def convert_facebook_string_to_cookies(fb_string):
    """
    Chuyển đổi chuỗi Facebook format: userID|password|access_token|cookies|app_secret|email
    thành file fb_cookies.json và trả về thông tin đăng nhập
    """
    # Tách chuỗi theo dấu |
    parts = fb_string.split('|')
    
    if len(parts) < 6:
        print("❌ Chuỗi Facebook không đúng format!")
        return None
    
    user_id = parts[0]
    password = parts[1] 
    access_token = parts[2]
    cookies_string = parts[3]
    app_secret = parts[4]
    email = parts[5]
    
    print(f"✅ Thông tin tài khoản:")
    print(f"   User ID: {user_id}")
    print(f"   Email: {email}")
    print(f"   Access Token: {access_token[:20]}...")
    
    # Chuyển đổi cookies string thành list dict
    cookies_list = []
    cookie_pairs = cookies_string.split('; ')
    
    for pair in cookie_pairs:
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookie_dict = {
                "name": name,
                "value": value,
                "domain": ".facebook.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            }
            cookies_list.append(cookie_dict)
    
    # Lưu vào file fb_cookies.json
    with open('fb_cookies.json', 'w', encoding='utf-8') as f:
        json.dump(cookies_list, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Đã tạo file fb_cookies.json với {len(cookies_list)} cookies")
    
    return {
        "user_id": user_id,
        "password": password,
        "email": email,
        "access_token": access_token,
        "app_secret": app_secret
    }

def update_toolfacebook_config(login_info):
    """
    Cập nhật thông tin đăng nhập trong toolfacebook.py
    """
    try:
        with open('toolfacebook.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Cập nhật username và password
        content = re.sub(
            r'user_name = "[^"]*"',
            f'user_name = "{login_info["email"]}"',
            content
        )
        
        content = re.sub(
            r'pass_word = "[^"]*"',
            f'pass_word = "{login_info["password"]}"',
            content
        )
        
        # Lưu lại file
        with open('toolfacebook.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Đã cập nhật thông tin đăng nhập trong toolfacebook.py")
        
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật file: {e}")

if __name__ == "__main__":
    # Chuỗi Facebook của bạn
    fb_string = "61571255043702|gghh29|VPL2NJGLLYPKAMMUIK6OFPV4PM64MTPE|c_user=61571255043702; xs=37:NEsh94tDdr4K1g:2:1741611901:-1:11399; fr=05FqrX1wjvwUn0DhA.AWV88C0QOAweL51cmOmDjPhdnb6moKfV573MGg.BnzuN9..AAA.0.0.BnzuN9.AWWQdXt5e6s; datr=xL3EZw_YrJP1XMFV9Rnt4ta6|EAAAAUaZA8jlABO33lpovFzzYpzjTQDqZA4Tdoo3IKBTuuABbuJODV1QqMyPcB6QPbsvfadl7kFPvZBFf7ZAqRCuptU3ODQ0CTpvHK1enVENpOuzmm0gdG3IWGGeEyfbzoJZCBbZAwioYybp3fCMcIebqNSuolS24CaGzUoVmZAFQ7HmB3OpwLs3zJZAoQwZCQ0d20WOXKuwrzxymXeOi8egZDZD|wlk42i75pc@qejjyl.com"
    
    print("🔄 Đang chuyển đổi thông tin Facebook...")
    
    # Chuyển đổi chuỗi thành cookies và thông tin đăng nhập
    login_info = convert_facebook_string_to_cookies(fb_string)
    
    if login_info:
        # Cập nhật thông tin trong toolfacebook.py
        update_toolfacebook_config(login_info)
        
        print("\n🎉 Hoàn thành! Bây giờ bạn có thể:")
        print("1. Chạy: python toolfacebook.py")
        print("2. Tool sẽ tự động đăng nhập với tài khoản này")
        print("3. Quan sát các thao tác tự động trong cửa sổ Chrome")
    else:
        print("❌ Không thể chuyển đổi thông tin Facebook!") 