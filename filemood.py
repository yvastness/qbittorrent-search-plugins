# VERSION: 1.0
# AUTHORS: yinhaoyu

try:
    from helpers import retrieve_url
except ImportError:
    pass

from urllib.parse import quote
import re
import novaprinter

class filemood:
    url = 'https://filemood.com/'
    name = 'FileMood'
    supported_categories = {'all': 'all'}

    def __findTorrents(self, html):
        torrents = []
        
        # 更精确地匹配只包含真实 torrent 的 table（必须有 dn-btn 和 dn-size）
        tables = re.findall(
            r'<table>.*?<td class="dn-btn">.*?<td class="dn-size">.*?</table>', 
            html, 
            re.DOTALL | re.IGNORECASE
        )

        for table in tables:
            # 跳过任何包含 "similar" 或 "Search for" 的块（安全过滤）
            if "similar" in table.lower() or "search for" in table.lower():
                continue

            # 提取 info_hash
            detail_match = re.search(r'href="(/[^"]+?-([a-f0-9]{40})\.html)"', table, re.IGNORECASE)
            if not detail_match:
                continue

            detail_path = detail_match.group(1)
            info_hash = detail_match.group(2).lower()

            # 标题
            title_match = re.search(r'title="([^"]+)"', table)
            title = title_match.group(1).strip() if title_match else f"Unknown_{info_hash[:8]}"

            # 大小
            size_match = re.search(r'<td class="dn-size">.*?<b>([^<]+)</b>', table, re.DOTALL | re.IGNORECASE)
            size = size_match.group(1).strip() if size_match else "0 MB"

            # Seeds / Leech
            status_match = re.search(r'<td class="dn-status">.*?<b>([^<]*)</b>', table, re.DOTALL | re.IGNORECASE)
            seeds = leech = "0"
            if status_match and '/' in status_match.group(1):
                parts = [p.strip() for p in status_match.group(1).split('/')]
                seeds = parts[0] or "0"
                leech = parts[1] or "0" if len(parts) > 1 else "0"

            # 构造 magnet
            dotted_name = re.sub(r'[\s/\\:]+', '.', title).strip('.')
            magnet_link = (
                f"magnet:?xt=urn:btih:{info_hash}"
                f"&dn={quote(dotted_name)}"
                "&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce"
                "&tr=udp%3A%2F%2Fopentrackr.org%3A1337%2Fannounce"
                "&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce"
            )

            desc_link = self.url.rstrip('/') + detail_path

            data = {
                'link': magnet_link,
                'name': title,
                'size': size,
                'seeds': seeds,
                'leech': leech,
                'engine_url': self.url,
                'desc_link': desc_link
            }
            torrents.append(data)

        print(f"[FileMood Debug] Found {len(torrents)} valid torrents (filtered suggestions)")
        return torrents

    def download_torrent(self, info):
        print(info)

    def search(self, what, cat='all'):
        what = what.replace(' ', '+').strip()
        current_page = 0

        while current_page < 3:
            try:
                search_url = f"{self.url}result?q={what}+in%3Atitle&f={current_page * 20}"
                html = retrieve_url(search_url)
                html = re.sub(r'\s+', ' ', html)

                results = self.__findTorrents(html)

                for data in results:
                    novaprinter.prettyPrinter(data)

                if len(results) == 0 and current_page > 0:
                    break
                current_page += 1
            except Exception as e:
                print(f"[FileMood Error] {e}")
                break
