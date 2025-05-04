import webbrowser

class BrowserController:
    def __init__(self):
        # Используем Safari как браузер по умолчанию для macOS
        self.browser = webbrowser.get('safari')
        
    def open_url(self, url):
        """Открывает URL в браузере"""
        self.browser.open(url, new=2)  # new=2 открывает в новой вкладке
