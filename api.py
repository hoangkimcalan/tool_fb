import aiohttp
import asyncio

URL_API = "http://localhost:4000/api"
# URL_API = "https://backend-crm-skmr.onrender.com/api"

async def create_post(post_data):
    """Tạo bài viết mới (async)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{URL_API}/post",
                json=post_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        print("Lỗi khi đăng bài:", e)
        raise
    except Exception as e:
        print("Lỗi không xác định khi đăng bài:", e)
        raise

async def create_comment(comment_data):
    """Tạo bình luận cho bài viết (async)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{URL_API}/comment",
                json=comment_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        print("Lỗi khi bình luận bài:", e)
        raise
    except Exception as e:
        print("Lỗi không xác định khi bình luận:", e)
        raise

async def create_reply_comment(facebook_comment_id, reply_comment_data):
    """Phản hồi bình luận (async)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{URL_API}/comment/{facebook_comment_id}/feedback",
                json=reply_comment_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        print("Lỗi khi phản hồi bình luận:", e)
        raise
    except Exception as e:
        print("Lỗi không xác định khi phản hồi:", e)
        raise