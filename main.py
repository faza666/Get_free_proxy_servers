import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import json
import time
import sys


def get_proxy(_url, output_json_file):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.binary_location = '/usr/local/bin/'
    driver = webdriver.Firefox(options=options)
    try:
        driver.get(_url)
        time.sleep(2)

        # Choose anonymous servers only:
        anonymity = driver.find_element(By.ID, 'xf1')
        anonymous = anonymity.find_elements(By.TAG_NAME, 'option')[1]
        anonymous.click()
        time.sleep(2)

        # Choose 500 servers on the page:
        list_length = driver.find_element(By.ID, 'xpp')
        option_500 = list_length.find_elements(By.TAG_NAME, 'option')[-1]
        option_500.click()
        time.sleep(5)

        content = driver.find_element(By.XPATH, '/html/body/table[2]/tbody/tr[4]/td/table/tbody')
        server_list = content.find_elements(By.TAG_NAME, 'tr')
        del server_list[:2]

        servers = []
        for each in server_list:
            server_info = {}
            info_list = each.find_elements(By.TAG_NAME, 'td')

            # There are some hidden elements on html page
            # to avoid them:
            if (len(info_list) < 10) or (info_list[2].text == 'NOA')\
                    or ('HTTPS' or 'SOCKS5') in info_list[1].text:
                continue

            server_info['Proxy address:port'] = info_list[0].text
            server_info['Proxy type'] = info_list[1].text
            server_info['Anonymity'] = info_list[2].text
            server_info['Country (city)'] = info_list[3].text
            server_info['Hostname/ORG'] = info_list[4].text
            server_info['Latency'] = info_list[5].text
            server_info['Speed'] = info_list[6].find_element(By.TAG_NAME, 'table').get_attribute('width')
            server_info['Uptime'] = info_list[8].text
            server_info['Check date (GMT+03)'] = info_list[9].text

            servers.append(server_info)

        print(f"there were found {len(servers)} servers:")

        with open(output_json_file, 'w') as file:
            file.write(json.dumps(servers))

    except Exception as _e:
        print(_e)
        servers = None
    finally:
        time.sleep(5)
        driver.quit()
    return servers


def check_proxy_response_time(server_list, output_json_file):
    with open(server_list, 'r') as file:
        json_str = file.read()

    proxy_list = json.loads(json_str)
    print(f"Checking servers and sorting the list..")
    for each in proxy_list:
        _proxy = each['Proxy address:port']
        start = time.time()
        response_time = None
        try:
            proxy = {
                'http': f"http://{_proxy}",
                'https': f"https://{_proxy}"
            }
            answer = requests.get(url="https://api.ipify.org", proxies=proxy, timeout=5)
            if not answer.status_code == 200:
                print(f"Server {_proxy} returns code: {answer.status_code}")
                proxy_list.remove(each)
                continue
            print(answer.text)
            end = time.time()
            response_time = round(end - start, 3)
            each["response_time"] = response_time
        except Exception as _e:
            print(f"Server {_proxy} returns Exception:\n\t{_e}")
            proxy_list.remove(each)

    sorted_list = sorted(proxy_list, key=lambda x: x['Latency'])
    print(len(sorted_list))
    with open(output_json_file, 'w') as file:
        file.write(json.dumps(sorted_list))

    return sorted_list


def push_output_proxy_settings(server_list, quantity=10):
    country_list = []
    with open('server_list.txt', 'w') as file:
        for server in server_list:
            if 'Russia' in server['Country (city)']:
                continue
            if server['Country (city)'] not in country_list:
                ip_address = (server['Proxy address:port']).split(':')[0]
                port = (server['Proxy address:port']).split(':')[1]
                file.write(f"{server['Proxy type'].lower()}\t{ip_address}\t{port}\n")
                country_list.append(server['Country (city)'])
            if len(country_list) == quantity:
                break


def main(_server_number):
    socks5_url = 'https://spys.one/en/socks-proxy-list/'
    https_url = 'https://spys.one/en/https-ssl-proxy/'
    free_proxy_url = 'https://spys.one/en/free-proxy-list/'
    # get_proxy(_url=socks5_url, output_json_file='servers.json')
    servers = check_proxy_response_time(server_list='servers.json', output_json_file='sorted_servers.json')
    push_output_proxy_settings(servers, quantity=_server_number)


if __name__ == '__main__':
    server_number = int(sys.argv[1])
    main(server_number)
