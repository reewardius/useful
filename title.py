import requests
import argparse
from bs4 import BeautifulSoup
import socket
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Функция для извлечения заголовка страницы
def get_title(url):
    try:
        # Проверка резолвинга домена
        hostname = url.split("//")[-1].split("/")[0]
        socket.gethostbyname(hostname)  # Если домен не резолвится, сайт пропускается

        # Выполняем HTTP-запрос с таймаутом 5 секунд
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            encoding = chardet.detect(response.content)['encoding']
            response.encoding = encoding if encoding else 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else None
            return url, title.strip() if title else None
        else:
            return url, None
    except (requests.exceptions.Timeout, requests.exceptions.RequestException, socket.gaierror) as e:
        print(f"Сайт {url} пропущен из-за ошибки: {str(e)}")
        return url, None
    except Exception as e:
        print(f"Неожиданная ошибка для сайта {url}: {str(e)}")
        return url, None


# Функция для обработки URL и вывода прогресса
def process_url(future, progress, total):
    try:
        result = future.result()
        progress[0] += 1
        print(f"Обработано {progress[0]}/{total} URL", end='\r')  # Прогресс
        return result
    except Exception as e:
        print(f"Ошибка в процессе выполнения задачи: {str(e)}")
        return None, None

def main():
    parser = argparse.ArgumentParser(description='Извлечение тега <title> из сайтов.')
    parser.add_argument('-l', '--list', type=str, required=True, help='Путь к файлу со списком сайтов')
    parser.add_argument('-o', '--output', type=str, required=False, help='Путь к файлу для сохранения результата')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Количество потоков для обработки запросов')
    args = parser.parse_args()

    try:
        with open(args.list, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Файл {args.list} не найден.")
        return

    total_urls = len(urls)
    progress = [0]  # Счетчик обработанных URL

    output_file = None
    if args.output:
        output_file = open(args.output, 'w', encoding='utf-8')

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(get_title, url): url for url in urls}
        for future in as_completed(futures):
            try:
                result = process_url(future, progress, total_urls)
                url, title = result
                if title:
                    result_str = f"{url}"
                    print(result_str)
                    if output_file:
                        output_file.write(result_str + '\n')
                        output_file.flush()  # Немедленная запись в файл
            except Exception as e:
                print(f"Ошибка при обработке: {str(e)}")

    if output_file:
        output_file.close()
        print(f"\nРезультаты сохранены в {args.output}")

if __name__ == "__main__":
    main()
