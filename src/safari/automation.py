from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class SafariAutomation:
    def __init__(self):
        self.driver = webdriver.Safari()

    def open_rutube(self):
        self.driver.get("https://rutube.ru")
        time.sleep(3)  # Wait for the page to load

    def play_anime(self, anime_url):
        self.driver.get(anime_url)
        time.sleep(3)  # Wait for the anime page to load
        self.driver.fullscreen_window()  # Open in fullscreen mode
        play_button = self.driver.find_element(By.CLASS_NAME, "play-button")  # Adjust selector as needed
        play_button.click()

    def pause_anime(self):
        pause_button = self.driver.find_element(By.CLASS_NAME, "pause-button")  # Adjust selector as needed
        pause_button.click()

    def resume_anime(self):
        play_button = self.driver.find_element(By.CLASS_NAME, "play-button")  # Adjust selector as needed
        play_button.click()

    def rewind_anime(self, seconds=10):
        rewind_button = self.driver.find_element(By.CLASS_NAME, "rewind-button")  # Adjust selector as needed
        for _ in range(seconds // 10):
            rewind_button.click()
            time.sleep(1)

    def forward_anime(self, seconds=10):
        forward_button = self.driver.find_element(By.CLASS_NAME, "forward-button")  # Adjust selector as needed
        for _ in range(seconds // 10):
            forward_button.click()
            time.sleep(1)

    def close_browser(self):
        self.driver.quit()