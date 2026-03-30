# VERSION: 1.0
# AUTHORS: yinhaoyu

import urllib.parse
import urllib.request
import re
import math
import time
import gzip
from io import BytesIO
from novaprinter import prettyPrinter


class btdig(object):
    url = 'https://www.btdig.com'
    name = 'btdig'
    supported_categories = {'all': '0'}

    def search(self, what, cat='all'):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
            'Accept-Encoding': 'gzip, deflate, br',
        }

        encoded = urllib.parse.quote(what)
        base_url = f"{self.url}/search?q={encoded}&order=0"

        response = self.get_response(base_url, headers)

        # 计算页数
        results_match = re.search(r'(\d+)\s+results? found', response, re.IGNORECASE)
        total_pages = min(math.ceil(int(results_match.group(1)) / 10), 8) if results_match else 5

        self.parse_page(response)

        for p in range(1, total_pages):
            time.sleep(1.3)
            url = f"{self.url}/search?q={encoded}&p={p}&order=0"
            response = self.get_response(url, headers)
            if response:
                self.parse_page(response)

    def get_response(self, url, headers):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                if resp.info().get('Content-Encoding') == 'gzip':
                    data = gzip.GzipFile(fileobj=BytesIO(data)).read()
                return data.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    def parse_page(self, html):
        if not html or len(html) < 1000:
            return

        # 更稳定的 block 匹配
        blocks = re.finditer(r'<div class="one_result".*?(?=<div class="one_result"|$)', html, re.DOTALL)

        for block in blocks:
            content = block.group(0)

            magnet_match = re.search(r'href="(magnet:\?xt=urn:btih:[^"]+)"', content, re.IGNORECASE)
            name_match = re.search(r'<div class="torrent_name".*?><a[^>]*>(.*?)</a>', content, re.DOTALL | re.IGNORECASE)
            size_match = re.search(r'<span class="torrent_size"[^>]*>(.*?)</span>', content, re.IGNORECASE)

            if magnet_match and name_match and size_match:
                name_raw = name_match.group(1)
                name = re.sub(r'<b[^>]*>|</b>', '', name_raw, flags=re.IGNORECASE).strip()

                # 关键修正：确保 size 是 "数字 单位" 格式
                size_raw = size_match.group(1).strip().replace('&nbsp;', ' ')
                # 如果原本是 "5GB" → 改成 "5 GB"
                size_str = re.sub(r'(\d+\.?\d*)\s*([KMGTPE]B)', r'\1 \2', size_raw)

                result = {
                    'link': magnet_match.group(1),
                    'name': name,
                    'size': size_str,
                    'desc_link': '',
                    'engine_url': self.url,
                    'seeds': '-1',
                    'leech': '-1'
                }
                prettyPrinter(result)


# 用来直接测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        btdig().search(sys.argv[1])
