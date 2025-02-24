# kịch bản:
'''
like bài, bình luận, thả tym, chia sẻ, đăng bài, kết bạn, nhắn tin
'''
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import pyautogui
import traceback
import threading
import socketio
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import NoSuchElementException
import requests



titles = ["video này hay quá", "ae xem video này hay không?", "có video hay đăng lên cho mọi người cùng xem",
         "mọi người có video nào hay như này có thể comment vào đây ta cùng xem nhỉ"]



content_post = [
    "Hãy để đam mê dẫn lối, chúng tôi đang tìm kiếm những tài năng sáng tạo, nhiệt huyết và muốn thách thức bản thân. Ứng tuyển ngay để mở ra cơ hội mới, khám phá tiềm năng vô hạn và cùng chúng tôi tạo nên những điều tuyệt vời trong tương lai!",
    "Bạn đã sẵn sàng cho hành trình mới? Một công việc tuyệt vời đang chờ đón bạn tại đây. Không chỉ là công việc, chúng tôi mang đến một môi trường giúp bạn phát triển và xây dựng sự nghiệp. Tham gia ngay và cùng nhau bứt phá giới hạn!",
    "Hãy đến với chúng tôi và khám phá những cơ hội tuyệt vời mà bạn không thể bỏ lỡ! Chúng tôi tin rằng với sự nỗ lực và đam mê của bạn, mọi giới hạn sẽ bị phá vỡ. Đăng ký ngay để trở thành một phần của đội ngũ thành công!",
    "Công việc trong mơ không còn xa, nó đang ở ngay trước mắt bạn! Chúng tôi đang tìm kiếm những ứng viên đầy nhiệt huyết, sáng tạo và sẵn sàng đón nhận thử thách. Cùng nhau, chúng ta sẽ chinh phục những đỉnh cao mới trong sự nghiệp!",
    "Gia nhập đội ngũ của chúng tôi là cơ hội để bạn phát triển bản thân và xây dựng sự nghiệp. Với môi trường làm việc năng động, thân thiện và đầy cơ hội thăng tiến, hãy cùng nhau tạo ra sự thay đổi lớn lao! Đừng bỏ lỡ, ứng tuyển ngay!",
    "Chúng tôi đang tìm kiếm những tài năng xuất sắc, sáng tạo và đam mê với công việc. Nếu bạn muốn thử thách bản thân trong một môi trường đầy năng động và cơ hội, đừng chần chừ, hãy gửi hồ sơ của bạn ngay hôm nay để cùng chúng tôi tiến xa hơn!",
    "Cơ hội không đến nhiều lần! Chúng tôi đang tìm kiếm những cá nhân tài năng, có đam mê và sẵn sàng đối mặt với thách thức mới. Hãy tham gia vào đội ngũ của chúng tôi để cùng nhau chinh phục những mục tiêu mới, xây dựng tương lai rực rỡ!",
    "Một hành trình sự nghiệp đầy triển vọng đang mở ra trước mắt bạn. Chúng tôi mang đến cơ hội phát triển bản thân và làm việc trong môi trường sáng tạo. Đừng ngại thử thách bản thân và ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội tuyệt vời này!",
    "Chúng tôi đang tìm kiếm những người bạn đồng hành đam mê, nhiệt huyết và sáng tạo để cùng nhau đạt được thành công. Đừng bỏ lỡ cơ hội này, gửi ngay hồ sơ của bạn và bước vào hành trình phát triển sự nghiệp đáng nhớ cùng chúng tôi!",
    "Đôi khi, cơ hội đến từ những điều bất ngờ. Hãy sẵn sàng cho một công việc mới đầy thú vị tại công ty chúng tôi. Môi trường làm việc thân thiện, sáng tạo và cơ hội thăng tiến luôn chờ đón bạn. Đừng bỏ qua, hãy ứng tuyển ngay!",
    "Bạn đã sẵn sàng bứt phá giới hạn? Một công việc thú vị trong môi trường đầy sáng tạo đang chờ đón bạn. Cùng chúng tôi chinh phục những đỉnh cao mới trong sự nghiệp và khám phá tiềm năng của bản thân. Ứng tuyển ngay để không bỏ lỡ!",
    "Chúng tôi tin rằng sự sáng tạo và nhiệt huyết của bạn sẽ là chìa khóa mở ra cánh cửa thành công trong công việc. Đừng bỏ lỡ cơ hội làm việc cùng một đội ngũ đầy tài năng và tận tâm. Ứng tuyển ngay hôm nay để khởi đầu hành trình mới!",
    "Công việc thú vị với những thách thức mới đang chờ đón bạn. Hãy tham gia đội ngũ của chúng tôi và cùng nhau khám phá những cơ hội phát triển không giới hạn. Đừng để tuột mất cơ hội này, ứng tuyển ngay và trở thành một phần của thành công!",
    "Nếu bạn đang tìm kiếm một môi trường làm việc sáng tạo, đầy thử thách và cơ hội phát triển, chúng tôi chính là điểm đến của bạn. Hãy nắm bắt cơ hội này và cùng chúng tôi xây dựng tương lai sự nghiệp vững chắc. Đăng ký ngay hôm nay!",
    "Mọi hành trình đều bắt đầu từ bước đi đầu tiên, và chúng tôi đang chờ đón bước đi của bạn. Cơ hội phát triển sự nghiệp không giới hạn đang mở ra tại đây, đừng bỏ lỡ, hãy gửi ngay hồ sơ của bạn để cùng chúng tôi tạo nên điều khác biệt!",
    "Sự nghiệp của bạn có thể phát triển vượt bậc khi bạn nắm bắt cơ hội. Chúng tôi đang tìm kiếm những ứng viên sáng tạo, nhiệt huyết và muốn phát triển bản thân. Hãy đến và khám phá cơ hội không giới hạn tại công ty chúng tôi. Ứng tuyển ngay!",
    "Thành công không đến từ việc chờ đợi, mà từ những hành động thiết thực. Hãy nắm bắt ngay cơ hội việc làm tuyệt vời tại công ty chúng tôi và cùng nhau tạo ra những giá trị đích thực. Ứng tuyển ngay hôm nay để trở thành một phần của đội ngũ!",
    "Bạn đang tìm kiếm một công việc mới, đầy thách thức và cơ hội phát triển? Hãy đến với chúng tôi, nơi sự sáng tạo và đam mê được trân trọng. Chúng tôi luôn chào đón những tài năng nhiệt huyết. Ứng tuyển ngay để không bỏ lỡ cơ hội!",
    "Tương lai sự nghiệp của bạn bắt đầu ngay hôm nay! Chúng tôi đang tìm kiếm những ứng viên tài năng và sáng tạo để cùng nhau xây dựng tương lai. Đừng chần chừ, hãy gửi hồ sơ của bạn ngay và gia nhập đội ngũ tuyệt vời của chúng tôi!",
    "Bạn đang tìm kiếm cơ hội phát triển sự nghiệp trong một môi trường chuyên nghiệp và năng động? Chúng tôi có vị trí dành cho bạn! Hãy cùng nhau khám phá và chinh phục những thử thách mới. Ứng tuyển ngay để không bỏ lỡ cơ hội tuyệt vời!",
    "Bạn có muốn trở thành một phần của đội ngũ tài năng và nhiệt huyết? Hãy tham gia cùng chúng tôi và khám phá những cơ hội phát triển bản thân không giới hạn. Đừng để lỡ cơ hội việc làm này, hãy ứng tuyển ngay và bắt đầu hành trình mới!",
    "Mỗi ngày đều là một cơ hội để bạn khám phá bản thân và phát triển sự nghiệp. Hãy đến với chúng tôi và cùng nhau tạo dựng tương lai tươi sáng hơn. Ứng tuyển ngay hôm nay để không bỏ lỡ những cơ hội phát triển không giới hạn!",
    "Bạn có sẵn sàng chinh phục những thử thách mới và khám phá tiềm năng bản thân? Chúng tôi đang tìm kiếm những ứng viên đam mê và tài năng như bạn. Hãy gửi hồ sơ ngay hôm nay để cùng chúng tôi xây dựng sự nghiệp vững chắc và thành công!",
    "Sự nghiệp của bạn chỉ cách một bước đi! Chúng tôi đang tìm kiếm những người đam mê, sáng tạo và sẵn sàng đối mặt với thách thức mới. Đừng bỏ lỡ cơ hội này, ứng tuyển ngay để trở thành một phần của đội ngũ đầy tài năng và nhiệt huyết!",
    "Bạn có muốn phát triển sự nghiệp trong một môi trường năng động và chuyên nghiệp? Chúng tôi đang chờ đón bạn! Hãy tham gia đội ngũ của chúng tôi và cùng nhau tạo ra những giá trị khác biệt. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội!",
    "Chúng tôi tin rằng bạn chính là mảnh ghép còn thiếu của đội ngũ chúng tôi! Hãy ứng tuyển ngay hôm nay để có cơ hội phát triển bản thân và sự nghiệp trong một môi trường đầy sáng tạo, thử thách và cơ hội thăng tiến. Đừng bỏ lỡ!",
    "Đừng để những cơ hội quý giá trôi qua! Hãy ứng tuyển ngay vào vị trí chúng tôi đang tìm kiếm và cùng nhau chinh phục những thử thách mới trong sự nghiệp. Môi trường làm việc thân thiện, sáng tạo và nhiều cơ hội thăng tiến đang chờ đón bạn!",
    "Bạn đã sẵn sàng cho những thử thách mới? Chúng tôi đang tìm kiếm những tài năng nhiệt huyết và sáng tạo để cùng nhau đạt được thành công. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển bản thân và sự nghiệp của bạn!",
    "Cơ hội việc làm tuyệt vời chỉ cách bạn một bước! Hãy tham gia đội ngũ của chúng tôi và khám phá những thử thách mới, cơ hội thăng tiến trong một môi trường sáng tạo và thân thiện. Đừng bỏ qua, ứng tuyển ngay hôm nay!",
    "Thành công bắt đầu từ một cơ hội. Hãy để chúng tôi cùng bạn thực hiện ước mơ sự nghiệp của mình. Chúng tôi đang tìm kiếm những người đam mê và tài năng. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển cùng chúng tôi!",
    "Bạn đang tìm kiếm một công việc thú vị với nhiều cơ hội phát triển? Hãy đến với chúng tôi và cùng nhau",
    "Chúng tôi đang tìm kiếm những tài năng đầy nhiệt huyết, sáng tạo và khao khát khám phá những thử thách mới. Đừng bỏ lỡ cơ hội phát triển bản thân tại môi trường làm việc năng động và thân thiện này. Hãy ứng tuyển ngay hôm nay để cùng chúng tôi tạo nên thành công!",
    "Bạn đã sẵn sàng bước vào hành trình sự nghiệp mới? Cùng chúng tôi chinh phục những thử thách, phát triển bản thân và xây dựng tương lai vững chắc. Đừng chần chừ, cơ hội không đến hai lần. Ứng tuyển ngay hôm nay để trở thành một phần của đội ngũ thành công!",
    "Hãy gia nhập đội ngũ của chúng tôi và khám phá những cơ hội phát triển không giới hạn. Chúng tôi luôn chào đón những cá nhân tài năng, đam mê và sẵn sàng đương đầu với thử thách. Hãy ứng tuyển ngay để cùng nhau tạo nên những thành công đột phá!",
    "Bạn có muốn trở thành một phần của môi trường làm việc sáng tạo, đầy thử thách và cơ hội? Hãy nắm bắt cơ hội việc làm tuyệt vời này và gia nhập đội ngũ của chúng tôi để phát triển sự nghiệp trong một tương lai tươi sáng hơn!",
    "Công việc trong mơ đang chờ đợi bạn! Chúng tôi đang tìm kiếm những người có đam mê và nhiệt huyết để cùng nhau xây dựng thành công. Đừng bỏ lỡ cơ hội này, ứng tuyển ngay hôm nay và cùng chúng tôi tạo nên những giá trị khác biệt!",
    "Bạn đã sẵn sàng bước vào hành trình phát triển sự nghiệp đầy triển vọng? Chúng tôi đang tìm kiếm những ứng viên nhiệt huyết, sáng tạo để cùng nhau đạt được những thành công mới. Đừng bỏ qua cơ hội này, hãy ứng tuyển ngay hôm nay!",
    "Mỗi ngày đều là một cơ hội để khám phá tiềm năng của bản thân. Hãy gia nhập đội ngũ của chúng tôi và cùng nhau tạo ra những điều tuyệt vời! Ứng tuyển ngay hôm nay để không bỏ lỡ những cơ hội phát triển sự nghiệp thú vị này!",
    "Chúng tôi đang tìm kiếm những người có niềm đam mê và sự sáng tạo không giới hạn. Nếu bạn muốn thử thách bản thân trong một môi trường làm việc đầy thú vị, hãy ứng tuyển ngay hôm nay và cùng chúng tôi đạt được những thành công lớn!",
    "Cơ hội việc làm tuyệt vời không đến thường xuyên! Hãy nhanh chóng ứng tuyển để trở thành một phần của đội ngũ sáng tạo và nhiệt huyết của chúng tôi. Đừng bỏ lỡ cơ hội phát triển bản thân và sự nghiệp, nộp hồ sơ ngay hôm nay!",
    "Bạn có đam mê với công việc? Chúng tôi đang tìm kiếm những ứng viên tài năng và nhiệt huyết để cùng nhau chinh phục những thử thách mới. Hãy gửi hồ sơ ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển sự nghiệp vượt bậc!",
    "Mỗi cơ hội đến đều là một bước tiến trong sự nghiệp của bạn. Chúng tôi đang tìm kiếm những ứng viên đam mê, sáng tạo và sẵn sàng đối mặt với thử thách. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội tuyệt vời này!",
    "Hãy đến với chúng tôi và khám phá những cơ hội phát triển sự nghiệp mà bạn luôn mong muốn. Chúng tôi đang tìm kiếm những tài năng sáng tạo, nhiệt huyết và có khát vọng. Đừng bỏ lỡ, ứng tuyển ngay để cùng chúng tôi tạo nên thành công!",
    "Sự nghiệp của bạn chỉ cách một bước đi! Hãy nắm bắt cơ hội này và tham gia đội ngũ của chúng tôi. Chúng tôi chào đón những ứng viên đam mê và sáng tạo để cùng nhau phát triển sự nghiệp trong môi trường năng động và thân thiện!",
    "Bạn đang tìm kiếm một công việc thú vị, đầy thử thách và cơ hội thăng tiến? Hãy tham gia vào đội ngũ của chúng tôi để phát triển bản thân trong môi trường làm việc sáng tạo và đầy năng động. Đừng bỏ qua, ứng tuyển ngay hôm nay!",
    "Chúng tôi đang tìm kiếm những người có đam mê và tài năng để cùng nhau tạo nên những giá trị khác biệt. Môi trường làm việc sáng tạo, đầy thử thách đang chờ đón bạn! Hãy gửi hồ sơ ứng tuyển ngay để bắt đầu hành trình sự nghiệp của bạn!",
    "Bạn đã sẵn sàng cho những thử thách mới? Hãy nắm bắt cơ hội này để phát triển sự nghiệp trong một môi trường chuyên nghiệp, thân thiện và đầy cơ hội. Ứng tuyển ngay hôm nay để không bỏ lỡ những cơ hội phát triển quý giá!",
    "Hãy đến với chúng tôi và khám phá tiềm năng của bản thân! Chúng tôi đang tìm kiếm những ứng viên sáng tạo, nhiệt huyết và muốn thử thách chính mình. Đừng chần chừ, hãy ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển bản thân!",
    "Mỗi ngày là một cơ hội mới để phát triển sự nghiệp. Hãy tham gia cùng chúng tôi để khám phá những thách thức thú vị và cơ hội thăng tiến trong môi trường làm việc năng động. Đừng bỏ lỡ, ứng tuyển ngay hôm nay để không bỏ qua cơ hội tuyệt vời!",
    "Bạn có muốn phát triển sự nghiệp trong một môi trường làm việc đầy thử thách và cơ hội? Hãy ứng tuyển ngay hôm nay và gia nhập đội ngũ tài năng của chúng tôi để cùng nhau tạo nên những giá trị khác biệt và thành công!",
    "Công việc mơ ước của bạn chỉ cách một bước! Hãy nhanh chóng nắm bắt cơ hội này và tham gia vào đội ngũ của chúng tôi để phát triển sự nghiệp trong môi trường năng động và sáng tạo. Đừng bỏ lỡ cơ hội tuyệt vời này, ứng tuyển ngay!",
    "Chúng tôi đang tìm kiếm những ứng viên tài năng và nhiệt huyết để cùng nhau xây dựng một tương lai thành công. Nếu bạn đang tìm kiếm một công việc đầy thử thách và cơ hội, hãy ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển!",
    "Sự nghiệp của bạn sẽ bứt phá khi bạn nắm bắt cơ hội. Chúng tôi đang tìm kiếm những người đam mê, sáng tạo và sẵn sàng đối mặt với thử thách. Đừng bỏ lỡ, hãy ứng tuyển ngay để trở thành một phần của đội ngũ tài năng của chúng tôi!",
    "Một môi trường làm việc thân thiện, sáng tạo và đầy cơ hội thăng tiến đang chờ đón bạn! Hãy ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển bản thân và sự nghiệp cùng với chúng tôi. Đừng để cơ hội này tuột khỏi tầm tay!",
    "Bạn có sẵn sàng cho những cơ hội mới? Chúng tôi đang tìm kiếm những ứng viên đam mê, sáng tạo và có khát vọng. Hãy gửi hồ sơ ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội làm việc trong môi trường năng động và thân thiện của chúng tôi!",
    "Đừng để cơ hội việc làm tuyệt vời này trôi qua! Hãy nhanh chóng ứng tuyển vào vị trí chúng tôi đang tìm kiếm để phát triển bản thân trong môi trường làm việc sáng tạo, năng động và thân thiện. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội!",
    "Chúng tôi đang tìm kiếm những ứng viên tài năng và đam mê để cùng nhau phát triển sự nghiệp. Nếu bạn muốn thử thách bản thân và khám phá những cơ hội mới, hãy ứng tuyển ngay hôm nay để cùng chúng tôi chinh phục những đỉnh cao mới!",
    "Môi trường làm việc sáng tạo, thân thiện và đầy cơ hội phát triển đang chờ đón bạn. Hãy nhanh chóng nắm bắt cơ hội này và ứng tuyển ngay hôm nay để trở thành một phần của đội ngũ thành công và đầy nhiệt huyết của chúng tôi!",
    "Bạn đang tìm kiếm một công việc đầy thử thách và cơ hội phát triển? Chúng tôi đang chờ đón bạn! Hãy nộp hồ sơ ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội làm việc trong môi trường sáng tạo và đầy triển vọng của chúng tôi!",
    "Công việc trong mơ của bạn không còn xa! Hãy nhanh chóng ứng tuyển vào vị trí mà chúng tôi đang tìm kiếm để phát triển bản thân trong môi trường năng động và thân thiện. Đừng bỏ lỡ cơ hội này, hãy ứng tuyển ngay hôm nay!",
    "Thời tiết hôm này thật thoải mái và dễ chịu, tâm trạng mình cũng rất tốt, cuối cùng mình cũng đạt được mục tiêu của mình. Tiếp tục cố gắng cho những điều tốt đẹp phía trước!"
]


def download_video():
    url = 'http://103.138.113.142:8000/get_video'
    response = requests.get(url)
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    video_path = desktop + '\downloaded_video.mp4'
    if response.status_code == 200:
        with open(video_path, 'wb') as video_file:
            video_file.write(response.content)
        print('video đã được tải xuống')
    else:
        print('không thể tải video', response.status_code)
    return video_path

def login(username, password, code_2fa):
    txtUser = browser.find_element(By.ID, 'email')
    txtUser.send_keys(username)
    txtPassword = browser.find_element(By.ID, 'pass')
    txtPassword.send_keys(password)
    txtPassword.send_keys(Keys.ENTER)
    time.sleep(5)
    try:
        try_another = browser.find_element(By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft")
        try_another.click()
        time.sleep(1)
        option_code = browser.find_element(By.CSS_SELECTOR, "input[dir='ltr']")
        option_code.click()
        option_code.send_keys(Keys.ARROW_DOWN)
        print('continue')
        continue_button = browser.find_elements(By.CSS_SELECTOR,
                                                "div[class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3']")
        actions = ActionChains(browser)
        actions.move_to_element(continue_button[1]).click().perform()
    except:
        print('khong can lua chon')

    # lấy mã xác thực trên 2fa.live
    try:
        # time.sleep(20)
        browser.execute_script("window.open('https://2fa.live/', 'new window')")
        handles = browser.window_handles
        browser.switch_to.window(browser.window_handles[1])
        wait_2fa = WebDriverWait(browser, 7)
        text_input = wait_2fa.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#listToken")))
        text_input.send_keys(code_2fa)
        browser.find_element(By.CSS_SELECTOR, "#submit").click()
        time.sleep(1)
        browser.find_element(By.ID, "copy_btn").click()
        browser.close()
        browser.switch_to.window(handles[0])
        clipboard_text = pyperclip.paste()
        clipboard_text = clipboard_text.replace("\n" + str(code_2fa) + "|", "")
        time.sleep(2)

        send_code = browser.find_element(By.CSS_SELECTOR, "input[dir='ltr']")
        send_code.send_keys(clipboard_text)
        send_code.send_keys(Keys.ENTER)
    except Exception as err:
        print('loi send code:', err)
    time.sleep(5)


def like_post():
    '''Like, Yêu thích, Thương thương, Haha, Wow, Buồn, Phẫn nộ'''
    try:
        like_button = browser.find_element(By.XPATH, "//span[@data-ad-rendering-role='thích_button']")
    except:
        like_button = browser.find_element(By.XPATH, "//span[@data-ad-rendering-role='like_button']")
    actions = ActionChains(browser)
    actions.move_to_element(like_button).perform()
    a = random.randint(0, 49)
    time.sleep(2)
    if a % 2 == 0:
        try:
            reaction_xpath = '//div[@aria-label="Thích"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
        except:
            reaction_xpath = '//div[@aria-label="Like"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
    elif a % 5 == 0:
        try:
            reaction_xpath = '//div[@aria-label="Yêu thích"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
        except:
            reaction_xpath = '//div[@aria-label="Love"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
    elif a % 3 == 0:
        try:
            reaction_xpath = '//div[@aria-label="Thương thương"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
        except:
            reaction_xpath = '//div[@aria-label="Care"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
    elif a % 7 == 0:
        reaction_xpath = '//div[@aria-label="Haha"]'
        reaction = browser.find_element(By.XPATH, reaction_xpath)
        reaction.click()
    elif a % 11 == 0:
        reaction_xpath = '//div[@aria-label="Wow"]'
        reaction = browser.find_element(By.XPATH, reaction_xpath)
        reaction.click()
    else:
        try:
            reaction_xpath = '//div[@aria-label="Phẫn nộ"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()
        except:
            reaction_xpath = '//div[@aria-label="Angry"]'
            reaction = browser.find_element(By.XPATH, reaction_xpath)
            reaction.click()

time.sleep(2)
# chia sẻ

def share_post(content):
    try:
        share_button = browser.find_element(By.XPATH, "//div[@aria-label='Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn.']")
    except:
        share_button = browser.find_element(By.XPATH, "//div[@aria-label='Send this to friends or post it on your profile.']")
    share_button.click()
    time.sleep(2)
    try:
        share = browser.find_element(By.XPATH, "//div[@aria-label='Chia sẻ ngay']")
    except:
        share = browser.find_element(By.XPATH, "//div[@aria-label='Share now']")
    share.click()

# đăng bài
# post_button = browser.find_element(By.XPATH, "//div[@aria-label='Tạo bài viết']")

def post_news():
    time.sleep(random.randint(5, 10))
    try:
        home = browser.find_element(By.XPATH, "//a[@aria-label='Trang chủ']")
    except:
        home = browser.find_element(By.XPATH, "//a[@aria-label='Home']")
    home.click()
    time.sleep(random.randint(5, 10))
    post_button = browser.find_element(By.XPATH, "//div[@class='x1ey2m1c xds687c x17qophe xg01cxk x47corl x10l6tqk x13vifvy x1ebt8du x19991ni x1dhq9h x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m']")
    post_button.click()
    time.sleep(random.randint(10, 15))
    h3_post = post_button.find_element(By.XPATH, "//div[@class='xi81zsa x1lkfr7t xkjl1po x1mzt3pk xh8yej3 x13faqbe']")
    h3_post.click()
    time.sleep(random.randint(5, 10))
    print('đã click')
    send_content = browser.find_element(By.XPATH, "//p[@class='xdj266r x11i5rnm xat24cr x1mh8g0r x16tdsg8']")
    send_content.send_keys(content_post[random.randint(0, len(content_post)-1)])
    time.sleep(random.randint(5, 8))
    try:
        post_new = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đăng']")
    except:
        post_new = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Post']")
    post_new.click()

# bình luận
def comment_post():
    time.sleep(random.randint(3, 5))
    try:
        comment = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Viết bình luận"]')
    except:
        comment = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Leave a comment"]')
    action = ActionChains(browser)
    time.sleep(random.randint(3, 5))
    try:
        action.move_to_element(comment).click().perform()
    except:
        print('khong click binh luan')

    comments = [" Danh sách ứng viên bên timviec365 OK nha, nhiều đa dạng các vị trí và hồ sơ chất nhé. Bên mình sử dụng dịch vụ lọc hồ sơ ứng viên 3 lần rồi. Giá cả phải chăng, ứng viên OK nhé.",
     " Chất lượng ứng viên bên timviec365 có OK không các bạn ơi. Nghe bạn e bảo công ty nó cũng dùng và bảo cũng được, nhưng chưa biết thiên hạ review thế nào?",
     " Công cụ tìm ứng viên bên timviec365 để xem thông tin xịn nha mọi người. Mình có thể tìm theo ngành nghề, tỉnh thành, công việc mong muốn hoặc theo từ khoá trong CV luôn nha. Danh sách ứng viên nhiều, tha hồ mà xem nhé.",
     " Ứng viên bên timviec365 đa dạng ngành nghề nha các tình yêu nhất là các ứng viên kinh doanh, nhập liệu, chăm sóc khách hàng í. Công ty mình cũng đang dùng. Hỗ trợ nhiệt tình, 24/24 luôn mà."]

    idx = random.randint(0, len(comments)-1)
    print('comment:', comments[idx])
    time.sleep(random.randint(5, 10))
    comment.send_keys(comments[idx])
    try:
        win = browser.find_element(By.XPATH, "//div[@aria-hidden='false']")
        try:
            enter = win.find_element(By.CSS_SELECTOR, 'div[aria-label="Bình luận"]')
            action = ActionChains(browser)
            action.move_to_element(enter).click().perform()
        except:
            enter = win.find_element(By.CSS_SELECTOR, 'div[aria-label="Comment"]')
            action = ActionChains(browser)
            action.move_to_element(enter).click().perform()
        print('comment xong')
    except:
        try:
            enter = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Bình luận"]')
            action = ActionChains(browser)
            action.move_to_element(enter).click().perform()
        except:
            enter = win.find_element(By.CSS_SELECTOR, 'div[aria-label="Comment"]')
            action = ActionChains(browser)
            action.move_to_element(enter).click().perform()
        print('comment xong')
    link_ele = browser.find_element(By.XPATH, "//span[@class='xt0psk2']")
    link_ele.click()
    time.sleep()
    link = browser.current_url
    api = "https://api.timviec365.vn/api/getData/saveLink"
    time_now = time.time()
    print('input:', {"link": link, "time": time_now})
    response = requests.post(api, data={"link": link, "time": time_now})
    api_push = '43.239.223.143:8088/comments'
    response_push = requests.post(api_push, data={"link": link})
    # thêm bạn bè
    try:
        add_friend = browser.find_element(By.XPATH, "//div[@aria-label='Thêm bạn bè']")
        add_friend.click()
    except:
        add_friend = browser.find_element(By.XPATH, "//div[@aria-label='Add friend']")
        add_friend.click()

# nhắn tin

def send_messenge(link_user, content):
    '''chỉ nhắn tin trong danh sách bạn bè'''
    browser.get(link_user)
    time.sleep(5)
    # try:
    #     link_ele = browser.find_element(By.XPATH, "//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1sur9pj xkrqix3 x1s688f']")
    # except:
    #     link_ele = browser.find_element(By.XPATH, "//div[@class='xsgj6o6 xw3qccf x1xmf6yo x1w6jkce xusnbm3']")
    # link_ele.click()
    time.sleep(5)
    try:
        send = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Nhắn tin"]')
    except:
        send = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Message"]')
    send.click()
    time.sleep(5)
    try:
        send_text = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Nhắn tin'][role='textbox']")
    except:
        send_text = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Message'][role='textbox']")
    send_text.click()
    send_text.send_keys(content)
    send_text.send_keys(Keys.ENTER)
    time.sleep(random.randint(2, 3))
    try:
        close_chat = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đóng đoạn chat']")
    except:
        close_chat = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Close chat']")
    time.sleep(random.randint(5, 10))
    close_chat.click()
    time.sleep(3)

def reply_inbox():
    try:
        messenger = browser.find_element(By.XPATH, "//div[@aria-label='Messenger']")
        messenger.click()
    except:
        for i in range(1, 5):
            try:
                messenger = browser.find_element(By.XPATH, "//div[@aria-label='Messenger, {} chưa đọc']".format(i))
                messenger.click()
                break
            except:
                continue
    time.sleep(3)
    option_messenge = browser.find_element(By.XPATH, "//div[@class='html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd']")
    option_messenge.click()
    try:
        send = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Nhắn tin"]')
    except:
        send = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Message"]')
    send.click()
    time.sleep(5)
    try:
        send_text = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Nhắn tin'][role='textbox']")
    except:
        send_text = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Message'][role='textbox']")
    send_text.click()
    send_text.send_keys(content_post[random.randint(0, len(content_post)-1)])
    send_text.send_keys(Keys.ENTER)
    try:
        close_chat = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đóng đoạn chat']")
    except:
        close_chat = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Close chat']")
    time.sleep(random.randint(5, 10))
    close_chat.click()
    time.sleep(3)

def add_friend():
    '''hàm này dùng để kết bạn trong nhóm'''
    try:
        try:
            browser.get("https://www.facebook.com/search/groups?q={}&filters=eyJwdWJsaWNfZ3JvdXBzOjAiOiJ7XCJuYW1lXCI6XCJwdWJsaWNfZ3JvdXBzXCIsXCJhcmdzXCI6XCJcIn0ifQ%3D%3D".format("tuyển dụng"))
            while str(browser.current_url) == "https://www.facebook.com/":
                print('làm lại')
                browser.get("https://www.facebook.com/search/groups?q={}&filters=eyJwdWJsaWNfZ3JvdXBzOjAiOiJ7XCJuYW1lXCI6XCJwdWJsaWNfZ3JvdXBzXCIsXCJhcmdzXCI6XCJcIn0ifQ%3D%3D".format("tuyển dụng"))
        except:
            print('loi roi')
        time.sleep(random.uniform(2, 3))
        element = browser.find_elements(By.XPATH, '//a[@aria-hidden="true" and contains(@href, "/groups/")]')
        link = element[random.randint(0, len(element) - 1)].get_attribute("href")
        browser.get(link)
        time.sleep(3)
        check_status = browser.find_element(By.CSS_SELECTOR,
                                            "[class='x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w xeuugli xg83lxy x1h0ha7o x1120s5i x1nn3v0j']")
        print('status:', check_status.text)
        # kết bạn trong nhóm
        link_user = browser.find_element(By.XPATH, "//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 xzsf02u x1s688f']")
        time.sleep(random.uniform(2, 3))

        # Cuộn tới phần tử và đảm bảo phần tử xuất hiện ở giữa trang
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_user)
        time.sleep(random.uniform(2, 3))
        link_user.click()
        time.sleep(random.uniform(2, 3))
        add_friend = browser.find_element(By.XPATH, "//div[@aria-label='Thêm bạn bè']")
        add_friend.click()
        link_friend = browser.current_url
        print('link_friend:', link_friend)
        time.sleep(random.uniform(3, 5))
        send_messenge(link_friend, "Chào bạn, mình là nhân sự bên timviec365, bạn cho mình hỏi là bạn đang đi tìm việc hay là bên tuyển dụng đó ạ? Nếu bạn đang cần tìm ứng viên hoặc đang cần tìm việc làm thì bạn lên trang web timviec365.vn tham khảo nhé.")
    except Exception as err:
        print('loi tim nhom:', err)

def join_group(nganhnghe):
    # join nhóm
    try:
        try:
            browser.get("https://www.facebook.com/search/groups?q={}&filters=eyJwdWJsaWNfZ3JvdXBzOjAiOiJ7XCJuYW1lXCI6XCJwdWJsaWNfZ3JvdXBzXCIsXCJhcmdzXCI6XCJcIn0ifQ%3D%3D".format(nganhnghe))
            while str(browser.current_url) == "https://www.facebook.com/":
                print('làm lại')
                browser.get("https://www.facebook.com/search/groups?q={}&filters=eyJwdWJsaWNfZ3JvdXBzOjAiOiJ7XCJuYW1lXCI6XCJwdWJsaWNfZ3JvdXBzXCIsXCJhcmdzXCI6XCJcIn0ifQ%3D%3D".format(nganhnghe))
        except:
            print('loi roi')
        time.sleep(random.uniform(2, 3))
        element = browser.find_elements(By.XPATH, '//a[@aria-hidden="true" and contains(@href, "/groups/")]')
        link = element[random.randint(0, len(element) - 1)].get_attribute("href")
        browser.get(link)
        time.sleep(3)
        check_status = browser.find_element(By.CSS_SELECTOR,
                                            "[class='x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x2lah0s x193iq5w xeuugli xg83lxy x1h0ha7o x1120s5i x1nn3v0j']")
        print('status:', check_status.text)
        # if check_status.text == "Nhóm Riêng tư":
        try:
            join_group = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Tham gia nhóm']")
            join_group.click()
        except:
            join_group = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Join group']")
            join_group.click()
        time.sleep(3)
        try:
            try:
                answer_question = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Trả lời câu hỏi']")
            except:
                answer_question = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Answer questions']")
            time.sleep(1)
            try:
                click_options = answer_question.find_elements(By.CSS_SELECTOR, "input[dir='ltr']")
                for click_option in click_options:
                    time.sleep(2)
                    click_option.click()
            except Exception as err:
                print('loi chon:', err)
            try:
                time.sleep(2)
                try:
                    write_answers = answer_question.find_elements(By.XPATH, "//textarea[@placeholder='Viết câu trả lời...']")
                except:
                    write_answers = answer_question.find_elements(By.XPATH, "//textarea[@placeholder='Write an answer...']")
                for write_answer in write_answers:
                    try:
                        write_answer.send_keys('Đồng ý')
                    except:
                        write_answer.send_keys('Agree')
                    time.sleep(2)
                    print('trả lời xong')
            except Exception as err:
                print('loi tra loi:', err)
            try:
                click_options = answer_question.find_elements(By.CSS_SELECTOR, "input[dir='ltr']")
                for click_option in click_options:
                    time.sleep(2)
                    click_option.click()
            except Exception as err:
                print('loi chon:', err)
            time.sleep(2)
            browser.execute_script("window.scrollTo(0, 2500)")
            time.sleep(3)
            try:
                send = answer_question.find_element(By.XPATH, "//div[@aria-label='Gửi']")
            except:
                send = answer_question.find_element(By.XPATH, "//div[@aria-label='Submit']")
            send.click()
            time.sleep(10)
        except Exception as err:
            print('err:', err)
    except Exception as err:
        print('loi tim nhom:', err)

# đọc thông báo
# def read_notification():
#     all_notification = []
#     time.sleep(random.uniform(2, 3))
#     browser.get("https://www.facebook.com/notifications")
#     notifications = browser.find_elements(By.XPATH, "//div[@class='x1n2onr6']")
#     for noti in notifications:
#         notification = {}
#         notification["text"] = text
#         notification["time"] = time
#         print('noti:', noti.text)

def list_group():
    try:
        find_group = browser.find_element(By.XPATH, "//a[@aria-label='Nhóm']")
    except:
        find_group = browser.find_element(By.XPATH, "//a[@aria-label='Groups']")
    find_group.click()
    time.sleep(random.uniform(4, 6))
    try:
        see_all = browser.find_element(By.XPATH, "//a[@aria-label='Xem tất cả']")
    except:
        see_all = browser.find_element(By.XPATH, "//a[@aria-label='See all']")
    see_all.click()
    time.sleep(random.uniform(4, 6))
    get_link = browser.find_elements(By.XPATH, "//a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1sur9pj xkrqix3 x1pd3egz']")
    for link in get_link:
        groups = {}
        link_group = link.get_attribute('href')
        groups["link"] = link_group
        groups["id"] = id
        api = '43.239.223.143:8088/list_friend'
        response = requests.post(api, json=groups)
    time.sleep(random.uniform(4, 6))
    try:
        home = browser.find_element(By.XPATH, "//a[@aria-label='Trang chủ']")
    except:
        home = browser.find_element(By.XPATH, "//a[@aria-label='Home']")
    home.click()
    # pass

def list_friend(id):
    list_friend = []
    browser.get('https://www.facebook.com/friends/list')
    get_link = browser.find_elements(By.XPATH, "//a[@class='x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x87ps6o x1lku1pv x1a2a7pz x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1lliihq']")
    for link in get_link:
        friends = {}
        link_friend = link.get_attribute('href')
        friends["link"] = link_friend
        friends["id"] = id
        api = '43.239.223.143:8088/list_friend'
        response = requests.post(api, json=friends)
        list_friend.append(link_friend)
    time.sleep(random.uniform(4, 6))
    send_messenge(list_friend[random.randint(0, len(list_friend)-1)], content_post[random.randint(0, len(content_post)-1)])
    try:
        home = browser.find_element(By.XPATH, "//a[@aria-label='Trang chủ']")
    except:
        home = browser.find_element(By.XPATH, "//a[@aria-label='Home']")
    home.click()

def agree_friend():
    browser.get("https://www.facebook.com/friends/requests")
    time.sleep(random.uniform(5, 8))
    try:
        agree = browser.find_element(By.XPATH, "//div[@aria-label='Xác nhận']")
    except:
        agree = browser.find_element(By.XPATH, "//div[@aria-label='Confirm']")
    agree.click()
    time.sleep(random.uniform(3, 5))
    print('ket ban xong')

def see_video():
    browser.get("https://www.facebook.com/watch/")
    time.sleep(random.uniform(30, 50))
    a = random.randint(0, 50)
    if a % 2 == 0:
        print('like post')
        like_post()
    time.sleep(random.uniform(30, 50))
    if a == 0:
        print('share post')
        share_post("")
    time.sleep(random.uniform(24, 36))
    element = browser.find_elements(By.XPATH, "//div[@class='x1ey2m1c x9f619 xds687c x17qophe x10l6tqk x13vifvy x1ypdohk']")

    browser.execute_script("arguments[0].scrollIntoView();", element[random.randint(1, 3)])
    print('cuộn xong')
    time.sleep(random.uniform(2400, 3600))

def interact_friend():
    browser.get('https://www.facebook.com/friends/list')
    time.sleep(5)
    list_friend = browser.find_elements(By.XPATH, "//div[@data-visualcompletion='ignore-dynamic']")
    friend = list_friend[random.randint(0, len(list_friend)-1)]
    friend.click()
    time.sleep(6)
    like_post()

def rep_inbox():
    pass
def rep_notification():
    # khi gọi đến hàm này
    browser.get("https://www.facebook.com/notifications")
    # thì đầu tiên là trả về toàn bộ 6 thông báo gần nhất
    time.sleep(random.uniform(4, 6))
    # sau đó người dùng click vào thông báo bất kỳ, gửi đến server, server click vào thông báo đó
    see_notifications = browser.find_elements(By.XPATH, "//div[@class='x1n2onr6']")
    see_notifications[0].click()
    time.sleep(random.uniform(4, 6))
    try:
        try:
            see_all = browser.find_element(By.XPATH, "//div[@aria-label='Xem tất cả']")
            see_all.click()
        except:
            see_all = browser.find_element(By.XPATH, "//div[@aria-label='See all']")
            see_all.click()
    except:
        pass
    # hiển thị nội dung của thông báo sau khi click
    content = browser.find_element(By.XPATH, "//div[@class='x169t7cy x19f6ikt']")
    print('content:', content.text)

def surf_facebook(id, title, browser):
    '''hàm này để lướt fb dạo
    trước tiên lướt fb, sau đó chọn 1 bài viết ngẫu nhiên để đọc cmt hoặc like hoặc share,
     tìm một nhóm bất kỳ và join nhóm, kết bạn với 1 thành viên trong nhóm sau đó nhắn tin với người đó,
     một ngày chỉ kết bạn với 3 người và nhắn tin nhắn chờ với 3 người đó từ 8h sáng đến 9h sáng, 12h trưa đến 1h chiều
     8h tối đến 9h tối...'''
    browser.get("https://www.facebook.com")
    try:
        time.sleep(random.uniform(5, 8))
        # lướt dạo
        a = random.randint(5, 10)
        while a > 0:
            browser.execute_script("window.scrollBy(0, {});".format(random.randint(200, 800)))
            time.sleep(random.uniform(2, 4))
            if a % 2 == 0:
                like_post()
                time.sleep(random.uniform(5, 8))
            a = a - 1
        # đọc comment
        try:
            comment = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Viết bình luận"]')
        except:
            comment = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Leave a comment"]')
        action = ActionChains(browser)
        time.sleep(2)
        try:
            action.move_to_element(comment).click().perform()
        except:
            print('khong click binh luan')
        time.sleep(random.uniform(2, 4))
        b = random.randint(3, 5)
        while b > 0:
            time.sleep(random.uniform(2, 4))
            browser.execute_script("window.scrollBy(0, {});".format(random.randint(100, 200)))
            b = b - 1
    except:
        pass
    try:
        see_video()
    except:
        pass
    try:
        c = random.randint(0, 10)
        if c == 0:
            agree_friend()
        elif c == 1:
            list_friend(id)
        elif c == 2:
            list_group(id)
        # elif c == 3:
        #     read_notification()
        elif c == 4:
            join_group()
        elif c == 5:
            add_friend()
        elif c == 6:
            reply_inbox()
        # elif c == 7:
        #     read_notification()
        elif c == 8:
            post_video(title)
        elif c == 9:
            interact_friend()
        time.sleep(random.uniform(2, 4))
        try:
            see_video()
        except:
            pass
    except:
        pass

# tương tác qua tin nhắn
def safe_find_element(browser, by, value):
    try:
        return browser.find_element(by, value)
    except NoSuchElementException:
        print(f"Element not found: {value}")
        return None

def safe_find_elements(browser, by, value):
    try:
        return browser.find_elements(by, value)
    except NoSuchElementException:
        print(f"Element not found: {value}")
        return None

def update_list_conversation():
    browser.get("https://www.facebook.com/messages/")
    time.sleep(random.uniform(4, 6))
    list_messenger = safe_find_element(browser, By.XPATH, "//div[@aria-label = 'Đoạn chat']")
    # element từng box chat
    all_list = safe_find_elements(list_messenger, By.XPATH, "//div[@class='x78zum5 xdt5ytf']")
    all_chat = []
    all_conversation = {}
    for friend in all_list:
        print('friend1:', friend.text)
        try:
            try:
                link_element = safe_find_element(friend, By.XPATH, ".//a[@aria-current = 'false']")
                link = link_element.get_attribute("href")
            except:
                link_element = safe_find_element(friend, By.XPATH, ".//a[@aria-current = 'page']")
                link = link_element.get_attribute("href")
            print('link:', link)
            id_chat = str(link).split('/')[5]
            content_friend = safe_find_element(friend, By.XPATH,
                                               ".//div[@class = 'x9f619 x1ja2u2z x78zum5 x1n2onr6 x1iyjqo2 xs83m0k xeuugli x1qughib x6s0dn4 x1a02dak x1q0g3np xdl72j9']")
            content = content_friend.text
            content = content.split('\n')
            name = content[0]
            content_chat = content[1]
            send_time = content[-1]
            all_chat.append({'id_chat': id_chat, 'name': name, 'content_chat': content_chat, 'send_time': send_time})
        except:
            continue
    all_conversation['id_fb'] = id_fb
    all_conversation['list_conversation'] = all_chat
    update_list_conversation = "http://43.239.223.143:8088/update_list_conversation"
    res = requests.post(update_list_conversation, json={"id_fb": id_fb, "list_conversation": all_chat})


def post_video(title):
    browser.get("https://www.facebook.com")
    time.sleep(5)
    post_element = browser.find_element(By.XPATH, "//div[@class='x1i10hfl x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x16tdsg8 x1hl2dhg xggy1nq x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xmjcpbm x107yiy2 xv8uw2v x1tfwpuw x2g32xy x78zum5 x1q0g3np x1iyjqo2 x1nhvcw1 x1n2onr6 xt7dq6l x1ba4aug x1y1aw1k xn6708d xwib8y2 x1ye3gou']")
    post_element.click()
    time.sleep(5)
    post_vi = browser.find_element(By.XPATH, "//div[@aria-label='Photo/video']")
    post_vi.click()
    time.sleep(2)
    add_video = browser.find_element(By.XPATH, "//div[@class='html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x14yjl9h xudhj91 x18nykt9 xww2gxu x6s0dn4 x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x3nfvp2 xl56j7k x1n2onr6 x1qhmfi1 x1vqgdyp x100vrsf']")
    add_video.click()
    time.sleep(2)
    video_path = download_video()
    pyperclip.copy(video_path)
    # Gửi tổ hợp phím Ctrl+V để dán từ clipboard
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(3)
    pyautogui.press('enter')
    time.sleep(3)
    try:
        post_text_area = browser.find_element(By.CSS_SELECTOR, "//div[@class='x1ed109x x1iyjqo2 x5yr21d x1n2onr6 xh8yej3']")
        post_text_area.send_keys(title)
    except:
        pass
    time.sleep(3)
    try:
        add_vd = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đăng']")
        add_vd.click()
    except:
        add_vd = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Post']")
        add_vd.click()
    time.sleep(5)
    os.remove(video_path)

sio = socketio.Client()


@sio.event
def connect():
    print('connected to server')

@sio.event
def disconnect():
    print("disconnected from server")

@sio.on('check_new_messenger')
def handle_server_request(data):
    print('bat dau check')
    time.sleep(random.uniform(4, 6))
    check_messenger = browser.find_element(By.XPATH, "//div[@aria-label='Messenger']")
    try:
        check_messenger.click()
        print('có tin nhắn mới nên không cập nhật')
    except:
        sio.emit('client_response', {'result':'you have new messages'})
        browser.get("https://www.facebook.com/messages/")
        time.sleep(random.uniform(4, 6))
        list_messenger = safe_find_element(browser, By.XPATH, "//div[@aria-label = 'Đoạn chat']")
        # element từng box chat
        all_list = safe_find_elements(list_messenger, By.XPATH, "//div[@class='x78zum5 xdt5ytf']")
        all_chat = []
        all_conversation = {}
        for friend in all_list:
            print('friend1:', friend.text)
            try:
                try:
                    link_element = safe_find_element(friend, By.XPATH, ".//a[@aria-current = 'false']")
                    link = link_element.get_attribute("href")
                except:
                    link_element = safe_find_element(friend, By.XPATH, ".//a[@aria-current = 'page']")
                    link = link_element.get_attribute("href")
                print('link:', link)
                id_chat = str(link).split('/')[5]
                content_friend = safe_find_element(friend, By.XPATH, ".//div[@class = 'x9f619 x1ja2u2z x78zum5 x1n2onr6 x1iyjqo2 xs83m0k xeuugli x1qughib x6s0dn4 x1a02dak x1q0g3np xdl72j9']")
                content = content_friend.text
                content = content.split('\n')
                name = content[0]
                content_chat = content[1]
                send_time = content[-1]
                all_chat.append({'id_chat':id_chat, 'name':name, 'content_chat':content_chat, 'send_time':send_time})
            except:
                continue
        all_conversation['id_fb'] = id_fb
        all_conversation['list_conversation'] = all_chat
        update_list_conversation = "http://43.239.223.143:8088/update_list_conversation"
        res = requests.post(update_list_conversation, json={"id_fb": id_fb, "list_conversation": all_chat})
        print('all_chat:', all_conversation)
        print('re:', res.text)
        sio.emit('client_response', {'result': all_conversation})


@sio.on('auto_send_mess')
def handle_auto_send_mess(data):
    '''server sẽ gửi id_fb đến client các máy, tại đây, câu lệnh check xem id_fb được gửi tới
    có trùng với id_fb đang đăng nhập trên máy hay không, nếu có thì thực hiện thao tác gửi
    tin nhắn bên dưới.'''
    fb_id = data["id_fb"]
    print('fb_id:', fb_id)
    print('id_fb:', id_fb)
    if fb_id == id_fb:
        id_chat = data["id_chat"]
        content = data["content"]
        print('data server send:', data)
        browser.get("https://www.facebook.com/messages/t/" + id_chat)
        time.sleep(random.uniform(4, 6))
        send_text = safe_find_element(browser, By.XPATH, "//div[@aria-label='Tin nhắn']")
        time.sleep(random.uniform(4, 6))
        send_text.click()
        send_text.send_keys(content)
        send_text.send_keys(Keys.ENTER)
        time.sleep(random.randint(2, 3))
        # gửi xong tin nhắn thì cập nhật cuộc trò chuyện mới gửi cho bên server, server sẽ gửi lại cho CRM.
        upload_conversation = safe_find_element(browser, By.XPATH, "//div[@aria-hidden='false' and @aria-label]")
        upload_conversation = upload_conversation.text
        sio.emit('client_response', {'result': upload_conversation})

if __name__ == "__main__":
    try:
        server_url = "http://127.0.0.1:5000"
        sio.connect(server_url)
        try:
            chrome_options = Options()
            prefs = {"profile.managed_default_content_settings.images": 2}
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            # chrome_options.add_argument("--window-position=-32000,-32000")
            service = webdriver.ChromeService(version_main=122)
            browser = webdriver.Chrome(service=service, options=chrome_options)
            # dang nhap tren fb
            browser.get("http://facebook.com")
            time.sleep(3)
            get_account = "http://43.239.223.143:8088/get_account"
            update_id = "http://43.239.223.143:8088/upload_excel"
            # response = requests.get(get_account)
            # result = json.loads(response.text)
            # print('result:', result)
            # user_name = result["data"]["item"]["user"]
            # pass_word = result["data"]["item"]["pass"]
            # code_2fa = result["data"]["item"]["code_2fa"]
            # id_chat = result["data"]["item"]["id_chat"]
            user_name = "0334388048"
            pass_word = "239210"
            code_2fa = ""
            id_chat = "12345"
            time_start = time.time()
            update_time = "http://43.239.223.143:8088/update_time"
            res = requests.post(update_time, data={"time": time_start, "id_chat": id_chat})
            login(user_name, pass_word, code_2fa)
            page_source = browser.page_source
            if '"userID":' in page_source:
                start = page_source.find('"userID":') + len('"userID":')
                end = page_source.find(',', start)
                id_fb = page_source[start:end]
                print('id_fb:', id_fb)
            time.sleep(random.uniform(4, 6))
            update_list_conversation()
            time.sleep(random.uniform(4, 6))
            while True:
                try:
                    surf_facebook(id_chat, titles[random.randint(0, len(titles) - 1)], browser)
                    time.sleep(random.uniform(2400, 3600))
                except Exception as err:
                    print('err:', err)
                    traceback.print_exc()
                    continue

        except Exception as err:
            print('Login Task Error:', err)
            traceback.print_exc()
        sio.wait()
        # socketio_thread.join()
        # login_thread.join()
    except Exception as err:
        print(err)
        pass


