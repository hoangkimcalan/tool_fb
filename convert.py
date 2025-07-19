import pickle
import json
import os
import time

def convert_pkl_to_json_cookies(pkl_filepath, json_filepath):
    """
    Chuyển đổi file .pkl chứa cookie thành file JSON theo định dạng mong muốn.

    Args:
        pkl_filepath (str): Đường dẫn đến file .pkl đầu vào.
        json_filepath (str): Đường dẫn đến file .json đầu ra.
    """
    if not os.path.exists(pkl_filepath):
        print(f"Lỗi: File .pkl không tồn tại tại đường dẫn: {pkl_filepath}")
        return

    try:
        with open(pkl_filepath, 'rb') as f:
            cookies = pickle.load(f)
    except pickle.UnpicklingError as e:
        print(f"Lỗi khi đọc file .pkl: {e}. Đảm bảo đây là file pickle hợp lệ.")
        return
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn khi đọc file .pkl: {e}")
        return

    json_cookies = []
    for cookie in cookies:
        # Tạo một bản sao để tránh sửa đổi cookie gốc và chỉ bao gồm các trường cần thiết
        new_cookie = {
            "domain": cookie.get("domain"),
            "httpOnly": cookie.get("httpOnly", False),
            "name": cookie.get("name"),
            "path": cookie.get("path", "/"),
            "secure": cookie.get("secure", False),
            "value": cookie.get("value")
        }
        
        # 'expiry' (thời gian hết hạn) thường là timestamp. 
        # Selenium có thể lưu là 'expiry' hoặc 'expirationDate'.
        # Nếu có, thêm vào, nếu không thì bỏ qua để tránh lỗi.
        if "expiry" in cookie and cookie["expiry"] is not None:
            new_cookie["expiry"] = int(cookie["expiry"])
        elif "expirationDate" in cookie and cookie["expirationDate"] is not None:
            new_cookie["expiry"] = int(cookie["expirationDate"])
        
        # 'sameSite' có thể không luôn có hoặc có giá trị khác nhau
        # Chuyển đổi 'unspecified' hoặc 'no_restriction' thành 'None' nếu đó là ý định của bạn.
        samesite_value = cookie.get("sameSite")
        if samesite_value is not None:
            if samesite_value in ["unspecified", "no_restriction"]:
                new_cookie["sameSite"] = "None"
            else:
                new_cookie["sameSite"] = samesite_value
        else:
            new_cookie["sameSite"] = "None" # Giá trị mặc định nếu không có

        json_cookies.append(new_cookie)

    try:
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_cookies, f, indent=4)
        print(f"Đã chuyển đổi thành công cookies từ '{pkl_filepath}' sang '{json_filepath}'")
    except Exception as e:
        print(f"Lỗi khi ghi file JSON: {e}")

# Ví dụ cách sử dụng hàm:
if __name__ == "__main__":
    # --- ĐỊNH NGHĨA DỮ LIỆU MẪU sample_cookies_data Ở ĐÂY ---
    # Đây là phần bạn thiếu trong mã của mình
    sample_cookies_data = [
        {
            "domain": ".facebook.com",
            "expirationDate": 1753501872.12345, # Có thể là 'expirationDate' hoặc 'expiry'
            "hostOnly": False,
            "httpOnly": True,
            "name": "checkpoint",
            "path": "/",
            "sameSite": "unspecified", # Ví dụ từ Selenium có thể là 'unspecified'
            "secure": True,
            "session": False,
            "storeId": "0",
            "value": "%7B%22u%22%3A61571092181408%2C%22t%22%3A1752897062%2C%22step%22%3A0%2C%22n%22%3A%22G5ZNxB2gCOY%3D%22%2C%22inst%22%3A122114851190703072%2C%22f%22%3A193593390684083%2C%22st%22%3A%22c%22%2C%22aid%22%3Anull%2C%22ca%22%3Anull%2C%22la%22%3A%22%22%2C%22ta%22%3A%221752897066.ch.s%3Apw.tDBEAiAgIUZoZu-I_Ypgzc4ivG4JgJtXadmCvolpHqaJJNuI9AIgKLF1PVYF-Z_pp8wpiLjrIA4tjzPRedPQVIJOgTf58xs%22%2C%22tfvaid%22%3Anull%2C%22tfvasec%22%3Anull%2C%22sat%22%3Anull%2C%22idg%22%3Afalse%2C%22cidue%22%3A%22%22%2C%22tfuln%22%3Anull%2C%22tfvri%22%3Anull%2C%22ct%22%3Anull%2C%22s%22%3A%22AWXtgKnWaRGbpamTG40%22%2C%22cs%22%3A%5B%5D%2C%22ssp%22%3A1%7D"
        },
        {
            "domain": ".facebook.com",
            "expiry": 1753501872, # Hoặc là 'expiry'
            "httpOnly": False,
            "name": "dpr",
            "path": "/",
            "sameSite": "no_restriction", # Một ví dụ khác cho sameSite
            "secure": True,
            "value": "2.25"
        },
        {
            "domain": ".facebook.com",
            "expiry": 1787457036,
            "httpOnly": True,
            "name": "sb",
            "path": "/",
            "sameSite": "Lax",
            "secure": True,
            "value": "CxZ7aLt0cglvdruYQCgWP87b"
        },
        {
            "domain": ".facebook.com",
            "expiry": 1760673036,
            "httpOnly": True,
            "name": "fr",
            "path": "/",
            "sameSite": "None", # Đã đúng định dạng None
            "secure": True,
            "value": "0MZSsXpSIIEToiO7c..BoexYL..AAA.0.0.BoexYL.AWevV6yckdrs-_6az6fg8abEdKU"
        }
    ]
    # --- KẾT THÚC ĐỊNH NGHĨA DỮ LIỆU MẪU ---

    # Ghi dữ liệu mẫu vào file .pkl
    sample_pkl_file = "cookies4.pkl"
    try:
        with open(sample_pkl_file, 'wb') as f:
            pickle.dump(sample_cookies_data, f)
        print(f"Đã tạo file .pkl mẫu: {sample_pkl_file}")
    except Exception as e:
        print(f"Lỗi khi tạo file .pkl mẫu: {e}")
        exit() # Thoát nếu không thể tạo file mẫu

    output_json_file = "fb_cookies.json"
    convert_pkl_to_json_cookies(sample_pkl_file, output_json_file)

    # Tùy chọn: Dọn dẹp file .pkl mẫu sau khi chuyển đổi
    # if os.path.exists(sample_pkl_file):
    #     os.remove(sample_pkl_file)
    #     print(f"Đã xóa file .pkl mẫu: {sample_pkl_file}")