from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
import time


# 运行环境需要安装chrome, 然后查看chrome版本，再去下载对应版本的驱动
# 下载地址：https://sites.google.com/a/chromium.org/chromedriver/downloads
# 下载完毕后将驱动文件放在项目根目录下
class LiveMonitor(object):
    def __init__(self, os_type="win"):
        option = webdriver.ChromeOptions()
        option.add_argument('headless')
        option.add_argument('blink-settings=imagesEnabled=false')
        option.add_argument('--disable-dev-shm-usage')
        # 加载selenium,win/linux/mac对应的驱动不一样
        if os_type == "win":
            self.driver = webdriver.Chrome("chromedriver.exe", options=option)
        if os_type == "linux":
            self.driver = webdriver.Chrome("chromedriver", options=option)
        if os_type == "mac":
            raise BaseException

    # 获取正在进行的直播列表
    # 返回一个list，item格式为（标题, 直播地址（为子地址，下同））
    # 示例：('Focus, Meditation, Concentration ......', '/watch?v=NYrhBvSXUXY')
    # 无直播时返回空list
    def live_check(self, url):
        bs_object = self._live_check(url)  # 获取正在进行的live列表的BeautifulSoup对象，没有时返回None
        live_list = self._process_live(bs_object)  # 解析出正在进行的live
        return live_list

    # 获取即将进行的直播列表
    # 返回一个list，item格式为（标题, 直播地址, 开始时间（unix时间戳））
    # 示例：('CHATTING ROOM【ふりーちゃっと】', '/watch?v=WinQpGPnSdI', 1632056400.0)
    # 无直播时返回空list
    def upcoming_live_check(self, url):
        bs_object = self._upcoming_live_check(url)
        live_list = self._upcoming_pre_live(bs_object, threshold=10)
        return live_list

    def _live_check(self, channel_url):
        self.driver.get(channel_url)
        live_xpath_str = "//*[@id='contents' and @class='style-scope ytd-channel-featured-content-renderer']"
        try:
            t = self.driver.find_element_by_xpath(live_xpath_str)
        except selenium.common.exceptions.NoSuchElementException:
            return None
        return t.get_attribute('innerHTML')  # 返回直播单元的html

    def _process_live(self, html):
        live_list = []
        if html is None:
            return live_list
        bs_object = BeautifulSoup(html, features="html.parser")
        bsl = bs_object.find_all("a", id="video-title")
        for b in bsl:
            live_list.append((b["aria-label"], b["href"]))
        return live_list

    def _upcoming_live_check(self, channel_url):
        # 跳转到预订直播页面，如果没有预订直播，这里会加载出该频道的所有的视频，后续通过这个项目下的条目数判断是否有预订直播
        self.driver.get(channel_url + "/videos?view=2&sort=dd&live_view=502&shelf_id=3")
        live_xpath_str = "//*[@id='items' and @class='style-scope ytd-grid-renderer']"
        try:
            t = self.driver.find_element_by_xpath(live_xpath_str)
        except selenium.common.exceptions.NoSuchElementException:
            return None
        return t.get_attribute('innerHTML')  # 返回直播单元的html

    # threshold：判断是否为加载了整个频道的视频的阙值
    def _upcoming_pre_live(self, html, threshold=10):
        pre_live_list = []
        # 如果没有捕捉到对象则返回空列表
        if html is None:
            return pre_live_list
        bs_object = BeautifulSoup(html, features="html.parser")
        bsl = bs_object.find_all("div", id="meta")
        # 如果加载出了所有的视频则没有预订直播，返回空列表,有一个判断阈值设定
        if len(bsl) > threshold:
            return pre_live_list
        for b in bsl:
            title = b.find_all("a", id="video-title")[0]["title"]
            link = b.find_all("a", id="video-title")[0]["href"]
            date = b.find_all("div", id="metadata-line")[0]
            date = (date.contents[1].string)  # "Scheduled for 19/09/2021, 21:00"
            if "Scheduled" in date:  # 英文网页
                date = " ".join(date.split(" ")[-2:])
                timeArray = time.strptime(date, "%d/%m/%Y, %H:%M")
            else:
                date = date.split("：")[-1]
                timeArray = time.strptime(date, "%Y/%m/%d %H:%M")
            unit_time = time.mktime(timeArray)
            pre_live_list.append((title, link, unit_time))
        return pre_live_list


if __name__ == '__main__':

    live_test_url = "https://www.youtube.com/c/YellowBrickCinema"
    coco_trl = "https://www.youtube.com/channel/UCS9uQI-jC3DE0L4IpXyvr6w"

    lm = LiveMonitor(os_type="win")

    # 检查正在进行的直播
    print(lm.live_check(live_test_url))
    print(lm.live_check(coco_trl))
    # 检查即将进行的直播
    print(lm.upcoming_live_check(live_test_url))
    print(lm.upcoming_live_check(coco_trl))

    # 内存占用检查
    for i in range(1000):
        time.sleep(1)
        lm.live_check(live_test_url)