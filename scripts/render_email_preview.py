"""Render a fixed public-news layout sample without APIs, mail, or publication."""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import top5

sample = json.loads((ROOT / 'docs/examples/reading-experience.json').read_text())
top5._publication_date = lambda: date.fromisoformat(sample['date'])
items = [dict(s, _prompt_id=f'g{n}i1', id=s['link'],
              published=datetime(2026, 9, 14, 12, tzinfo=timezone.utc),
              category='Industry & Business')
         for n, s in enumerate(sample['stories'], 1)]
body = top5.render_top5_email(items, executive_summary=sample['executive_summary'],
                             top_stories=[s['_prompt_id'] for s in items])
# These examples demonstrate layout, not source publication timestamps or a new edition.
body = body.replace(top5.EVIDENCE_NOTE,
                    '版式示例：采用2026年9月14日公开事件，不代表本次新增报道。')
body = body.replace('报道时间：2026-09-14 20:00', '报道日期：2026-09-14')
body = body.replace(top5.LOGO_URL, '../assets/branding/new-vision-investment-mono.png')
(ROOT / 'docs/email-preview.html').write_text(body)
print(ROOT / 'docs/email-preview.html')
