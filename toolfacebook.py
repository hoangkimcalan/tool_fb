import asyncio
import random
import time
import traceback
import json
import os
import logging

import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from utils import hide_process, initialize, log_message, run_as_trusted, smooth_scroll, type_text_input

# Constants
COOKIE_FILE = "fb_cookies.json"
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

async def save_cookies(browser):
    """Lưu cookies vào file JSON"""
    cookies = browser.get_cookies()
    if cookies:
        with open(COOKIE_FILE, "w") as file:
            json.dump(cookies, file)
        log_message("Cookies saved successfully!")
    else:
        log_message("No cookies to save.", logging.ERROR)

async def load_cookies(browser):
    """Nạp cookies từ file JSON"""
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
        try:
            with open(COOKIE_FILE, "r") as file:
                cookies = json.load(file)
                for cookie in cookies:
                    browser.add_cookie(cookie)
            log_message("Cookies loaded successfully!")
        except json.JSONDecodeError:
            log_message("Corrupted cookie file. Deleting...", logging.ERROR)
            os.remove(COOKIE_FILE)

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
    except Exception as e:
        log_message(f"Login failed: {e}",logging.ERROR)

async def like_post(browser, actions):
    '''Like, Yêu thích, Thương thương, Haha, Wow, Buồn, Phẫn nộ'''
    try:
        like_button = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.XPATH, "//span[@data-ad-rendering-role='like_button'] | //span[@data-ad-rendering-role='thích_button']")))

        log_message(f"like_button: {like_button}")
        
        actions.move_to_element(like_button)
        actions.perform()
        
        await asyncio.sleep(random.uniform(1, 3))
        
        selected_reaction = random.choice(REACTIONS)
        log_message(f"selected_reaction: {selected_reaction}")
        
        await asyncio.sleep(random.uniform(2, 3))
        #**Tìm và kiểm tra kích thước Reaction**
        try:
            reaction_button = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.XPATH, selected_reaction["xpath"])))
            # Kiểm tra kích thước trước khi click
            size = reaction_button.size
            if size['width'] > 0 and size['height'] > 0:
                reaction_button.click()
                log_message(f"Đã react: {selected_reaction['name']}")
                
                await asyncio.sleep(random.uniform(2, 3))  # Chờ để tránh spam
            else:
                log_message(f" Reaction `{selected_reaction['name']}` không thể click (không có kích thước).")
        except:
            log_message(f" Không tìm thấy reaction: {selected_reaction['name']}", logging.ERROR)
    except Exception as e:
        log_message(f" Lỗi khi like bài viết: {e}", logging.ERROR)
        traceback.print_exc()
        pass

async def comment_post(browser, actions):
    try:
        wait = WebDriverWait(browser, 5)
        try:
            comment = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Viết bình luận"] | //div[@aria-label="Leave a comment"]')))
        except:
            log_message("Vao day loi khi find comment de post", logging.ERROR)
            comment = browser.find_element(By.XPATH, '//div[@aria-label="Leave a comment"]')
        log_message(f"comment tim thay: {comment}")
        
        actions.move_to_element(comment)
        actions.click()
        actions.perform()
        
        # Chọn ngẫu nhiên một bình luận
        comment_text = random.choice(COMMENTS)
        await asyncio.sleep(random.uniform(2, 4))
        log_message(f" Đang nhập bình luận: {comment_text}")
        
        comment_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
        await asyncio.sleep(1)
        p_tag = comment_box.find_element(By.TAG_NAME, "p")
        
        log_message(f" p_tag: {p_tag}")
        await asyncio.sleep(2)
        actions.send_keys_to_element(p_tag, comment_text)
        
        await asyncio.sleep(random.uniform(2, 4))
        actions.send_keys(Keys.ENTER)
        actions.perform()
        
        log_message(" Bình luận đã được gửi thành công!")
        
        await asyncio.sleep(2)
        actions.send_keys(Keys.ESCAPE).perform()
        
    except Exception as e:
        log_message(f" Lỗi khi comment: {e}", logging.ERROR)
        traceback.print_exc()
        pass
    await asyncio.sleep(4)
    
async def share_post( browser,actions):
    try:
        share_button = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn.'] | //div[@aria-label='Send this to friends or post it on your profile.']")))
        log_message(f" Tìm thấy nút share: {share_button}")
        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", share_button)
        
        await asyncio.sleep(2)
        
        actions.move_to_element(share_button)
        actions.click()
        actions.perform()
        
        await asyncio.sleep(5)
        
        share = browser.find_element(By.XPATH, "//div[@aria-label='Chia sẻ ngay'] | //div[@aria-label='Share now']")
        log_message(f" Tìm thấy nút chia sẻ: {share}")
        
        actions.move_to_element(share)
        actions.click()
        actions.perform()
        
        log_message(f"Đã chia sẻ bài viết thành công")
    except Exception as err:
        log_message(f"err share {err}", logging.ERROR)
        
async def watch_videos(browser, actions):
    try:
        browser.get("https://www.facebook.com/watch/")
        await asyncio.sleep(random.uniform(3, 6))
        wait = WebDriverWait(browser, 10)
        video_selected = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='x1ey2m1c x9f619 xds687c x17qophe x10l6tqk x13vifvy x1ypdohk']")
        ))
        log_message(f" Tìm thấy khung video: {video_selected}")
        await asyncio.sleep(random.uniform(2, 4))
        
        actions.move_to_element(video_selected)
        actions.click()
        actions.perform()
        
        scroll_count_video = random.randint(6, 15)  # Số lần cuộn
        
        while scroll_count_video > 0:
            log_message(f"scrool_count)watch_video {scroll_count_video}")
            # Cuộn từ từ (Mô phỏng cuộn chậm dần đều)
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 800)

            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))
            #thoi gian dung lai de xem video
            await asyncio.sleep(random.uniform(40, 70))
            scroll_count_video = scroll_count_video - 1
        
    except Exception as err:
        log_message(f"err watch videos {err}", logging.ERROR)
    

        

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
        time.sleep(random.uniform(5, 8))
        scroll_count = random.randint(6, 15)  # Số lần cuộn
        actions = ActionChains(browser)
        
        while scroll_count > 0:
            log_message(f"scrool_count {scroll_count}")
            # Cuộn từ từ (Mô phỏng cuộn chậm dần đều)
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 1000)

            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))
            #thoi gian dung lai de doc tin nhan
            await asyncio.sleep(random.uniform(4, 6))

            if scroll_count % 13 == 0:
                await comment_post(browser, actions)
                await asyncio.sleep(random.uniform(3, 5))
            elif scroll_count % 7 == 0:
                await like_post(browser, actions)
                await asyncio.sleep(random.uniform(3, 5))

            scroll_count = scroll_count - 1

        await asyncio.sleep(random.uniform(2, 5))
        log_message("Đã hoàn thành lướt Facebook")

        try:
            await watch_videos(browser, actions)
        except:
            pass

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

# **Hàm main() để chạy chương trình**
async def main():
    try:
        await initialize()
        chrome_options = Options()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")

        # chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        screen_width = 1920  # Adjust this value based on your screen resolution
        screen_height = 1080  # Adjust this value based on your screen resolution
        chrome_options.add_argument(f"--window-position={screen_width // 2},0")
        chrome_options.add_argument(f"--window-size={screen_width // 2},{screen_height}")
        service = webdriver.ChromeService(version_main=122)
        browser = webdriver.Chrome(service=service, options=chrome_options)
        # dang nhap tren fb
        browser.get("https://facebook.com")
        await asyncio.sleep(3)

        browser.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)

        user_name = "0334388048"
        pass_word = "239210"
        code_2fa = ""
        id_chat = "10502329"
        
        if os.path.exists(COOKIE_FILE):
            await load_cookies(browser)
            browser.refresh()  # Refresh lại trang để áp dụng cookies
            await asyncio.sleep(4)

        # Kiểm tra nếu vẫn cần đăng nhập
        if not await is_logged_in(browser):
            log_message("Cookies không hợp lệ hoặc hết hạn, cần đăng nhập lại.")
            await login(user_name, pass_word, code_2fa, browser)
            
        await asyncio.sleep(3)

        page_source = browser.page_source
        if '"userID":' in page_source:
            start = page_source.find('"userID":') + len('"userID":')
            end = page_source.find(',', start)
            id_fb = page_source[start:end]
            log_message(f'id_fb: {id_fb}')

        while True:
            try:
                await surf_facebook("10502329", random.choice(COMMENTS), browser)
                await asyncio.sleep(random.uniform(2400, 3600))
            except Exception as err:
                log_message(f'err:{err}', logging.ERROR)
                traceback.print_exc()
                continue

    except Exception as err:
        log_message(f'err in main:{err}', logging.ERROR)


if __name__ == "__main__":
    asyncio.run(main())
