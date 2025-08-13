import asyncio
import json
import time
import traceback
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from api import create_post, create_comment, create_reply_comment
from utils import log_message
import aiohttp
import aiofiles
import os
import logging
import re
import random
import websockets
import pandas as pd
from datetime import datetime
from post_structure_manager import *
from selenium.common.exceptions import TimeoutException


# WEBSOCKET_URL = "ws://123.24.206.25:4000"
WEBSOCKET_URL = "ws://localhost:4000"

# Hàm xóa ảnh
def delete_image(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            log_message(f"Đã xóa ảnh: {file_path}", logging.INFO)
        else:
            log_message(f"File không tồn tại để xóa: {file_path}", logging.WARNING)
    except Exception as e:
        log_message(f"Lỗi khi xóa ảnh {file_path}: {e}", logging.ERROR)

# Hàm bình luận vào bài viết theo URL cụ thể
async def comment_on_post_url(browser, pending_posts, get_facebook_name, get_websocket_role, get_id_tosend_websocket):
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
                                    commenter_name = get_facebook_name  # Fallback về tên Facebook hiện tại
                                
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
                                    "facebookId": get_websocket_role,
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
                        "authorName": get_facebook_name,
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
                    user_ids = get_id_tosend_websocket
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
                    "authorName": get_facebook_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                if 'post_id_from_websocket' in locals() and post_id_from_websocket:
                    error_result["postId"] = post_id_from_websocket
                
                # Thêm thông tin user_id từ tài khoản hiện tại
                user_ids = get_id_tosend_websocket
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
async def reply_to_comment(browser, pending_posts, get_facebook_name, get_websocket_role, get_id_tosend_websocket):
    """
    Hàm trả lời bình luận cụ thể dựa vào URL và aria-label
    """
    try:
        
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
                    user_ids = get_id_tosend_websocket
                    user_name = get_facebook_name
                    
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
                        "authorName": get_facebook_name,
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
                    user_ids = get_id_tosend_websocket
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
                    "authorName": get_facebook_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                if 'comment_id_from_websocket' in locals() and comment_id_from_websocket:
                    error_result["commentId"] = comment_id_from_websocket
                
                if 'post_id_from_websocket' in locals() and post_id_from_websocket:
                    error_result["postId"] = post_id_from_websocket
                
                # Thêm thông tin user_id từ tài khoản hiện tại
                user_ids = get_id_tosend_websocket
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
async def reply_to_reply_comment(browser,pending_posts,get_facebook_name, get_websocket_role, get_id_tosend_websocket):
    """
    Hàm trả lời reply comment cụ thể dựa vào URL, commentId và replyId
    """
    try:
        
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
                    user_ids = get_id_tosend_websocket
                    user_name = get_facebook_name
                    userId = reply_data.get("authorId", "")
                    
                    # Lấy commenter name từ post structure hoặc user accounts
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
                        "authorName": get_facebook_name,
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
                    user_ids = get_id_tosend_websocket
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
                    "authorName": get_facebook_name,
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
                user_ids = get_id_tosend_websocket
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

# Hàm tạo bài viết mới
async def post_news_feed(browser,pending_posts, get_facebook_name, get_websocket_role, get_id_tosend_websocket):
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
            post_box = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
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
            post_box = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
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
                      
    
                    
                    payloadPost = {
                        "facebookId": get_websocket_role,
                        "userId": userId,
                        "userNameFacebook": get_facebook_name,
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
                        "authorName": get_facebook_name,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Thêm postId nếu có từ WebSocket
                    if post_id_from_websocket:
                        url_data["postId"] = post_id_from_websocket
                        log_message(f"Đã thêm postId vào dữ liệu gửi: {post_id_from_websocket}", logging.INFO)
                    
                    # Thêm thông tin user_id từ tài khoản hiện tại
                    user_ids = get_id_tosend_websocket
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
            import traceback
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