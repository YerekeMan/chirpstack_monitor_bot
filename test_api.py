import os
import requests
from dotenv import load_dotenv

# Загружаем данные из твоего .env
load_dotenv()

API_KEY = os.getenv("CHIRPSTACK_API_KEY")
URL = os.getenv("CHIRPSTACK_URL")

# В ChirpStack v3 авторизация идет через этот заголовок
headers = {
    "Grpc-Metadata-Authorization": f"Bearer {API_KEY}"
}


def test_connection():
    # Эндпоинт для получения списка организаций
    endpoint = f"{URL}/api/organizations?limit=10"

    print(f"Пробую подключиться к: {endpoint}...")

    try:
        response = requests.get(endpoint, headers=headers, timeout=5)

        if response.status_code == 200:
            print("✅ Успех! Связь с ChirpStack установлена.")
            data = response.json()
            orgs = data.get('result', [])

            if orgs:
                print(f"Найдено организаций: {len(orgs)}")
                for org in orgs:
                    print(f" - ID: {org['id']}, Имя: {org['name']}")
            else:
                print("Организаций пока нет, но API ответил корректно.")

        elif response.status_code == 401:
            print("❌ Ошибка 401: Неверный API_KEY. Проверь его в ChirpStack.")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Не удалось подключиться: {e}")


if __name__ == "__main__":
    test_connection()