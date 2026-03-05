# quickpage

## Overview - 概要
QuickPage is a wrapper for Playwright. By controlling the Page object through QuickPage, you can easily implement processes such as browser automation and scraping.

quickpageはPlaywrightのラッパーです。QuickPageを介してPageオブジェクトを操作することで、ブラウザの自動操作、スクレイピングなどの処理を簡単に実装できます。

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

## Requirements - 必要条件
To run quickpage, you need the following environment:

quickpageの実行には、以下の環境が必要です。

* Python 3.10 or higher
* Libraries:
    * playwright (version 1.49.0 or higher)
* Browser binaries (install separately / 別途インストールが必要):
    * `playwright install chromium`

## Basic Usage - 基本的な使い方
### QuickPage Class
The quickpage module consists of a single class: QuickPage. This class wraps a Playwright Page instance, providing convenient methods for interacting with web pages.

quickpageモジュールは、QuickPageクラス1つによって構成されています。QuickPageクラスは、PlaywrightのPageインスタンスを受け取り、操作をラップします。

```py
p = QuickPage(page)
```

### Recommended setup - 推奨セットアップ

スクレイピングのロジックは `scrape(page)` 関数にまとめ、ブラウザの起動・終了は `main()` に分離するパターンを推奨します。

```py
import os
import asyncio
import random
import pandas as pd
from playwright.async_api import async_playwright, Page
from quickpage import QuickPage

CSV_PATH = 'classroom_info.csv'


async def scrape(page: Page) -> None:
    p = QuickPage(page)
    await p.block('image', 'font')

    # 都道府県URLを収集
    await p.go_to('https://www.foobarbaz1.jp')
    pref_urls = [await p.attr('href', e) for e in await p.ss('li.item > ul > li > a')]

    # 教室URLを収集
    classroom_urls = []
    for i, url in enumerate(pref_urls, 1):
        print(f'{i}/{len(pref_urls)} pref_urls')
        if not await p.go_to(url):
            continue
        await asyncio.sleep(random.uniform(1, 2))
        links = [await p.attr('href', e) for e in await p.ss('.school-area h4 a')]
        classroom_urls.extend(links)

    # 教室情報を取得してCSVに追記
    for i, url in enumerate(classroom_urls, 1):
        print(f'{i}/{len(classroom_urls)} classroom_urls')
        if not await p.go_to(url):
            continue
        await asyncio.sleep(random.uniform(1, 2))
        row = {
            'URL': page.url,
            '教室名': await p.attr('textContent', await p.s('h1 .text01')),
            '住所': await p.attr('innerText', await p.s('.item .mapText')),
            '電話番号': await p.attr('textContent', await p.s('.item .phoneNumber')),
            'HP': await p.attr('href', await p.s('a', await p.next(await p.s_re('th', 'ホームページ')))),
        }
        pd.DataFrame([row]).to_csv(
            CSV_PATH,
            mode='a',
            index=False,
            header=not os.path.exists(CSV_PATH),
            encoding='utf-8-sig',
        )


async def main() -> None:
    async with async_playwright() as pw:
        async with await pw.chromium.launch(headless=False) as browser:
            async with await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
            ) as context:
                page = await context.new_page()
                await scrape(page)

asyncio.run(main())
```

### Methods
The QuickPage class provides the following instance methods:

QuickPageクラスは、以下のインスタンスメソッドによって構成されています。

* Get elements - 要素を取得
    * [ss](#ss)
    * [s](#s)
    * [ss_re](#ss_re)
    * [s_re](#s_re)
    * [next](#next)
    * [wait_for](#wait_for)
* Get attribute value - 属性値を取得
    * [attr](#attr)
* Operate browser - ブラウザを操作
    * [go_to](#go_to)
    * [block](#block)
* Get HTML - HTMLを取得
    * [html](#html)

---

<a id="ss"></a>
#### 1. ss
Get multiple elements as a list using a CSS selector. Returns an empty list if no elements are found. If an ElementHandle is passed as the second argument, the search is performed within that element's DOM subtree.

CSSセレクタで複数の要素をリストで取得します。存在しない場合は空のリストを返します。第二引数にElementHandleを渡すと、その要素のDOMサブツリーからの取得となります。
```py
elems = await p.ss('li.item > ul > li > a')
```

---

<a id="s"></a>
#### 2. s
Get a single element using a CSS selector. If more than one element satisfies the condition, only the first one is returned. Returns None if no element is found. If an ElementHandle is passed as the second argument, the search is performed within that element's DOM subtree.

CSSセレクタで要素を取得します。条件を満たす要素が複数ある場合、最初の一つだけが返されます。存在しない場合はNoneを返します。第二引数にElementHandleを渡すと、その要素のDOMサブツリーからの取得となります。
```py
elem = await p.s('h1 .text01')
```

---

<a id="ss_re"></a>
#### 3. ss_re
Get multiple elements as a list using a CSS selector and a regular expression to match the element's textContent. NFKC normalization is applied before matching, ensuring stable behavior on Japanese sites with mixed full-width and half-width characters. Returns an empty list if no elements are found. If an ElementHandle is passed as the third argument, the search is performed within that element's DOM subtree.

CSSセレクタと、textContentに対する正規表現マッチングで複数の要素をリストで取得します。照合前にNFKC正規化を行うため、全角・半角混在の日本語サイトでも安定して動作します。存在しない場合は空のリストを返します。第三引数にElementHandleを渡すと、その要素のDOMサブツリーからの取得となります。
```py
elems = await p.ss_re('li.item > ul > li > a', r'店\s*舗')
```

---

<a id="s_re"></a>
#### 4. s_re
Get a single element using a CSS selector and a regular expression to match the element's textContent. NFKC normalization is applied before matching. If more than one element satisfies the condition, only the first one is returned. Returns None if no element is found. If an ElementHandle is passed as the third argument, the search is performed within that element's DOM subtree.

CSSセレクタと、textContentに対する正規表現マッチングで要素を取得します。照合前にNFKC正規化を行います。条件を満たす要素が複数ある場合、最初の一つだけが返されます。存在しない場合はNoneを返します。第三引数にElementHandleを渡すと、その要素のDOMサブツリーからの取得となります。
```py
elem = await p.s_re('table tbody tr th', r'住\s*所')
```

---

<a id="next"></a>
#### 5. next
Get the next sibling element of a given element. Useful for navigating sibling relationships that are difficult to express with CSS selectors alone, such as retrieving the `td` next to a `th`.

渡された要素の次の兄弟要素を取得します。`th` の隣の `td` を取得するなど、CSSセレクタだけでは辿りにくい兄弟関係のナビゲーションに使います。
```py
next_elem = await p.next(elem)
```

---

<a id="wait_for"></a>
#### 6. wait_for
Wait until the element matching the selector appears in the DOM, then return it. Useful for reliably retrieving elements that are dynamically inserted or not yet present immediately after page navigation. Returns None on timeout.

指定セレクタの要素がDOMに出現するまで待機して返します。動的に挿入される要素や、ページ遷移直後にまだ存在しない要素を確実に取得したいときに使います。タイムアウトした場合はNoneを返します。
```py
elem = await p.wait_for('.dynamic-content')
elem = await p.wait_for('.slow-element', timeout=10000)  # 10秒
```

---

<a id="attr"></a>
#### 7. attr
Get the value of an attribute or text from an element, with leading and trailing whitespace stripped. `textContent` and `innerText` are retrieved via JavaScript. Other attributes such as `href` and `src` are retrieved via `get_attribute`. Safely returns None if elem is None, so the result of `s()` can be passed directly.

要素から属性値またはテキストを取得し、前後の空白を除去して返します。`textContent` / `innerText` はJavaScript経由で取得します。`href`、`src` などその他の属性は `get_attribute` で取得します。`elem` が None の場合は安全に None を返すため、`s()` の結果を直接渡せます。
```py
text = await p.attr('textContent', elem)
href = await p.attr('href', elem)
```

---

<a id="go_to"></a>
#### 8. go_to
Navigate to the specified URL and return True if successful. Returns False on exception or if None is passed. Designed to suppress exceptions and return False, enabling the pattern `if not await p.go_to(url): continue` inside loops.

指定URLに遷移し、成否をboolで返します。例外発生時やNoneを渡した場合はFalseを返します。例外を握り潰してFalseを返す設計により、ループ内で `if not await p.go_to(url): continue` と書けます。
```py
if not await p.go_to('https://example.com'):
    continue
```

---

<a id="block"></a>
#### 9. block
Block loading of specified resource types at the network level. Blocking images and fonts alone can significantly speed up page loading. Multiple resource types can be specified.

指定したリソース種別の読み込みをネットワークレベルでブロックします。画像・フォントをブロックするだけでページ読み込みが大幅に高速化されます。複数のリソース種別を指定できます。

Available resource types: `"image"`, `"font"`, `"stylesheet"`, `"media"`, `"script"` etc.
```py
await p.block('image', 'font')
```

---

<a id="html"></a>
#### 10. html
Return the fully rendered HTML of the current page. Since it retrieves the DOM after JavaScript execution, correct HTML is obtained even for SPAs and dynamic sites.

現在のページのレンダリング済みHTMLを返します。JavaScript実行後のDOMを取得するため、SPAや動的サイトでも正しいHTMLが得られます。
```py
html = await p.html()
```

## License - ライセンス
[MIT](./LICENSE)