# README https://github.com/nishizawatakamasa/quickpage/blob/main/README.md

import re
import unicodedata as ud
from playwright.sync_api import Page, ElementHandle


class QuickPage:
    def __init__(self, page: Page) -> None:
        self._page = page

    def first(self, elems: list[ElementHandle]) -> ElementHandle | None:
        return elems[0] if elems else None

    def re_filter(self, pattern: str, elems: list[ElementHandle]) -> list[ElementHandle]:
        return [elem for elem in elems if (text := self.text_c(elem)) is not None and re.search(pattern, ud.normalize("NFKC", text))]

    def ss(self, selector: str) -> list[ElementHandle]:
        return self._page.query_selector_all(selector)

    def s(self, selector: str) -> ElementHandle | None:
        return self.first(self.ss(selector))

    def ss_re(self, selector: str, pattern: str) -> list[ElementHandle]:
        return self.re_filter(pattern, self.ss(selector))

    def s_re(self, selector: str, pattern: str) -> ElementHandle | None:
        return self.first(self.ss_re(selector, pattern))

    def ss_in(self, selector: str, from_: ElementHandle | None) -> list[ElementHandle]:
        return [] if from_ is None else from_.query_selector_all(selector)

    def s_in(self, selector: str, from_: ElementHandle | None) -> ElementHandle | None:
        return self.first(self.ss_in(selector, from_))

    def ss_re_in(self, selector: str, pattern: str, from_: ElementHandle | None) -> list[ElementHandle]:
        return self.re_filter(pattern, self.ss_in(selector, from_))

    def s_re_in(self, selector: str, pattern: str, from_: ElementHandle | None) -> ElementHandle | None:
        return self.first(self.ss_re_in(selector, pattern, from_))

    def next(self, elem: ElementHandle | None) -> ElementHandle | None:
        return None if elem is None else elem.evaluate_handle("el => el.nextElementSibling").as_element()

    def text_c(self, elem: ElementHandle | None) -> str | None:
        if elem is None:
            return None
        return text.strip() if (text := elem.evaluate("el => el.textContent")) else text

    def i_text(self, elem: ElementHandle | None) -> str | None:
        if elem is None:
            return None
        return text.strip() if (text := elem.evaluate("el => el.innerText")) else text

    def attr(self, attr_name: str, elem: ElementHandle | None) -> str | None:
        if elem is None:
            return None
        return attr.strip() if (attr := elem.get_attribute(attr_name)) else attr

    def goto(self, url: str | None) -> bool:
        if not url:
            return False
        try:
            self._page.goto(url, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            return False

    def wait(self, selector: str, timeout: int = 15000) -> ElementHandle | None:
        try:
            return self._page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            return None
