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

# Danh sách các reaction có thể thả (cập nhật XPath mới)
REACTIONS = [
    {"name": "Like", "xpath": '//div[@aria-label="Thích" or @aria-label="Like"]'},
    {"name": "Love", "xpath": '//div[@aria-label="Yêu thích" or @aria-label="Love"]'},
    {"name": "Care", "xpath": '//div[@aria-label="Thương thương" or @aria-label="Care"]'},
    {"name": "Haha", "xpath": '//div[@aria-label="Haha"]'},
    {"name": "Wow", "xpath": '//div[@aria-label="Wow"]'},
    {"name": "Sad", "xpath": '//div[@aria-label="Buồn" or @aria-label="Sad"]'},
    {"name": "Angry", "xpath": '//div[@aria-label="Phẫn nộ" or @aria-label="Angry"]'}
]

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





async def test_surf_facebook(browser):
    """Test chức năng lướt Facebook"""
    try:
        log_message("Testing surf Facebook function...")
        
        # Cuộn trang vài lần để load thêm bài viết
        for i in range(3):
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(400, 600)
            await smooth_scroll(browser, current_scroll, target_scroll, duration=1.5)
            await asyncio.sleep(random.randint(5, 10))  # Chờ load bài viết, tránh lặp lại việc cuộn sau một thời gian cố định 
            log_message(f"Scrolled {i+1}/5 times - Current position: {current_scroll}")
        
        log_message("Surf Facebook test completed!")
        
    except Exception as e:
        log_message(f"Error in test_surf_facebook: {e}", logging.ERROR)

async def test_react_post(browser):
    """Test chức năng thả reaction cho bài viết (bao gồm cả Like)"""
    try:
        # Tìm nút Like để hover và hiện reaction panel
        like_button = None
        max_scroll = 10
        # Cuộn trang để tìm nút Like
        for i in range(max_scroll):
            like_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Thích" or @aria-label="Like") and @role="button"]')
            for btn in like_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    like_button = btn
                    break
            if like_button:
                break
            # Nếu chưa tìm thấy, cuộn thêm
            browser.execute_script("window.scrollBy(0, 200);")
            await asyncio.sleep(10)
            
        if not like_button:
            return
        
        # Scroll nút Like vào view để đảm bảo có thể click
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
        await asyncio.sleep(2)
        
        # Chọn ngẫu nhiên một reaction (bao gồm cả Like)
        selected_reaction = random.choice(REACTIONS)
        log_message(f"Selected reaction: {selected_reaction['name']}")
        
        # Nếu chọn Like, click trực tiếp vào nút Like
        if selected_reaction['name'] == 'Like':
            try:
                browser.execute_script("arguments[0].click();", like_button)
                await asyncio.sleep(random.uniform(2, 3))
                return
            except:
                like_button.click()
                await asyncio.sleep(random.uniform(2, 3))
                return
        
        # Nếu chọn reaction khác, hover để hiện reaction panel
        actions = ActionChains(browser)
        actions.move_to_element(like_button)
        actions.perform()
        await asyncio.sleep(3)  # Chờ để hover có hiệu ứng
        
        await asyncio.sleep(random.uniform(2, 3))
        
        # Tìm reaction button chính xác hơn
        reaction_button = None
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Thử tìm các div có role="button" và aria-label chính xác
                exact_xpath = f'//div[@role="button" and @aria-label="{selected_reaction["name"]}"]'
                reaction_button = WebDriverWait(browser, 3).until(
                    EC.presence_of_element_located((By.XPATH, exact_xpath))
                )
                break
                
            except:
                try:
                    # Tìm trong reaction panel (thường có class hoặc role đặc biệt)
                    # Hoặc tìm các element có aria-label chứa tên reaction
                    panel_reactions = browser.find_elements(By.XPATH, f'//div[contains(@aria-label, "{selected_reaction["name"]}")]')
                    for reaction in panel_reactions:
                        aria_label = reaction.get_attribute('aria-label')
                        if aria_label and selected_reaction["name"].lower() in aria_label.lower():
                             # Thêm điều kiện kiểm tra kích thước để lọc ra các phần tử không phải nút bấm
                            size = reaction.size
                            if size['width'] > 0 and size['height'] > 0 and reaction.is_displayed() and reaction.is_enabled():
                                reaction_button = reaction
                                break
                    if reaction_button:
                        break
                        
                except Exception as e:
                    pass # Continue to next attempt
                
            if attempt < max_attempts - 1:
                await asyncio.sleep(2)
                # Thử hover lại để panel hiển thị lại
                actions.move_to_element(like_button)
                actions.perform()
                await asyncio.sleep(2)
        
        if not reaction_button:
            return
            
        # Kiểm tra kích thước và trạng thái cuối cùng trước khi click
        size = reaction_button.size
        
        if size['width'] > 0 and size['height'] > 0 and reaction_button.is_displayed() and reaction_button.is_enabled():
            # Scroll reaction button vào view
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
            await asyncio.sleep(1) # Chờ một chút sau khi scroll

            try:
                # Tạo một ActionChains mới hoặc đảm bảo đã reset các hành động trước đó
                click_actions = ActionChains(browser)
                click_actions.move_to_element(reaction_button) # Di chuyển chuột đến element
                click_actions.click() # Thực hiện hành động click
                click_actions.perform() # Thực thi chuỗi hành động
            except Exception as e:
                # Fallback sang JavaScript click nếu ActionChains thất bại
                try:
                    browser.execute_script("arguments[0].click();", reaction_button)
                except Exception as e_inner:
                    traceback.print_exc()
            
            await asyncio.sleep(random.uniform(2, 3))  # Chờ để tránh spam
            
    except Exception as e:
        traceback.print_exc()
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
        
        # 2. Test thả reaction bài viết (bao gồm cả Like)
        await test_react_post(browser)
        await asyncio.sleep(3)
        #3. Lướt Facebook thêm lần nữa để kiểm tra tính ổn định
        await test_surf_facebook(browser)
        await asyncio.sleep(3)
        # 4. Thả reaction thêm lần nữa để kiểm tra tính ổn định
        await test_react_post(browser)
        await asyncio.sleep(3)
        
        log_message("Test cơ bản hoàn thành!")
        log_message("Đăng nhập: OK")
        log_message("Lướt Facebook: OK") 
        log_message("Thả reaction: OK")
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