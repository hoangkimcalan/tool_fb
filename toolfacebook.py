import asyncio
import random
import time
import traceback
import json
import os
import logging
import sys

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

CONTENT_POST = [
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
    "Công việc mơ ước của bạn không còn xa! Hãy nhanh chóng ứng tuyển vào vị trí mà chúng tôi đang tìm kiếm để phát triển bản thân trong môi trường năng động và thân thiện. Đừng bỏ lỡ cơ hội này, hãy ứng tuyển ngay hôm nay!",
    "Thời tiết hôm này thật thoải mái và dễ chịu, tâm trạng mình cũng rất tốt, cuối cùng mình cũng đạt được mục tiêu của mình. Tiếp tục cố gắng cho những điều tốt đẹp phía trước!"
]

# lưu cookie lại mỗi khi đăng nhập thành công
async def save_cookies(browser):
    """Lưu cookies vào file JSON"""
    cookies = browser.get_cookies()
    if cookies:
        # Lọc chỉ giữ cookie chưa hết hạn
        valid_cookies = [cookie for cookie in cookies if 'expiry' not in cookie or cookie['expiry'] > time.time()]
        
        with open(COOKIE_FILE, "w") as file:
            json.dump(valid_cookies, file, indent=4)

        log_message("Cookies saved successfully!")
    else:
        log_message("No cookies to save.", logging.ERROR)

# load cookie từ file JSON để tránh đăng nhập lại
async def load_cookies(browser):
    """Nạp cookies từ file JSON"""
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
        try:
            with open(COOKIE_FILE, "r") as file:
                cookies = json.load(file)
            
            # Lọc chỉ giữ cookie chưa hết hạn
            valid_cookies = [cookie for cookie in cookies if 'expiry' not in cookie or cookie['expiry'] > time.time()]
            
            if valid_cookies:
                for cookie in valid_cookies:
                    browser.add_cookie(cookie)

                # Nếu có cookie hết hạn, cập nhật lại file JSON
                if len(valid_cookies) < len(cookies):
                    with open(COOKIE_FILE, "w") as file:
                        json.dump(valid_cookies, file, indent=4)
                    log_message("Expired cookies removed and updated JSON file.")

                log_message("Valid cookies loaded successfully!")
            else:
                log_message("All cookies have expired. Deleting cookie file...", logging.WARNING)
                os.remove(COOKIE_FILE)

        except json.JSONDecodeError:
            log_message("Corrupted cookie file. Deleting...", logging.ERROR)
            os.remove(COOKIE_FILE)
    return False

# Hàm đăng nhập Facebook
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


#Hàm react_post
async def react_post(browser):
    """Chức năng thả reaction cho bài viết"""
    try:
        # 1. Tìm nút 'Like' ban đầu (Thích/Like)
        # Sử dụng WebDriverWait để chờ nút Like xuất hiện và có thể click được.
        like_button = None
        try:
            like_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Thích" or @aria-label="Like") and @role="button"]'))
            )
        except Exception:
            log_message("Không tìm thấy nút Thích/Like để tương tác.", logging.WARNING)
            return

        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
        await asyncio.sleep(2)

        selected_reaction = random.choice(REACTIONS)
        log_message(f"Selected reaction: {selected_reaction['name']}")

        # 2. Di chuột qua nút 'Like' để hiển thị các reaction options
        actions = ActionChains(browser)
        actions.move_to_element(like_button).perform()
        await asyncio.sleep(4)  # Đợi đủ thời gian cho các reaction options xuất hiện

        # 3. Tìm nút reaction cụ thể
        reaction_button = None
        # Xây dựng XPath cho nút reaction đã chọn.
        # Facebook có thể dùng aria-label chính xác hoặc aria-label có chứa số lượng người đã reaction.
        # Chúng ta sẽ thử cả hai trường hợp.
        
        # Thử XPath chính xác trước
        exact_xpath = selected_reaction['xpath']
        
        try:
            reaction_button = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.XPATH, exact_xpath))
            )
            log_message(f"Found reaction button with exact xpath for {selected_reaction['name']}")
        except Exception:
            log_message(f"Không tìm thấy reaction button chính xác cho '{selected_reaction['name']}'. Thử XPath chứa từ khóa.", logging.INFO)
            # Nếu không tìm thấy bằng XPath chính xác, thử tìm bằng aria-label chứa tên reaction
            # Ví dụ: "Yêu thích: 123 người"
            containing_xpath = f'//div[@role="button" and contains(@aria-label, "{selected_reaction["name"]}")]'
            try:
                reaction_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, containing_xpath))
                )
                log_message(f"Found reaction button with containing xpath for {selected_reaction['name']}")
            except Exception:
                log_message(f"Hoàn toàn không tìm thấy reaction button cho '{selected_reaction['name']}'.", logging.WARNING)
                traceback.print_exc() # In chi tiết lỗi để debug nếu cần
                return

        if not reaction_button:
            log_message(f"Không tìm thấy reaction button với aria-label='{selected_reaction['name']}' sau khi hover.", logging.WARNING)
            return

        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
        await asyncio.sleep(1)
        
        # 4. Click vào nút reaction
        actions.move_to_element(reaction_button)
        actions.click()
        actions.perform()
        log_message(f"Đã thả cảm xúc '{selected_reaction['name']}' thành công!")
        await asyncio.sleep(random.uniform(2, 3))

    except Exception as e:
        log_message(f"Lỗi trong hàm react_post: {e}", logging.ERROR)
        traceback.print_exc()
        pass
# Hàm bình luận bài viết
async def comment_post(browser, actions):
    try:
        await asyncio.sleep(random.uniform(2, 4))
        comment_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Viết bình luận" or @aria-label="Leave a comment") and @role="button"]')
        for btn in comment_buttons:
            if btn.is_displayed() and btn.is_enabled():
                comment_button = btn
                break
        if not comment_button:
            # Không tìm thấy nút bình luận, bỏ qua
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
        await asyncio.sleep(2)
        actions.send_keys_to_element(p_tag, comment_text)
        await asyncio.sleep(random.uniform(2, 4))
        actions.send_keys(Keys.ENTER)
        actions.perform()  
        await asyncio.sleep(2)
        actions.send_keys(Keys.ESCAPE).perform()
    except Exception as e:
        log_message(f"Error in comment_post: {e}", logging.ERROR)
        traceback.print_exc()

# Hàm chia sẻ bài viết
async def share_post(browser, actions):
    try:
        share_buttons = browser.find_elements(By.XPATH, '//div[(@aria-label="Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn." or @aria-label="Send this to friends or post it on your profile.") and @role="button"]')
        for btn in share_buttons:
            if btn.is_displayed() and btn.is_enabled():
                share_button = btn
                break
        if not share_button:
            return
        # Scroll nút chia sẻ vào view
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
        await asyncio.sleep(2)
        # Click vào nút chia sẻ
        actions.move_to_element(share_button)
        actions.click()
        actions.perform()

        await asyncio.sleep(5)
        # Tìm và click nút "Chia sẻ ngay"
        share_now_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Chia sẻ ngay" or @aria-label="Share now") and @role="button"]'))
        )
        actions.move_to_element(share_now_button)
        actions.click()
        actions.perform()
        log_message("Đã chia sẻ bài viết thành công!")
        await asyncio.sleep(random.uniform(2, 3))
    except Exception as e:
        log_message(f"Error in share_post: {e}", logging.ERROR)
        traceback.print_exc()

async def watch_videos(browser, actions):
    try:
        browser.get("https://www.facebook.com/watch/")
        await asyncio.sleep(random.uniform(3, 6))
        scroll_count_video = random.randint(6, 15)  # Số lần cuộn #fix
        while scroll_count_video > 0:
            log_message(f"scroll_count_watch_video {scroll_count_video}")

            await asyncio.sleep(random.uniform(4, 7))

            # Tìm tất cả video trên trang
            video_selected = browser.find_elements(By.XPATH, "//div[contains(@class, 'x1ey2m1c') and contains(@class, 'x9f619')]")

            # Lọc các video đang hiển thị
            visible_videos = [video for video in video_selected if video.is_displayed()]
            await asyncio.sleep(random.uniform(40, 60))

            if visible_videos:
                log_message(f"Found {len(visible_videos)} visible videos.")
                current_video = visible_videos[0]

                # Nếu scroll_count_video chia hết cho 7 hoặc 13 thì thực hiện hành động
                if scroll_count_video % 7 == 0 or scroll_count_video % 13 == 0:
                    if scroll_count_video % 7 == 0:
                        await asyncio.sleep(random.uniform(5, 7))
                        # Tìm nút like sử dụng selector đã được test thành công
                        like_buttons = browser.find_elements(By.XPATH, "//span[@data-ad-rendering-role='like_button']")
                        for btn in like_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                like_button = btn
                                break
                        if like_button:
                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
                            await asyncio.sleep(random.uniform(1, 3))
                            like_button.click()
                            log_message("Liked the post video successfully!")
                        else:
                            log_message("Like button is not visible, skipping...")

                    elif scroll_count_video % 13 == 0:
                        await share_post(browser, actions)
                        await asyncio.sleep(random.uniform(3, 5))
                        
                    await asyncio.sleep(random.uniform(2, 5))

                    # Sau khi like hoặc share, click vào video để lấy URL
                    actions.move_to_element(current_video).click().perform()
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Lấy URL video đã tương tác
                    video_url = browser.current_url
                    log_message(f"current_url: {video_url}")
            else:
                log_message("No visible videos found, continuing...")

            # Cuộn trang để xem video tiếp theo
            scroll_count_video -= 1

            # Thực hiện cuộn trang với hiệu ứng mượt mà
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 800)
            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))
                
        log_message("Đã hoàn thành xem video Facebook")
        
    except Exception as err:
        log_message(f"err watch videos {err}", logging.ERROR)
        traceback.print_exc()

# Hàm tạo bài viết mới
async def post_news_feed(browser):
    try:
        await asyncio.sleep(random.uniform(5, 8))
        actions = ActionChains(browser)
        # Tim kiếm nút Home
        home = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Home' or @aria-label='Trang chủ']"))
        )
        home.click()
        await asyncio.sleep(random.uniform(5, 8))
        # Tìm nút tạo bài viết mới (phải dùng @class)
        h3_post = browser.find_element(By.XPATH, "//div[@class='xi81zsa x1lkfr7t xkjl1po x1mzt3pk xh8yej3 x13faqbe']")
        h3_post.click()
        # Chờ cho hộp thoại tạo bài viết mới xuất hiện
        post_box = WebDriverWait(browser, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
        await asyncio.sleep(1)

        p_tag = post_box.find_element(By.TAG_NAME, "p")

        if(p_tag and p_tag.is_displayed()):
            await asyncio.sleep(2)
            actions.send_keys_to_element(p_tag, random.choice(CONTENT_POST))
            await asyncio.sleep(random.uniform(2, 4))
            actions.perform()
            await asyncio.sleep(2)
            # Tìm nút đăng bài viết
            try:
                post_new_button = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đăng']")
            except:
                post_new_button = browser.find_element(By.CSS_SELECTOR, "div[aria-label='Post']")
            await asyncio.sleep(2)
            post_new_button.click()
            log_message("Đã đăng bài viết thành công!")
        await asyncio.sleep(random.uniform(2, 4))
    except Exception as err:
        log_message(f"err post new feed {err}", logging.ERROR)
        traceback.print_exc()
        pass

# Hàm xem danh sách bạn bè + send message cho bạn bè (random)
async def list_friend(browser):
    try:
        list_friend = []
        browser.get("https://www.facebook.com/friends/list")
        await asyncio.sleep(random.uniform(2, 4))
        friends_box = browser.find_element(By.XPATH, "//div[@class='x135pmgq']")
        log_message(f"friends_box: {friends_box}")
        await asyncio.sleep(random.uniform(1, 3))
        # Có thể xóa debug log thẻ <a> nếu muốn gọn log
        friends_link = friends_box.find_elements(By.XPATH, ".//a[contains(@class, 'x1qjc9v5') and contains(@class, 'xjbqb8w') and contains(@class, 'xde0f50') and contains(@class, 'x1lliihq')]")

        for link in friends_link:
            link_friend = link.get_attribute('href')
            if link_friend:
                list_friend.append(link_friend)
        
        await asyncio.sleep(random.uniform(4, 6))
        log_message(f"list_friend: {list_friend}")
        if not list_friend:
            log_message("Không tìm thấy bạn bè nào trong danh sách!", logging.WARNING)
            return
        await send_message(browser, random.choice(list_friend), random.choice(CONTENT_POST))
        
        
    except Exception as err:
        log_message(f"err list_friend {err}", logging.ERROR)
        traceback.print_exc()
        pass

# Hàm nhắn tin cho một bạn
async def send_message(browser, link_user, content):
    try:
        browser.get(link_user)
        await asyncio.sleep(random.uniform(4, 6))
        actions = ActionChains(browser)
        try:
            send_button = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Nhắn tin"]')
        except:
            try:
                send_button = browser.find_element(By.CSS_SELECTOR, 'div[aria-label="Message"]')
            except:
                log_message("Không tìm thấy nút nhắn tin!", logging.ERROR)
                return
        send_button.click()
        await asyncio.sleep(random.uniform(2, 4))
        # Tìm ô nhập tin nhắn
        post_box = None
        try:
            post_box = WebDriverWait(browser, 12).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"))
            )
        except Exception as e:
            # Nếu không tìm thấy, thử lại
            try:
                post_box = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Nhắn tin'][contenteditable='true'][role='textbox']"))
                )
            except:
                post_box = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Message'][contenteditable='true'][role='textbox']"))
                )
        await asyncio.sleep(3)
        p_tag = post_box.find_element(By.TAG_NAME, "p")
        await asyncio.sleep(random.uniform(2, 4))
        if p_tag and p_tag.is_displayed():
            actions.send_keys_to_element(p_tag, content)
            await asyncio.sleep(random.uniform(2, 4))
            actions.send_keys(Keys.ENTER)
            actions.perform()
            await asyncio.sleep(2)
            log_message("Tin nhắn đã được gửi thành công!")
        await asyncio.sleep(2)
        actions.send_keys(Keys.ESCAPE).perform()
    except Exception as err:
        log_message(f"err send_message {err}", logging.ERROR)
        traceback.print_exc()

async def add_friend(browser):
    try:
        log_message("Bắt đầu quy trình thêm bạn bè.", logging.INFO)

        log_message("Tìm kiếm các nhóm tuyển dụng...", logging.INFO)
        browser.get("https://www.facebook.com/search/groups?q=tuyển%20dụng")
        await asyncio.sleep(random.uniform(3, 5))
        groups_box = browser.find_elements(By.XPATH, '//a[contains(@href, "/groups/") and @aria-hidden="true"]')
        group_links = [g.get_attribute("href") for g in groups_box if g.is_displayed() and g.get_attribute("href")]

        link_group = random.choice(group_links)

        members_url = link_group.rstrip("/") + "/members"
        browser.get(members_url)
        await asyncio.sleep(random.uniform(5, 8))

        for i in range(5):
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(random.uniform(2, 4))

        add_friend_buttons = browser.find_elements(
            By.XPATH,
            "//div[@role='button' and (starts-with(@aria-label, 'Kết bạn với ') or starts-with(@aria-label, 'Add Friend'))]"
        )

        profile_info_to_add = []
        for idx, btn in enumerate(add_friend_buttons):
            try:
                aria_label = btn.get_attribute('aria-label')
                user_name = ''
                if aria_label:
                    if aria_label.startswith('Kết bạn với '):
                        user_name = aria_label[len('Kết bạn với '):].strip()
                    elif aria_label.startswith('Add Friend'):
                        user_name = aria_label[len('Add Friend'):].strip()
                
                profile_link_element = None
                member_card_xpath = "./ancestor::div[contains(@class, 'x1ja2u2z')][1]"
                member_card = None
                member_card = btn.find_element(By.XPATH, member_card_xpath)
                if member_card:
                    # Tìm link profile trong member_card
                    xpath_profile_link = f".//a[@role='link' and (contains(., '{user_name}') or @aria-label='{user_name}') and (contains(@href, '/user/') or contains(@href, 'profile.php?id='))]"
                    try:
                        profile_link_element = member_card.find_element(By.XPATH, xpath_profile_link)
                    except Exception:
                        # Fallback nếu không tìm thấy bằng tên chính xác
                        xpath_profile_link = ".//a[@role='link' and (contains(@href, '/user/') or contains(@href, 'profile.php?id='))]"
                        try:
                            profile_link_element = member_card.find_element(By.XPATH, xpath_profile_link)
                        except Exception:
                            pass # Không tìm thấy link profile nào trong member_card này
                if profile_link_element:
                    link_user = profile_link_element.get_attribute('href')
                    if link_user and not link_user.startswith("http"):
                        link_user = "https://www.facebook.com" + link_user
                    
                    if link_user:
                        profile_info_to_add.append((link_user, user_name, btn))
                    else:
                        log_message(f"Liên kết profile rỗng sau khi tìm thấy phần tử cho '{user_name}'.", logging.WARNING)
                else:
                    log_message(f"Không tìm thấy phần tử liên kết profile nào cho '{user_name}'.", logging.WARNING)
            except Exception as e:
                log_message(f"Lỗi khi xử lý nút Kết bạn (chung): {e}", logging.ERROR)
                traceback.print_exc()
                continue

        if not profile_info_to_add:
            return

        link_user, user_name, add_btn = random.choice(profile_info_to_add)
        
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
        await asyncio.sleep(random.uniform(1, 2))
        
        try:
            add_btn.click()
            log_message(f"Đã gửi lời mời kết bạn thành công tới {user_name}!", logging.INFO)
        except Exception as click_err:
            log_message(f"Không thể click nút 'Kết bạn': {click_err}. Thử click bằng JavaScript.", logging.WARNING)
            browser.execute_script("arguments[0].click();", add_btn)
            log_message(f"Đã gửi lời mời kết bạn thành công tới {user_name} (qua JS click)!", logging.INFO)

        await asyncio.sleep(random.uniform(2, 4))
        await send_message(browser, link_user, "Chào bạn, mình là nhân sự bên timviec365, bạn cho mình hỏi là bạn đang đi tìm việc hay là bên tuyển dụng đó ạ? Nếu bạn đang cần tìm ứng viên hoặc đang cần tìm việc làm thì bạn lên trang web timviec365.vn tham khảo nhé.")

    except Exception as err:
        log_message(f"Lỗi tổng quát trong hàm add_friend: {err}", logging.ERROR)
        traceback.print_exc()
# hàm lướt dạo facebook
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
        await asyncio.sleep(random.uniform(3, 5))
        scroll_count = random.randint(14, 15)  # Số lần cuộn
        actions = ActionChains(browser)
        while scroll_count > 0:            
            # Cuộn từ từ (Mô phỏng cuộn chậm dần đều)
            current_scroll = browser.execute_script("return window.pageYOffset;")
            target_scroll = current_scroll + random.randint(600, 1000)

            await smooth_scroll(browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))            
            # Thoi gian dung lai de doc tin
            await asyncio.sleep(random.uniform(4, 6))

            if scroll_count % 13 == 0:
                # await comment_post(browser, actions)
                await asyncio.sleep(random.uniform(3, 5))
            elif scroll_count % 7 == 0:
                await react_post(browser)
                await asyncio.sleep(random.uniform(3, 5))

            scroll_count = scroll_count - 1

        await asyncio.sleep(random.uniform(2, 5))
        log_message("Đã hoàn thành lướt Facebook")

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
async def read_notification(browser):
    """Đọc thông báo mới trên Facebook"""

# **Hàm main() để chạy chương trình**
async def main(client_user_id_chat):
    browser = None
    try:
        # Kiểm tra tham số đầu vào
        if not client_user_id_chat:
            return
        initialize()
        #Lấy data từ file user_accounts.json
        account_data = None
        try:
            with open("user_accounts.json", "r", encoding="utf-8") as file:
                accounts = json.load(file)
                
                for acc in accounts:
                    acc_user_id = str(acc.get("user_id_chat")) # Đảm bảo cùng kiểu dữ liệu
                    log_message(f"Kiểm tra tài khoản: user_id_chat={acc_user_id}, note={acc.get('note', 'N/A')}", logging.DEBUG)
                    if acc_user_id == client_user_id_chat:
                        account_data = acc
                        break
        except FileNotFoundError:
            log_message("File user_accounts.json không tồn tại, chương trình sẽ dừng lại.", logging.ERROR)
            return
        except json.JSONDecodeError:
            log_message("File user_accounts.json bị hỏng, chương trình sẽ dừng lại.", logging.ERROR)
            return
        if not account_data:
            log_message(f"Tài khoản với user_id_chat '{client_user_id_chat}' không được tìm thấy trong user_accounts.json. Chương trình sẽ không chạy.", logging.ERROR)
            return
        facebook_username = account_data.get("facebook_username")
        facebook_password = account_data.get("facebook_password")
        facebook_2fa_code = account_data.get("facebook_2fa_code", "")
        if not facebook_username or not facebook_password:
            log_message("Thông tin đăng nhập Facebook không đầy đủ trong user_accounts.json. Chương trình sẽ dừng lại.", logging.ERROR)
            return
        
        log_message(f"Đang chạy tool cho tài khoản: {facebook_username} (User ID Chat: {client_user_id_chat})", logging.INFO)

        chrome_options = Options()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")

        # chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        screen_width = 1920  # Adjust this value based on your screen resolution
        screen_height = 1050  # Adjust this value based on your screen resolution
        chrome_options.add_argument(f"--window-position={screen_width // 2},0")
        chrome_options.add_argument(f"--window-size={screen_width // 2},{screen_height}")
        service = webdriver.ChromeService(version_main=122)
        browser = webdriver.Chrome(service=service, options=chrome_options)
        browser.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)
        # dang nhap tren fb
        actions = ActionChains(browser)
        browser.get("https://facebook.com")
        await asyncio.sleep(3)
        
        if os.path.exists(COOKIE_FILE):
            # load_cookies trả về True/False, nên có thể dùng trực tiếp
            if await load_cookies(browser):
                browser.refresh()
                await asyncio.sleep(4)
            else:
                log_message("Tải cookies thất bại hoặc không có cookies hợp lệ. Tiến hành đăng nhập mới.", logging.INFO)

        # Kiểm tra nếu vẫn cần đăng nhập
        if not await is_logged_in(browser):
            log_message("Cookies không hợp lệ hoặc hết hạn, cần đăng nhập lại.")
            # Hàm login gốc không trả về giá trị, giả định nó thành công nếu không có ngoại lệ
            await login(facebook_username, facebook_password, facebook_2fa_code, browser)
            # Sau khi login, kiểm tra lại trạng thái đăng nhập
            if not await is_logged_in(browser):
                log_message("Đăng nhập thất bại sau khi thử. Chương trình sẽ dừng lại.", logging.ERROR)
                return
            
        await asyncio.sleep(3)

        page_source = browser.page_source
        if '"userID":' in page_source:
            start = page_source.find('"userID":') + len('"userID":')
            end = page_source.find(',', start)
            id_fb = page_source[start:end]
            log_message(f'id_fb: {id_fb}')

        while True:
            try:    
                # surf_facebook gốc có 3 tham số, giữ nguyên để không thay đổi logic cũ
                await surf_facebook("", random.choice(COMMENTS), browser)
                await asyncio.sleep(random.uniform(2, 4))
                await watch_videos(browser, actions = ActionChains(browser))
                await post_news_feed(browser)
                await asyncio.sleep(random.uniform(2, 4))
                await list_friend(browser)
                await asyncio.sleep(random.uniform(2, 4))
                await add_friend(browser)
                await asyncio.sleep(random.uniform(200, 300))
            except Exception as err:
                log_message(f'err:{err}', logging.ERROR)
                traceback.print_exc()
                log_message("Có lỗi xảy ra, chương trình sẽ dừng lại.", logging.ERROR)
                break

    except Exception as err:
        traceback.print_exc()
    finally:
        if browser:
            try:
                browser.quit()
                log_message("Đã đóng browser.", logging.INFO)
            except:
                pass
        log_message("Chương trình đã kết thúc.", logging.INFO)


if __name__ == "__main__":
    # Lấy user_id_chat từ command line arguments
    if len(sys.argv) > 1:
        client_user_id_chat = sys.argv[1]
        print(f"Starting tool with user_id_chat: {client_user_id_chat}")
    else:
        print("Usage: python toolfacebook.py <user_id_chat>")
        sys.exit(1)
    
    asyncio.run(main(client_user_id_chat))