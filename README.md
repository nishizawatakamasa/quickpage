# quickpage

## Overview - 概要

QuickPage is a wrapper for Playwright.

quickpageはPlaywrightのラッパーです。


## Requirements - 必要条件

To run quickpage, you need the following environment:

quickpageの実行には、以下の環境が必要です。

- Python 3.10 or higher
- Libraries:
  - playwright (version 1.49.0 or higher)
- Browser binaries (install separately / 別途インストールが必要):


## Installation - インストール

You can install quickpage and all required dependencies from PyPI:

quickpageとその実行に必要なライブラリは以下でインストールできます。

### pip

```
pip install quickpage
```

### uv (recommended)

```
uv add quickpage
```

After installation, you need to install the browser binary separately:

インストール後、ブラウザのバイナリを別途インストールする必要があります。

### pip

```
python -m playwright install chromium
```

### uv

```
uv run playwright install chromium
```


## Basic Usage - 基本的な使い方
```py
import random
import time
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright, Page
from quickpage import QuickPage

BASE_DIR = Path(__file__).parent

CSV_PATH = BASE_DIR / 'classroom_info.csv'

def scrape(page: Page) -> None:
    p = QuickPage(page)

    p.goto('https://www.foobarbaz1.jp')
    pref_urls = [p.attr('href', e) for e in p.ss('li.item > ul > li > a')]

    classroom_urls = []
    for i, url in enumerate(pref_urls, 1):
        print(f'{i}/{len(pref_urls)} pref_urls')
        if not p.goto(url):
            continue
        time.sleep(random.uniform(1, 2))
        links = [p.attr('href', e) for e in p.ss('.school-area h4 a')]
        classroom_urls.extend(links)

    for i, url in enumerate(classroom_urls, 1):
        print(f'{i}/{len(classroom_urls)} classroom_urls')
        if not p.goto(url):
            continue
        time.sleep(random.uniform(1, 2))
        row = {
            'URL': page.url,
            '教室名': p.text_c(p.s('h1 .text01')),
            '住所': p.i_text(p.s('.item .mapText')),
            '電話番号': p.text_c(p.s('.item .phoneNumber')),
            'HP': p.attr('href', p.s_in('a', p.next(p.s_re('th', 'ホームページ')))),
        }
        pd.DataFrame([row]).to_csv(
            CSV_PATH,
            mode='a',
            index=False,
            header=not CSV_PATH.exists(),
            encoding='utf-8-sig',
        )


def main() -> None:
    with sync_playwright() as pw:
        with pw.chromium.launch(headless=False, channel="chrome") as browser:
            with browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                # ChromeのUser-Agentは chrome://version で確認できる。それをそのままコピーして使うのが一番自然。
                user_agent='Mozilla/5.0 ...',
                extra_http_headers={'Accept-Language': 'ja-JP,ja;q=0.9'}
            ) as context:
                page = context.new_page()
                page.set_default_timeout(15000) 
                blocked = {'image', 'font', 'media'}
                def handler(route):
                    if route.request.resource_type in blocked:
                        route.abort()
                    else:
                        route.continue_()
                page.route('**/*', handler)
                scrape(page)

if __name__ == '__main__':
    main()
```

## License - ライセンス

[MIT](./LICENSE)
