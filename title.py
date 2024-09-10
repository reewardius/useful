import requests
import argparse
from bs4 import BeautifulSoup
import socket
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_title(url):
    try:
        # Проверка резолвинга домена
        hostname = url.split("//")[-1].split("/")[0]  # Извлекаем hostname из URL
        socket.gethostbyname(hostname)  # Если домен не резолвится, будет выброшено исключение

        # Выполняем HTTP-запрос
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Определение кодировки
            encoding = chardet.detect(response.content)['encoding']
            response.encoding = encoding
            # Парсим HTML с помощью BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else None
            return url, title.strip() if title else None
        else:
            return url, None
    except (requests.exceptions.RequestException, socket.gaierror):
        return url, None

def main():
    parser = argparse.ArgumentParser(description='Извлечение тега <title> из сайтов.')
    parser.add_argument('-l', '--list', type=str, required=True, help='Путь к файлу со списком сайтов')
    parser.add_argument('-o', '--output', type=str, required=False, help='Путь к файлу для сохранения результата')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Количество потоков для обработки запросов')
    args = parser.parse_args()

    # Чтение списка сайтов из файла
    try:
        with open(args.list, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Файл {args.list} не найден.")
        return

    # Открываем файл на запись с кодировкой UTF-8, если указан флаг -o
    output_file = None
    if args.output:
        output_file = open(args.output, 'w', encoding='utf-8')

    # Создаем ThreadPoolExecutor для параллельной обработки URL
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        # Отправляем задачи на выполнение и собираем результаты
        futures = {executor.submit(get_title, url): url for url in urls}
        for future in as_completed(futures):
            url, title = future.result()
            if title:  # Если заголовок найден и сайт доступен
                result = f"{url}"
                print(result)
                if output_file:
                    output_file.write(result + '\n')
                    output_file.flush()  # Обеспечивает немедленную запись в файл

    if output_file:
        output_file.close()
        print(f"Результаты сохранены в {args.output}")

if __name__ == "__main__":
    main()
