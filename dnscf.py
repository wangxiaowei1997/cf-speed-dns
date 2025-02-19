import requests
import traceback
import time
import os
import json

# API 密钥
CF_API_TOKEN = os.environ["CF_API_TOKEN"]
CF_ZONE_ID = os.environ["CF_ZONE_ID"]
CF_DNS_NAMES = os.environ["CF_DNS_NAMES"]


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
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [record['id'] for record in response.json()['result'] if record['name'] == name]
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
            return f"成功更新 {name} → {cf_ip}"
        return f"更新 {name} 失败，状态码：{response.status_code}"
    except Exception as e:
        traceback.print_exc()
        return f"更新 {name} 异常：{str(e)}"




def main():
    ip_addresses_str = get_cf_speed_test_ip()
    if not ip_addresses_str:
        print("无法获取优选IP地址")
        return

    ip_addresses = ip_addresses_str.split(',')
    domain_records = {}
    total_required = 0

    # 获取所有域名的DNS记录并计算总需求
    cf_dns_names_list = [name.strip() for name in CF_DNS_NAMES.split(',')]
    for domain in cf_dns_names_list:
        records = get_dns_records(domain)
        if not records:
            print(f"跳过 {domain}（无DNS记录）")
            continue
        domain_records[domain] = records
        total_required += len(records)

    # 检查IP数量是否足够
    if len(ip_addresses) < total_required:
        msg = f"需要 {total_required} 个IP，但只获取到 {len(ip_addresses)} 个"
        print(msg)
        return

    # 分配IP并更新记录
    ip_cursor = 0
    results = []
    for domain, records in domain_records.items():
        required = len(records)
        assigned_ips = ip_addresses[ip_cursor: ip_cursor + required]
        ip_cursor += required

        for i, record_id in enumerate(records):
            result = update_dns_record(record_id, domain, assigned_ips[i])
            results.append(f"{domain}：{result}")

    if results:
        print("\n".join(results))


if __name__ == '__main__':
    main()