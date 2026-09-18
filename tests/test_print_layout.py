"""Optional real Chromium/PDF regression gate; see docs/print-validation.md."""
import io
import os
import unicodedata
from pathlib import Path

import pytest

from tests.test_top5 import chinese, story  # noqa: F401
import top5

playwright = pytest.importorskip('playwright.sync_api')
pypdf = pytest.importorskip('pypdf')


@pytest.fixture(scope='module')
def browser():
    with playwright.sync_playwright() as p:
        options = {'headless': True}
        if os.environ.get('CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['CHROMIUM_EXECUTABLE']
        instance = p.chromium.launch(**options)
        yield instance
        instance.close()


@pytest.mark.parametrize('case', ['preview', 'empty', 'one', 'five', 'long', 'mixed'])
def test_two_physical_pages_with_visible_content(browser, chinese, case, tmp_path):
    root = Path(__file__).resolve().parents[1]
    count = 0 if case == 'empty' else 1 if case == 'one' else 5
    items = [story(n) for n in range(1, count + 1)]
    summary = '业务软件竞争转向可验证的执行结果。'
    warning = '来源覆盖：8/10 个订阅源读取成功；2 个源失败，本期覆盖不完整。'
    if case in ('long', 'mixed'):
        # Stress all slots at once, including optional history and source labels.
        prose = '宽' * 2000 if case == 'long' else '测' + 'W' * 2000
        summary = prose + '。'
        for n, item in enumerate(items, 1):
            for field in ('title', 'facts', 'why_it_matters', 'affected_parties',
                          'tracking_metric', 'source', 'what_changed'):
                item[field] = f'测试{n}' + prose
            item['previous_report_date'] = '2026-09-14'
    if case == 'preview':
        markup = (root / 'docs/print-preview.html').read_text()
    else:
        markup = top5.render_top5_print(items, executive_summary=summary, coverage_note=warning)
    # Use the real logo without relying on public network availability.
    import base64
    logo = 'data:image/png;base64,' + base64.b64encode(
        (root / 'assets/branding/new-vision-investment-mono.png').read_bytes()).decode()
    markup = markup.replace(top5.LOGO_URL, logo).replace(
        '../assets/branding/new-vision-investment-mono.png', logo)
    page = browser.new_page()
    try:
        page.route('https://**/*', lambda route: route.abort())
        page.emulate_media(media='print')
        page.set_content(markup, wait_until='load')
        page.evaluate('document.fonts.ready')
        problems = page.evaluate('''() => {
            const problems = [];
            for (const [i, box] of [...document.querySelectorAll('.page')].entries()) {
                const bounds = box.getBoundingClientRect();
                const footer = box.querySelector('.footer').getBoundingClientRect();
                for (const element of box.querySelectorAll('h1,h2,p,li,img')) {
                    const r = element.getBoundingClientRect();
                    if (r.bottom > footer.top || r.left < bounds.left - 1 || r.right > bounds.right + 1)
                        problems.push({page:i+1, text:element.textContent.slice(0,35), bottom:r.bottom, footer:footer.top});
                }
                const walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
                while (walker.nextNode()) {
                    const node = walker.currentNode;
                    if (!node.textContent.trim()) continue;
                    const range = document.createRange(); range.selectNodeContents(node);
                    for (const r of range.getClientRects()) {
                        if (r.left < bounds.left - 1 || r.right > bounds.right + 1 || r.bottom > bounds.bottom + 1)
                            problems.push({page:i+1, text:node.textContent.slice(0,35), overflow:true});
                    }
                }
            }
            return problems;
        }''')
        assert problems == []
        pdf = page.pdf(prefer_css_page_size=True, print_background=True)
        (tmp_path / f'{case}.pdf').write_bytes(pdf)
        pages = pypdf.PdfReader(io.BytesIO(pdf)).pages
        assert len(pages) == 2
        text = [''.join(unicodedata.normalize('NFKC', p.extract_text()).split()) for p in pages]
        assert '1/2' in text[0] and '2/2' in text[1]
        assert '今日一个行动' in text[1]
        if case != 'preview':
            assert ''.join(unicodedata.normalize('NFKC', warning).split()) in text[0]
        # Every story source must survive PDF printing, including the fifth story.
        assert text[0].count('来源:') == min(count, 2)
        assert text[1].count('来源:') == max(count - 2, 0)
        links = {
            annotation.get_object()['/A']['/URI']
            for pdf_page in pages for annotation in pdf_page.get('/Annots', [])
            if annotation.get_object().get('/A', {}).get('/URI')
        }
        assert len(links) == count
    finally:
        page.close()
