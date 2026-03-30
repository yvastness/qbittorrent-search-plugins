# VERSION: 1.0
# AUTHORS: yinhaoyu

import re
import html as htmlmod
import urllib.parse
from helpers import retrieve_url, download_file
from novaprinter import prettyPrinter


def _decode(s):
    return htmlmod.unescape(htmlmod.unescape(s))


def _parse_size(text):
    m = re.search(r'([\d.]+)\s*(gb|mb|kb|tb|gib|mib|kib|tib)', text, re.I)
    if not m:
        return -1
    val  = float(m.group(1))
    unit = m.group(2).lower()
    mult = {"tb":1<<40,"tib":1<<40,"gb":1<<30,"gib":1<<30,
            "mb":1<<20,"mib":1<<20,"kb":1<<10,"kib":1<<10}
    return int(val * mult.get(unit, 1))


class projectjav(object):
    url = "https://projectjav.com"
    name = "ProjectJAV"
    supported_categories = {"all": "all"}

    def search(self, what, cat="all"):
        # ── 搜索页 → 第一个电影的详情 URL ────────────────────────────────
        keyword    = urllib.parse.quote_plus(what)
        search_url = f"{self.url}/?searchTerm={keyword}"
        try:
            search_html = retrieve_url(search_url)
        except Exception:
            return

        m = re.search(r'href=["\'](/movie/[^"\']+)["\']', search_html)
        if not m:
            return

        detail_path = m.group(1)
        desc_link   = self.url + detail_path

        # ── 详情页 ────────────────────────────────────────────────────────
        try:
            detail_html = retrieve_url(desc_link)
        except Exception:
            return

        # 电影标题
        t = re.search(r'<h1[^>]*>\s*([^<]{3,})', detail_html)
        if not t:
            t = re.search(r'<title>\s*([^<|–\-]{3,})', detail_html)
        movie_name = t.group(1).strip() if t else what

        # ── 找每个 magnet，截取后 800 字符提取元数据 ──────────────────────
        # 结构：<strong>Seeds</strong> 53  /  <strong>Leechs</strong> 11
        magnet_re = re.compile(r'href=["\']([^"\']*magnet:[^"\']+)["\']')

        for mag_m in magnet_re.finditer(detail_html):
            magnet = _decode(mag_m.group(1))
            after  = detail_html[mag_m.end(): mag_m.end() + 800]

            # size: <td>4.9gb</td>
            size = -1
            sm = re.search(r'<td>\s*([\d.]+\s*(?:gb|mb|kb|tb|gib|mib))\s*</td>', after, re.I)
            if sm:
                size = _parse_size(sm.group(1))

            # seeds: <strong>Seeds</strong> 53
            seeds = -1
            sm2 = re.search(r'<strong>Seeds</strong>\s*(\d+)', after)
            if sm2:
                seeds = int(sm2.group(1))

            # leech: <strong>Leechs</strong> 11
            leech = -1
            lm2 = re.search(r'<strong>Leechs</strong>\s*(\d+)', after)
            if lm2:
                leech = int(lm2.group(1))

            prettyPrinter({
                "link":       magnet,
                "name":       movie_name,
                "size":       str(size),
                "seeds":      seeds,
                "leech":      leech,
                "engine_url": self.url,
                "desc_link":  desc_link,
            })

    def download_torrent(self, info):
        if info.startswith("magnet:"):
            print(info)
            return
        print(download_file(info))
