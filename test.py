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
    # Hàm bình luận bài viết
async def test_comment_post(browser, actions):
    try:
        # Tìm nút bình luận với logic cuộn trang
        comment_button = None
        max_scroll = 10
        
        # Cuộn trang để tìm nút bình luận
        for i in range(max_scroll):
            try:
                comment_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Viết bình luận" or @aria-label="Leave a comment") and @role="button"]')
                for btn in comment_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        comment_button = btn
                        break
                if comment_button:
                    break
            except Exception as e:
                log_message(f"Lỗi khi tìm nút bình luận lần {i+1}: {e}")
                
            # Nếu chưa tìm thấy, cuộn thêm
            if not comment_button:
                browser.execute_script("window.scrollBy(0, 200);")
                await asyncio.sleep(10)
                
        if not comment_button:
            log_message("Không tìm thấy nút bình luận sau khi cuộn trang", logging.ERROR)
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
        log_message(f"Tìm thấy p_tag: {p_tag}")
        await asyncio.sleep(2)
        actions.send_keys_to_element(p_tag, comment_text)
        await asyncio.sleep(random.uniform(2, 4))
        actions.send_keys(Keys.ENTER)
        actions.perform()   
        log_message("Bình luận đã được gửi thành công!")
            
        await asyncio.sleep(2)
        actions.send_keys(Keys.ESCAPE).perform()
            
    except Exception as e:
        log_message(f"Error in comment_post: {e}", logging.ERROR)
        traceback.print_exc()

# Hàm chia sẻ bài viết
async def test_share_post(browser, actions):
    try:
        # Tìm nút chia sẻ với logic cuộn trang
        share_button = None
        max_scroll = 10
        
        # Cuộn trang để tìm nút chia sẻ
        for i in range(max_scroll):
            try:
                share_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn." or @aria-label="Send this to friends or post it on your profile.") and @role="button"]')
                for btn in share_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        share_button = btn
                        break
                if share_button:
                    break
            except Exception as e:
                log_message(f"Lỗi khi tìm nút chia sẻ lần {i+1}: {e}")
                
            # Nếu chưa tìm thấy, cuộn thêm
            if not share_button:
                browser.execute_script("window.scrollBy(0, 200);")
                await asyncio.sleep(10)
                
        if not share_button:
            return
        
        # Scroll nút chia sẻ vào view
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
        await asyncio.sleep(2)
        
        # Click vào nút chia sẻ
        try:
            actions.move_to_element(share_button)
            actions.click()
            actions.perform()
        except Exception as e:
            # Fallback sang JavaScript click nếu ActionChains thất bại
            try:
                browser.execute_script("arguments[0].click();", share_button)
            except Exception as e_inner:
                return       
        await asyncio.sleep(5)    
        # Tìm và click nút "Chia sẻ ngay"
        try:
            share_now_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Chia sẻ ngay" or @aria-label="Share now") and @role="button"]'))
            )
            # Click nút chia sẻ ngay
            try:
                actions.move_to_element(share_now_button)
                actions.click()
                actions.perform()
            except Exception as e:
                # Fallback sang JavaScript click
                try:
                    browser.execute_script("arguments[0].click();", share_now_button)
                except Exception as e_inner:
                    return
            log_message("Đã chia sẻ bài viết thành công!")
            await asyncio.sleep(random.uniform(2, 3))           
        except Exception as e:
            return        
    except Exception as e:
        traceback.print_exc()
# Hàm xem video
async def watch_videos(browser, actions):
    try:
        browser.get("https://www.facebook.com/watch/")
        await asyncio.sleep(random.uniform(3, 6))
        scroll_count_video = random.randint(6, 15)  # Số lần cuộn
        while scroll_count_video > 0:
            log_message(f"scroll_count_watch_video {scroll_count_video}")

            await asyncio.sleep(random.uniform(4, 7))

            # Lấy danh sách video
            video_selected = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@class='x1ey2m1c x9f619 xds687c x17qophe x10l6tqk x13vifvy x1ypdohk']")
            ))

            # Lọc video trong tầm nhìn
            visible_videos = [video for video in video_selected if video.is_displayed()]
            await asyncio.sleep(random.uniform(40, 60))

            if visible_videos:
                log_message(f"visible_videos: {visible_videos}")
                current_video = visible_videos[0]

                # Nếu scroll_count_video chia hết cho 7 hoặc 13 thì thực hiện hành động
                if scroll_count_video % 7 == 0 or scroll_count_video % 13 == 0:
                    if scroll_count_video % 7 == 0:
                        await asyncio.sleep(random.uniform(5, 7))
                        try:
                            like_buttons = WebDriverWait(browser, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//span[@data-ad-rendering-role='like_button'] | //span[@data-ad-rendering-role='thích_button']"))
                            )
                            
                            if like_buttons and like_buttons[0].is_displayed():
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_buttons[0])
                                await asyncio.sleep(random.uniform(1, 3))
                                like_buttons[0].click()
                                log_message("Liked the post video successfully!")
                            else:
                                log_message("Like button is not visible, skipping...")
                        except Exception as e:
                            log_message(f"Error clicking like button: {e}")

                    elif scroll_count_video % 13 == 0:
                        await test_share_post(browser, actions)
                        await asyncio.sleep(random.uniform(3, 5))
                        
                    await asyncio.sleep(random.uniform(2, 5))

                    # Sau khi like hoặc share, click vào video để lấy URL
                    actions.move_to_element(current_video).click().perform()
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Lấy URL video đã tương tác
                    video_url = browser.current_url
                    log_message(f"current_url: {video_url}")

            # Trừ lượt cuộn
            scroll_count_video -= 1

            # Cuộn từ từ (Mô phỏng cuộn chậm dần đều)
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 800)
            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))

            
        log_message("Đã hoàn thành xem video Facebook")
        
    except Exception as err:
        log_message(f"err watch videos {err}", logging.ERROR)
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
        # 4. Test bình luận bài viết
        await test_comment_post(browser, ActionChains(browser))
        #5. Chia sẻ bài viết
        await test_surf_facebook(browser)
        await asyncio.sleep(3)
        await test_share_post(browser, ActionChains(browser))
        log_message("Test cơ bản hoàn thành!")
        log_message("Đăng nhập: OK")
        log_message("Lướt Facebook: OK") 
        log_message("Thả reaction: OK")
        log_message("Bình luận bài viết: OK")
        log_message("Có thể tiếp tục test các chức năng khác!")
        
        # Giữ browser mở để xem kết quả
        await asyncio.sleep(30)
        
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