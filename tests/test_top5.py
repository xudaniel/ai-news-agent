"""Chinese fork behavior, safe rendering and real decision-pipeline regression tests."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

import pytest

import graph
import publisher
import ranking
import renderer
import top5


@pytest.fixture
def chinese(monkeypatch):
    for module in (graph, publisher, ranking, renderer):
        monkeypatch.setattr(module, 'DIGEST_FORMAT', 'top5-zh')
    monkeypatch.setattr(publisher, 'DIGEST_ISSUE_TITLE_PREFIX', '科技与AI Top 5')
    monkeypatch.setattr(publisher, '_DIGEST_TIME_ZONE', top5._DIGEST_TIME_ZONE.__class__('Asia/Shanghai'))
    monkeypatch.setattr(top5, '_DIGEST_TIME_ZONE', publisher._DIGEST_TIME_ZONE)
    monkeypatch.setattr(publisher, '_utcnow', lambda: datetime(2026, 9, 15, 2, tzinfo=timezone.utc))
    monkeypatch.delenv('DIGEST_DATE', raising=False)


def story(n):
    return {
        'id': f'https://example.com/{n}', '_prompt_id': f'g{n}i1',
        'title': f'测试科技事件{n}', 'original_title': f'Test event {n}',
        'link': f'https://example.com/{n}', 'source': '官方公告',
        'published': datetime(2026, 9, 15, 0, tzinfo=timezone.utc),
        'category': 'Industry & Business', 'summary': '供应商宣布产品上线。',
        'source_type': 'news', 'source_role': 'primary', 'feed_mode': 'core',
        'facts': '供应商宣布产品上线，实际采用情况尚未披露。',
        'why_it_matters': '可能降低客户部署成本。',
        'watchpoint': '关注正式可用范围与客户部署数据。',
        'event_date': '2026-09-15', 'relevance': '产品', 'event_status': '已上线',
        'importance': '中', 'impact_horizon': '中期',
        'affected_parties': '企业产品团队受益，缺乏工作流能力的通用工具承压。',
        'tracking_metric': '跟踪三个月内付费客户数和任务完成率。',
    }


def test_fork_defaults_without_legacy_test_environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith('DIGEST_')}
    env['PYTHONPATH'] = 'src'
    result = subprocess.run([sys.executable, '-c',
        'import config,collector,json; print(json.dumps([config.DIGEST_FORMAT,config.DIGEST_TIMEZONE,config.DIGEST_ISSUE_REPO,collector._MAX_FUTURE_SKEW.total_seconds()]))'],
        env=env, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == ['top5-zh', 'Asia/Shanghai', 'xudaniel/ai-news-agent', 0]


def test_only_five_stories_and_separate_facts_from_inference(chinese):
    items = [story(n) for n in range(1, 9)]
    ids = [item['_prompt_id'] for item in reversed(items)]
    body = renderer.to_markdown(items, top_stories=ids, executive_summary='本日重点是产品落地。')
    assert len(re.findall(r'^## [1-5]\.', body, re.M)) == 5
    assert body.index('测试科技事件8') < body.index('测试科技事件7')
    assert '测试科技事件1' not in body
    assert '发生了什么' in body and '为什么重要（推断）' in body and '观察点' in body
    assert '2026-09-15 08:00' in body
    assert 'RSS 标题与摘要' in body
    assert publisher._today_title_base() == '科技与AI Top 5｜2026-09-15'


def test_quiet_day_is_not_filled_with_extra_stories(chinese):
    body = renderer.to_markdown([story(1)])
    assert '仅选入 1 条' in body
    assert '不代表当天科技界没有新闻' in renderer.to_markdown([])


@pytest.mark.parametrize('key', ['facts', 'why_it_matters', 'watchpoint'])
def test_missing_evidence_fails_closed(chinese, key):
    item = story(1)
    del item[key]
    with pytest.raises(ValueError, match=key):
        renderer.to_markdown([item])


def test_unsafe_markup_escaped_and_non_web_links_rejected(chinese):
    item = story(1)
    item['title'] = '测试<script>alert(1)</script>[伪链接]'
    body = renderer.to_markdown([item])
    assert '<script>' not in body and '\\[伪链接\\]' in body
    item['link'] = 'javascript:alert(1)'
    with pytest.raises(ValueError, match='HTTP'):
        renderer.to_markdown([item])


def test_unsupported_and_future_event_dates_rejected(chinese):
    item = story(1)
    item['event_date'] = '未明确'
    assert '事件日期：** 未明确' in renderer.to_markdown([item])
    item['event_date'] = '2026-09-16'
    with pytest.raises(ValueError, match='event date'):
        renderer.to_markdown([item])


def test_chinese_mode_will_not_publish_english_fallback(chinese, monkeypatch):
    monkeypatch.setattr(graph, '_get_openai_api_key', lambda: '')
    with pytest.raises(RuntimeError, match='no heuristic publication'):
        graph.node_categorize({'items': [story(1)]})


def test_decisions_propagate_evidence_through_complete_renderer(chinese, tmp_path, monkeypatch):
    candidate = story(1)
    snapshot = graph.build_candidate_snapshot([candidate])
    candidates = tmp_path / 'candidates.json'
    candidates.write_text(json.dumps(snapshot))
    decisions = {
        'schema_version': 2, 'kind': 'ai-news-agent.decisions',
        'snapshot_id': snapshot['snapshot_id'],
        'top_stories': ['g1i1'], 'executive_summary': '今日测试摘要。',
        'groups': [{'group_id': 'g1', 'off_topic_ids': [], 'clusters': [{
            'keep_id': 'g1i1', 'duplicate_ids': [], 'category': 'Industry & Business',
            'short_title': '中文产品上线', 'tier': 'high',
            **{k: candidate[k] for k in ('facts', 'why_it_matters', 'watchpoint', 'event_date', 'relevance',
                                          'event_status', 'importance', 'impact_horizon',
                                          'affected_parties', 'tracking_metric')},
        }]}],
    }
    decisions_file = tmp_path / 'decisions.json'
    decisions_file.write_text(json.dumps(decisions))
    output = tmp_path / 'news.md'
    monkeypatch.setattr(graph, '_NEWS_FILE', output)
    state = graph.apply_decisions_file(decisions_file, candidates)
    assert '中文产品上线' in state['markdown']
    assert candidate['watchpoint'] in output.read_text()
    assert '30 秒速览' in output.with_suffix('.html').read_text()
    # Invalid later decisions must not leave a stale, publishable file behind.
    del decisions['groups'][0]['clusters'][0]['facts']
    decisions_file.write_text(json.dumps(decisions))
    with pytest.raises(ValueError, match='facts'):
        graph.apply_decisions_file(decisions_file, candidates)
    assert not output.exists()
    assert not output.with_suffix('.html').exists()


def test_beijing_midnight_rejects_previous_day(chinese, monkeypatch):
    monkeypatch.setenv('DIGEST_DATE', '2026-09-15')
    monkeypatch.setattr(publisher, '_utcnow', lambda: datetime(2026, 9, 15, 16, tzinfo=timezone.utc))
    with pytest.raises(RuntimeError, match='date'):
        publisher._publication_date()


def test_overview_status_and_daily_action_match_editorial_order(chinese):
    items = [story(1), story(2)]
    items[1]['watchpoint'] = '今天验证第二个产品的试用权限。'
    body = renderer.to_markdown(items, top_stories=['g2i1', 'g1i1'])
    overview, detail = body.split('## 1.', 1)
    assert '30 秒速览' in overview
    assert overview.index('测试科技事件2') < overview.index('测试科技事件1')
    assert '产品 · 已上线' in overview
    assert body.split('## 今日一个行动')[1].strip() == items[1]['tracking_metric']


@pytest.mark.parametrize('field,value', [
    ('relevance', 'Investment'), ('event_status', 'GA'),
    ('what_changed', 'New rollout'), ('executive_summary', 'English only'),
])
def test_new_user_visible_fields_reject_english_or_unknown_labels(chinese, field, value):
    item = story(1)
    kwargs = {}
    if field == 'executive_summary':
        kwargs[field] = value
    else:
        item[field] = value
    if field == 'what_changed':
        item['previous_report_date'] = '2026-09-14'
    with pytest.raises(ValueError):
        top5.render_top5_email([item], **kwargs)


def test_continuity_requires_prior_date_and_material_delta(chinese):
    item = story(1)
    item['previous_report_date'] = '2026-09-14'
    with pytest.raises(ValueError, match='together'):
        renderer.to_markdown([item])
    item['what_changed'] = '从邀请测试扩大到企业客户正式使用。'
    assert '较 2026-09-14 新增' in renderer.to_markdown([item])
    assert item['what_changed'] in top5.render_top5_email([item])
    item['previous_report_date'] = '2026-09-15'
    with pytest.raises(ValueError, match='precede'):
        renderer.to_markdown([item])


def test_missing_status_stays_unknown_instead_of_guessing(chinese):
    item = story(1)
    del item['event_status']
    assert '产品 · 未明确' in top5.render_top5_email([item])
    assert '首次报道' not in top5.render_top5_email([item])


def test_html_escapes_sources_and_keeps_monochrome_mobile_layout(chinese):
    item = story(1)
    item['facts'] += '<img src=x onerror=alert(1)>'
    item['source'] = '<script>官方</script>'
    item['link'] = 'https://example.com/?a=1&b=2'
    output = top5.render_top5_email([item])
    assert '<script>' not in output and '<img src=x' not in output
    assert '&lt;img' in output and 'a=1&amp;b=2' in output
    assert 'width=device-width' in output and 'font:18px' in output
    assert 'background:#ffffff' in output and 'color:#111111' in output
    assert 'alt="欣远景投资"' in output
    assert '今日一个行动' in output
    assert '大字版' not in output and '石墨版' not in output
    item['link'] = 'javascript:alert(1)'
    with pytest.raises(ValueError, match='HTTP'):
        top5.render_top5_email([item])


def test_priority_impact_and_tracking_fields_render_and_validate(chinese):
    item = story(1)
    output = top5.render_top5_email([item], executive_summary='业务软件竞争转向可验证的执行结果。')
    assert '重要性中' in output and '中期' in output
    assert '谁受益／谁承压' in output and item['affected_parties'] in output
    assert '后续验证指标' in output and item['tracking_metric'] in output
    assert '判断依据' in output
    item['impact_horizon'] = '很快'
    with pytest.raises(ValueError, match='impact_horizon'):
        top5.render_top5_email([item])


def test_two_page_print_layout_assigns_first_two_then_remaining(chinese):
    items = [story(n) for n in range(1, 6)]
    output = top5.render_top5_print(items, executive_summary='业务软件竞争转向可验证的执行结果。')
    assert output.count('class="page"') == 2
    first_page, second_page = output.split('<section class="page">')[1:]
    assert '测试科技事件1' in first_page and '测试科技事件2' in first_page
    assert '<h2>3. 测试科技事件3</h2>' not in first_page
    assert '测试科技事件3' in second_page and '测试科技事件5' in second_page
    assert '1 / 2' in first_page and '2 / 2' in second_page
    assert 'break-inside:avoid' in output and '欣远景投资' in output
