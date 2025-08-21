import requests
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import time
import re
import random
import pyperclip

API_URL = "http://123.24.206.25:5000/"
# Gọi API cho tool facebook
def call_api(endpoint, payload, type="data", files=None):
    url = API_URL + endpoint
    headers = {
        'X-API-Key': '123456ABCDEF'
    }
    if type == "data":
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
    elif type == "json":
        response = requests.request("POST", url, headers=headers, json=payload, files=files)
    return response

def get_commands(user_id):
    commands = call_api("get_commands", {"user_id": user_id}).json().get('data', [])
    return commands


# Đóng hộp thoại trả lời câu hỏi
def close_dialog(driver):
    try:
        # Ấn nút "Đóng" nếu có
        close_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Đóng' and @role='button']"))
        )
        close_btn.click()
    except:
        pass

    try:
        # Ấn nút "Thoát" nếu có
        exit_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Thoát' and @role='button']"))
        )
        exit_btn.click()
    except:
        pass

# Lấy câu trả lời tham gia nhóm kín, nếu câu trả lời chưa có, sẽ cào câu hỏi gửi về server
def get_answer(driver, group_link):
    need_answer = False
    answer_question_dialog = driver.find_element(
        By.XPATH,
        "//div[@class='x1n2onr6 x1ja2u2z x1afcbsf x78zum5 xdt5ytf x1a2a7pz x6ikm8r x10wlt62 x71s49j x1jx94hy xw5cjc7 x1dmpuos x1vsv7so xau1kf4 x104qc98 x15o3w11 xogydr4 x1vmz7ll x1yyrj1m x1n7qst7 xh8yej3']"
    )
    questions = answer_question_dialog.find_elements(By.XPATH, ".//span[@class='x1lliihq x6ikm8r x10wlt62 x1n2onr6 x1j85h84']")
    for question in questions:
        grandparent = question.find_element(By.XPATH, "./../../../../../..")
        answers = grandparent.find_elements(By.XPATH, ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x6prxxf xvq8zen x1s688f xzsf02u']")
        how_to_answer = grandparent.find_element(By.XPATH, ".//span[@class='x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1nxh6w3 x1sibtaa xo1l8bm xi81zsa']")
        how_to_answer = how_to_answer.text if how_to_answer.text.strip() else 'Trả lời câu hỏi'
        answer = call_api("get_answer", {
            "group_link": group_link,
            "question": question.text,
            "how_to_answer": how_to_answer,
            "answers[]": [answer.text for answer in answers]
        })
        if answer.status_code == 200:
            answer = answer.json().get("answer", "")
            time.sleep(1)
            if answer:
                if how_to_answer == "Trả lời câu hỏi":
                    answer_input = grandparent.find_element(By.XPATH, ".//textarea")
                    answer_input.click()
                    answer_input.send_keys(answer)
                if "nhiều" in how_to_answer:
                    for checktext in answer.split("|"):
                        checkbox = grandparent.find_element(
                            By.XPATH,
                            f"//label[.//span[text()='{checktext}']]//input[@type='checkbox']"
                        )
                        checkbox.click()
                if "1" in how_to_answer:
                    radio = grandparent.find_element(
                        By.XPATH,
                        f"//input[@type='radio' and @value='{answer}']"
                    )
                    radio.click()
            time.sleep(1)
        else:
            need_answer = True
    if need_answer:
        close_dialog(driver)
    else:
        answer_question_dialog.find_element(
            By.XPATH,
            "//div[@aria-label='Gửi' and @role='button']"
        ).click()

# Đếm số lượng bình luận trong một bài viết
def parse_comment_count(driver, post):
    try:
        element = post.find_element(By.XPATH, ".//span[contains(text(), 'bình luận')]")
    except:
        if len(post.find_elements(By.XPATH, ".//span[text()='Bình luận']")) > 0:
            driver.execute_script("""
                arguments[0].scrollIntoView({ behavior: "smooth", block: "start" });
            """, post)
            return 0
        return -1
    text = element.get_attribute("innerText").strip()
    if len(text) > 15:
        return -1
    driver.execute_script("""
        arguments[0].scrollIntoView({ behavior: "smooth", block: "start" });
    """, post)
    match = re.search(r"([\d,.]+)\s*([KM]?)", text)
    if not match:
        return -1
    number_str = match.group(1).replace(",", ".")
    if "K" in match.group(2):
        return int(float(number_str) * 1000)
    if "M" in match.group(2):
        return int(float(number_str) * 1000000)
    return int(float(number_str))

def extract_post_content(raw_text):
    lines = raw_text.split('\n')
    # Gộp các dòng sau khi loại bỏ khoảng trắng
    cleaned = [line.strip() for line in lines if line.strip()]
    if len(cleaned) < 10:
        return ""
    # Bắt đầu từ vị trí có chuỗi nhiễu (nhiều dòng ngắn liên tiếp)
    start_index = 0
    short_streak = 0
    for i, line in enumerate(cleaned):
        if len(line) <= 2:
            short_streak += 1
        else:
            if short_streak >= 10:
                start_index = i
            short_streak = 0
    # Sau đoạn nhiễu, tìm dòng đầu tiên đủ dài
    content = ""
    for line in cleaned[start_index:]:
        if line == "Tất cả cảm xúc:":
            break
        elif line.endswith("bình luận") or line.endswith("lượt chia sẻ"):
            break
        elif line == "Thích" or line == "Bình luận" or line == "Chia sẻ" or line == "Gửi":
            break
        else:  
            content += line + "\n"
    if "FacebookFacebook" in content:
        content = ""
    return content.strip()

# Lấy các bài viết chưa được phê duyệt
def get_unapproved_posts(user_id):
    response = call_api("get_unapproved_posts", {'user_id': user_id})
    if response.status_code == 200:
        return response.json()
    return None

# Lấy đường dẫn bài viết
def extract_post_link(driver, post, timeout=10):
    try:
        # Chờ nút chia sẻ trong post
        share_button = WebDriverWait(post, timeout).until(
            EC.element_to_be_clickable((By.XPATH, ".//span[@data-ad-rendering-role='share_button']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", share_button)

        # Chờ nút "Sao chép liên kết"
        copy_link_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Sao chép liên kết']/ancestor::div[@role='button']"))
        )
        copy_link_button.click()

        # Trích dữ liệu từ clipboard
        return pyperclip.paste()
    except Exception as e:
        pass

    return driver.current_url

# Kiểm tra trạng thái của bài viết
def check_post(driver, post_ids, group_link, post_contents, fb_id):
    driver.get("https://www.facebook.com/" + group_link + "/user/" + fb_id)
    y = 0
    start_time = time.time()
    max_duration = len(post_ids) * 3
    while time.time() - start_time < max_duration:
        y += 1000
        driver.execute_script(f"window.scrollTo(0, {y});")
        time.sleep(random.uniform(0, 1))
        posts = driver.find_elements(By.CSS_SELECTOR, 'div[class="html-div xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x78zum5 x1n2onr6 xh8yej3"]')
        for i in range(len(posts)):
            post = posts[i]
            try:
                comment_count = parse_comment_count(driver, post)
                if comment_count < 0:
                    continue
                content = extract_post_content(post.get_attribute("innerText").strip())
                if content == "":
                    continue
                if "Xem thêm" in content:
                    see_more = post.find_element(By.XPATH, ".//div[text()='Xem thêm']")
                    if see_more.is_displayed():
                        see_more.click()
                        time.sleep(1)
                        content = extract_post_content(post.get_attribute("innerText").strip())
                    else:
                        continue
                if content in post_contents:
                    index = post_contents.index(content)
                    call_api("update_post_status", {'post_id': post_ids[index], 'status': 'Đã đăng thành công'})
                    call_api("update_post_link", {'post_id': post_ids[index], 'link': extract_post_link(driver, post)})
                    post_contents.remove(content)
                    post_ids.remove(post_ids[index])
                    if (len(post_contents) == 0):
                        break
            except NoSuchElementException:
                continue
            except Exception as e:
                continue