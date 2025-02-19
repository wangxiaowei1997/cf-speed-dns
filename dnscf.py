import requests
import traceback
import time
import os
import json

# API 密钥
CF_API_TOKEN = os.environ["CF_API_TOKEN"]
CF_ZONE_ID = os.environ["CF_ZONE_ID"]
CF_DNS_NAMES = os.environ["CF_DNS_NAMES"]


# pushplus_token
# PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}


def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
    return None


def get_dns_records(name):
    def_info = []
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['result']
        for record in records:
            if record['name'] == name:
                def_info.append(record['id'])
        return def_info
    else:
        print(f'Error fetching DNS records for {name}:', response.text)
        return []


def update_dns_record(record_id, name, cf_ip):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}'
    data = {
        'type': 'A',
        'name': name,
        'content': cf_ip
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            msg = f"成功更新 {name} 的DNS记录为 {cf_ip}"
            print(f"[SUCCESS] {msg} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return msg
        else:
            msg = f"更新 {name} 失败，状态码：{response.status_code}"
            print(f"[ERROR] {msg} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return msg
    except Exception as e:
        traceback.print_exc()
        msg = f"更新 {name} 时发生异常：{str(e)}"
        return msg


def push_plus(content):
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": 'PUSHPLUS_TOKEN',
        "title": "IP优选DNSCF推送",
        "content": content,
        "template": "markdown",
        "channel": "wechat"
    }
    try:
        response = requests.post(url, json=data)
        print(f"推送状态：{response.status_code}")
    except Exception as e:
        print(f"推送失败：{str(e)}")


def main():
    ip_addresses_str = get_cf_speed_test_ip()
    if not ip_addresses_str:
        print("无法获取优选IP地址")
        return

    ip_addresses = ip_addresses_str.split(',')
    cf_dns_list = [name.strip() for name in CF_DNS_NAMES.split(',')]
    results = []

    for dns_name in cf_dns_list:
        record_ids = get_dns_records(dns_name)
        if not record_ids:
            results.append(f"{dns_name}: 未找到DNS记录")
            continue

        min_length = min(len(record_ids), len(ip_addresses))
        for i in range(min_length):
            result = update_dns_record(record_ids[i], dns_name, ip_addresses[i])
            results.append(f"{dns_name}: {result}")

        if len(record_ids) < len(ip_addresses):
            results.append(f"{dns_name}: IP地址数量({len(ip_addresses)})多于DNS记录数量({len(record_ids)})")

    if results:
        print('success !')
        # push_plus("\n".join(results))


if __name__ == '__main__':
    main()