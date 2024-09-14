import requests
import socket
from bs4 import BeautifulSoup
import shodan

# Ваш API-ключ Shodan
SHODAN_API_KEY = '<>'

# Инициализация Shodan API
api = shodan.Shodan(SHODAN_API_KEY)

# Популярные порты для проверки
ports = [80, 443]

# Функция для получения IP-адресов и виртуальных хостов по запросу Shodan
def get_ips_and_hosts_from_shodan(query):
    try:
        results = api.search(query)
        ip_addresses = []
        virtual_hosts = set()
        for result in results['matches']:
            ip = result['ip_str']
            ip_addresses.append(ip)
            # Получение виртуальных хостов из заголовков, если они есть
            hostnames = result.get('hostnames', [])
            for hostname in hostnames:
                virtual_hosts.add(hostname)
        return ip_addresses, list(virtual_hosts)
    except shodan.APIError as e:
        print(f"Error fetching data from Shodan: {e}")
        return [], []

# Функция для проверки статуса виртуального хоста и получения заголовков
def check_status(ip, host):
    try:
        response = requests.get(
            f"http://{ip}",  # Можно использовать https:// при необходимости
            headers={"Host": host},
            timeout=5
        )
        content_length = response.headers.get('Content-Length', 'N/A')
        title = 'N/A'
        first_10_lines = 'N/A'

        # Проверка типа контента
        if 'text/html' in response.headers.get('Content-Type', ''):
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.title
                if title_tag:
                    title = title_tag.string.strip()
                
                # Извлечение первых 10 строк
                lines = response.text.splitlines()
                first_10_lines = '\n'.join(lines[:10])
            except Exception as e:
                print(f"Error parsing HTML for {host}: {e}")

        return {
            'status_code': response.status_code,
            'title': title,
            'content_length': content_length,
            'first_10_lines': first_10_lines
        }
    except requests.RequestException as e:
        return {
            'status_code': str(e),
            'title': 'N/A',
            'content_length': 'N/A',
            'first_10_lines': 'N/A'
        }

# Функция для проверки доступности порта
def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        try:
            s.connect((ip, port))
            return "Open"
        except socket.error:
            return "Closed"

# Функция для записи результатов в файл
def write_results_to_file(ip, host, status_info):
    filename = f"{ip}_{host}.txt"
    with open(filename, 'w') as f:
        f.write(f"IP Address: {ip}\n")
        f.write(f"Virtual Host: {host}\n")
        f.write(f"HTTP Status: {status_info['status_code']}\n")
        f.write(f"Title: {status_info['title']}\n")
        f.write(f"Content-Length: {status_info['content_length']}\n")
        f.write(f"First 10 Lines:\n{status_info['first_10_lines']}\n")
        f.write("\nPort Statuses:\n")
        for port in ports:
            port_status = check_port(ip, port)
            f.write(f"Port {port}: {port_status}\n")

# Получение IP-адресов и виртуальных хостов из Shodan
query = 'ssl:"temabit.com"'
ip_addresses, virtual_hosts = get_ips_and_hosts_from_shodan(query)

# Проверка статуса для каждого IP-адреса и виртуального хоста
for ip_address in ip_addresses:
    print(f"\nChecking IP Address: {ip_address}")
    
    for vhost in virtual_hosts:
        # Проверка HTTP статуса и получение заголовков
        status_info = check_status(ip_address, vhost)
        
        # Условие для вывода результатов и записи в файл
        if status_info['first_10_lines'] != 'N/A':
            print(f"Virtual Host: {vhost}, HTTP Status: {status_info['status_code']}, Title: {status_info['title']}, Content-Length: {status_info['content_length']}")
            print(f"First 10 Lines:\n{status_info['first_10_lines']}\n")
            
            # Запись результатов в файл
            write_results_to_file(ip_address, vhost, status_info)
