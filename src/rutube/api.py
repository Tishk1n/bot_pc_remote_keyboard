import requests

class RutubeAPI:
    def __init__(self):
        self.base_url = "https://rutube.ru/api"
        self.session = requests.Session()

    def search_anime(self, query):
        search_url = f"{self.base_url}/search/video/"
        params = {
            "query": query,
            "genre": "anime",
            "limit": 10
        }
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException as e:
            print(f"Ошибка поиска: {e}")
            return []

    def get_video_info(self, video_id):
        video_url = f"{self.base_url}/video/{video_id}/"
        try:
            response = self.session.get(video_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка получения информации о видео: {e}")
            return None