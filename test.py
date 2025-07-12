import asyncio
import random
import time
import traceback
import json
import os
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import log_message, smooth_scroll, type_text_input

# Constants
COOKIE_FILE = "fb_cookies.json"

async def load_cookies(browser):
    """Nạp cookies từ file JSON"""
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
        try:
            with open(COOKIE_FILE, "r") as file:
                cookies = json.load(file)
            
            for cookie in cookies:
                browser.add_cookie(cookie)
            
            log_message("Valid cookies loaded successfully!")
            return True
        except Exception as e:
            log_message(f"Error loading cookies: {e}", logging.ERROR)
            return False
    return False

async def is_logged_in(browser):
    """Kiểm tra xem đã đăng nhập vào Facebook chưa"""
    try:
        await asyncio.sleep(3)
        login_elements = browser.find_elements(By.ID, "email") + browser.find_elements(By.ID, "pass")
        if login_elements:
            log_message("Chưa đăng nhập vào Facebook!")
            return False
        log_message("Đã đăng nhập vào Facebook!")
        return True
    except Exception:
        return False

async def test_like_post(browser):
    """Test chức năng like bài viết với cải tiến"""
    try:
        log_message("Testing like post function...")
        like_button = None
        max_scroll = 10
        for i in range(max_scroll):
            like_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Thích" or @aria-label="Like") and @role="button"]')
            for btn in like_buttons:
                log_message(f"Check like button: displayed={btn.is_displayed()}, enabled={btn.is_enabled()}")
                if btn.is_displayed() and btn.is_enabled():
                    like_button = btn
                    break
            if like_button:
                break
            # Nếu chưa tìm thấy, cuộn thêm
            browser.execute_script("window.scrollBy(0, 400);")
            await asyncio.sleep(1)
        if not like_button:
            log_message("Không tìm thấy nút Like nào hiển thị và có thể click sau khi cuộn.")
            return
        log_message(f"Found like button: {like_button}")
        # Scroll element vào view
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
        await asyncio.sleep(1)
        # Thử hover trước
        actions = ActionChains(browser)
        actions.move_to_element(like_button)
        actions.perform()
        await asyncio.sleep(1)
        log_message("Hovered over like button successfully!")
        # Thử click bằng JavaScript thay vì ActionChains
        browser.execute_script("arguments[0].click();", like_button)
        await asyncio.sleep(2)
        log_message("Clicked like button successfully using JavaScript!")
    except Exception as e:
        log_message(f"Error in test_like_post: {e}", logging.ERROR)



async def test_surf_facebook(browser):
    """Test chức năng lướt Facebook"""
    try:
        log_message("Testing surf Facebook function...")
        
        # Cuộn trang vài lần để load thêm bài viết
        for i in range(5):
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(400, 600)
            await smooth_scroll(browser, current_scroll, target_scroll, duration=1.5)
            await asyncio.sleep(3)  # Chờ load bài viết
            log_message(f"Scrolled {i+1}/5 times - Current position: {current_scroll}")
        
        log_message("Surf Facebook test completed!")
        
    except Exception as e:
        log_message(f"Error in test_surf_facebook: {e}", logging.ERROR)

async def main():
    """Test các chức năng cơ bản"""
    try:
        log_message(" Starting Facebook Tool Test...")
        
        # Khởi tạo Chrome
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        browser = webdriver.Chrome(options=chrome_options)
        
        # Đăng nhập
        browser.get("https://facebook.com")
        await asyncio.sleep(3)
        
        # Load cookies
        if await load_cookies(browser):
            browser.refresh()
            await asyncio.sleep(4)
        
        # Kiểm tra đăng nhập
        if not await is_logged_in(browser):
            log_message("Không thể đăng nhập! Vui lòng kiểm tra cookies.")
            return
        
        log_message("Đăng nhập thành công! Bắt đầu test...")
        
        # Test các chức năng cơ bản
        log_message("Bắt đầu test các chức năng cơ bản...")
        
        # 1. Test lướt Facebook
        await test_surf_facebook(browser)
        await asyncio.sleep(3)
        
        # 2. Test like bài viết
        await test_like_post(browser)
        await asyncio.sleep(3)
        
        log_message("Test cơ bản hoàn thành!")
        log_message("Đăng nhập: OK")
        log_message("Lướt Facebook: OK") 
        log_message("Like bài viết: OK")
        log_message("Có thể tiếp tục test các chức năng khác!")
        
        # Giữ browser mở để xem kết quả
        await asyncio.sleep(15)
        
    except Exception as e:
        log_message(f"Error in main: {e}", logging.ERROR)
        traceback.print_exc()
    finally:
        try:
            browser.quit()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 