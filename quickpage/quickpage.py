# README https://github.com/nishizawatakamasa/quickpage/blob/main/README.md

import re
import unicodedata as ud
from playwright.async_api import Page, ElementHandle


class QuickPage:
    """Playwright の Page をラップした軽量ユーティリティクラス。"""

    def __init__(self, page: Page) -> None:
        self._page = page

    # ------------------------------------------------------------------ #
    # 要素取得
    # ------------------------------------------------------------------ #

    async def ss(
        self,
        selector: str,
        from_: ElementHandle | None = None,
    ) -> list[ElementHandle]:
        """
        CSSセレクタにマッチする全要素を返す。

        Args:
            selector: CSSセレクタ文字列。
            from_:    起点となる要素。None の場合はページ全体を対象とする。

        Returns:
            マッチした ElementHandle のリスト。0件の場合は空リスト。
        """
        if from_ is not None:
            return await from_.query_selector_all(selector)
        return await self._page.query_selector_all(selector)

    async def s(
        self,
        selector: str,
        from_: ElementHandle | None = None,
    ) -> ElementHandle | None:
        """
        CSSセレクタにマッチする最初の要素を返す。

        Args:
            selector: CSSセレクタ文字列。
            from_:    起点となる要素。None の場合はページ全体を対象とする。

        Returns:
            最初にマッチした ElementHandle。存在しない場合は None。
        """
        if from_ is not None:
            return await from_.query_selector(selector)
        return await self._page.query_selector(selector)

    async def ss_re(
        self,
        selector: str,
        pattern: str,
        from_: ElementHandle | None = None,
    ) -> list[ElementHandle]:
        """
        CSSセレクタと正規表現パターンの両方にマッチする全要素を返す。

        テキスト照合前に NFKC 正規化を行うため、全角・半角混在の
        日本語サイトでも安定して動作する。

        Args:
            selector: CSSセレクタ文字列。
            pattern:  textContent に対して適用する正規表現パターン。
            from_:    起点となる要素。None の場合はページ全体を対象とする。

        Returns:
            マッチした ElementHandle のリスト。0件の場合は空リスト。
        """
        elems = await self.ss(selector, from_)
        result = []
        for elem in elems:
            text = await self.attr("textContent", elem)
            if text and re.search(pattern, ud.normalize("NFKC", text)):
                result.append(elem)
        return result

    async def s_re(
        self,
        selector: str,
        pattern: str,
        from_: ElementHandle | None = None,
    ) -> ElementHandle | None:
        """
        CSSセレクタと正規表現パターンの両方にマッチする最初の要素を返す。

        テキスト照合前に NFKC 正規化を行うため、全角・半角混在の
        日本語サイトでも安定して動作する。

        Args:
            selector: CSSセレクタ文字列。
            pattern:  textContent に対して適用する正規表現パターン。
            from_:    起点となる要素。None の場合はページ全体を対象とする。

        Returns:
            最初にマッチした ElementHandle。存在しない場合は None。
        """
        elems = await self.ss_re(selector, pattern, from_)
        return elems[0] if elems else None

    async def next(self, elem: ElementHandle | None) -> ElementHandle | None:
        """
        指定要素の次の兄弟要素を返す。

        th の隣の td を取得するなど、セレクタだけでは辿りにくい
        兄弟関係のナビゲーションに使う。

        Args:
            elem: 起点となる要素。None の場合は None を返す。

        Returns:
            次の兄弟 ElementHandle。存在しない場合は None。
        """
        if elem is None:
            return None
        handle = await elem.evaluate_handle("el => el.nextElementSibling")
        return handle.as_element()

    # ------------------------------------------------------------------ #
    # 属性・テキスト取得
    # ------------------------------------------------------------------ #

    async def attr(
        self,
        attr_name: str,
        elem: ElementHandle | None,
    ) -> str | None:
        """
        要素から属性値またはテキストを取得し、前後の空白を除去して返す。

        textContent / innerText は JavaScript 経由で取得する。
        その他の属性（href, src, class 等）は get_attribute で取得する。
        elem が None の場合は None を返すため、s() の結果を直接渡せる。

        Args:
            attr_name: 取得する属性名。"textContent" / "innerText" も指定可。
            elem:      対象の ElementHandle。None の場合は None を返す。

        Returns:
            属性値の文字列（前後空白除去済み）。取得できない場合は None。
        """
        if elem is None:
            return None
        if attr_name in ("textContent", "innerText"):
            val: str | None = await elem.evaluate(f"el => el.{attr_name}")
        else:
            val = await elem.get_attribute(attr_name)
        return val.strip() if val else None

    # ------------------------------------------------------------------ #
    # ページ操作
    # ------------------------------------------------------------------ #

    async def go_to(self, url: str | None) -> bool:
        """
        指定 URL に遷移し、成否を bool で返す。

        ループ内で `if not await d.go_to(url): continue` と書けるよう
        例外を握り潰して False を返す設計にしている。
        None を渡した場合も安全に False を返す。

        Args:
            url: 遷移先 URL。None の場合は False を返す。

        Returns:
            遷移成功で True、失敗・例外・None で False。
        """
        if not url:
            return False
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            return False

    async def wait_for(
        self,
        selector: str,
        timeout: int = 5000,
    ) -> ElementHandle | None:
        """
        指定セレクタの要素が DOM に出現するまで待機して返す。

        動的に挿入される要素や、ページ遷移直後にまだ存在しない要素を
        確実に取得したいときに使う。タイムアウトした場合は None を返す。

        Args:
            selector: 待機対象の CSSセレクタ。
            timeout:  タイムアウトまでのミリ秒数（デフォルト: 5000ms）。

        Returns:
            出現した ElementHandle。タイムアウトした場合は None。
        """
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return await self._page.query_selector(selector)
        except Exception:
            return None

    async def block(self, *resource_types: str) -> None:
        """
        指定したリソース種別の読み込みをネットワークレベルでブロックする。

        ページ単位で設定する。画像・フォントをブロックするだけで
        ページ読み込みが大幅に高速化される。

        指定できる resource_types:
            "image", "font", "stylesheet", "media", "script" など

        Args:
            *resource_types: ブロックするリソース種別（複数指定可）。

        使い方:
            await d.block("image", "font")
        """
        blocked = set(resource_types)

        async def handler(route):
            if route.request.resource_type in blocked:
                await route.abort()
            else:
                await route.continue_()

        await self._page.route("**/*", handler)

    # ------------------------------------------------------------------ #
    # HTML取得
    # ------------------------------------------------------------------ #

    async def html(self) -> str:
        """
        現在のページのレンダリング済み HTML を返す。

        JavaScript 実行後の DOM を取得するため、SPA や動的サイトでも
        正しい HTML が得られる。ローカル解析用に保存する際の基本メソッド。

        Returns:
            <!DOCTYPE html> から始まる完全な HTML 文字列。
        """
        return await self._page.content()