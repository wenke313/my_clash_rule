#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同步 4 个 AI 厂商 rule-provider（OpenAI / Claude / Gemini / Grok）。

数据源：v2fly/domain-list-community（MetaCubeX geosite 的上游）
流程：拉分组 → 展开 include: → full:/普通条目转成 DOMAIN/DOMAIN-SUFFIX
      → 合并 sources/ai-local-additions.yaml 本地增益 → 写出仓库根 yaml

只用标准库，不引依赖。CI 与本地跑同一份代码。

用法：
    python scripts/sync_ai_domains.py           # 生成并写入
    python scripts/sync_ai_domains.py --check   # 只比对，有差异则退出码 1
"""

import re
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/'
ROOT = Path(__file__).resolve().parent.parent
ADDITIONS = ROOT / 'sources' / 'ai-local-additions.yaml'

# 厂商 -> v2fly 分组（google-gemini 内部 include google-deepmind，会自动展开）
VENDORS = {
    'OpenAI': ['openai'],
    'Claude': ['anthropic'],
    'Gemini': ['google-gemini', 'google-deepmind'],
    'Grok': ['xai'],
}

# 上游数据完整性下限：低于这个数视为拉取失败，拒绝写入（防上游挂掉把规则清空）
MIN_ENTRIES = {'OpenAI': 15, 'Claude': 12, 'Gemini': 25, 'Grok': 3}

_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_cache = {}


def fetch(group):
    """拉一个 v2fly 分组原文，带内存缓存。"""
    if group in _cache:
        return _cache[group]
    url = BASE + group
    try:
        with _opener.open(url, timeout=30) as r:
            txt = r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'[FAIL] 拉取 {group} 失败: HTTP {e.code}')
    except Exception as e:
        raise SystemExit(f'[FAIL] 拉取 {group} 失败: {e}')
    _cache[group] = txt
    return txt


def parse(group, seen=None):
    """解析分组，递归展开 include:。

    返回 (suffix:set, full:set, regexp:set)
    v2fly 语法：
        普通行          -> 域后缀匹配（含子域）
        full:xxx        -> 精确域名
        regexp:xxx      -> 正则（clash classical 不支持，收集后丢弃并提示）
        keyword:xxx     -> 关键字（同上）
        include:xxx     -> 引用另一分组
        行尾 @ads 等    -> 属性标注，剥掉
    """
    if seen is None:
        seen = set()
    if group in seen:
        return set(), set(), set()
    seen.add(group)

    suffix, full, regexp = set(), set(), set()
    for raw in fetch(group).splitlines():
        line = raw.split('#')[0].split('@')[0].strip()
        if not line:
            continue
        if line.startswith('include:'):
            a, b, c = parse(line[len('include:'):].strip(), seen)
            suffix |= a
            full |= b
            regexp |= c
        elif line.startswith('full:'):
            full.add(line[len('full:'):].strip().lower())
        elif line.startswith('regexp:'):
            regexp.add(line[len('regexp:'):].strip())
        elif line.startswith('keyword:'):
            regexp.add('keyword:' + line[len('keyword:'):].strip())
        else:
            suffix.add(line.lower())

    # full: 已精确覆盖的，不必再当后缀
    suffix -= full
    return suffix, full, regexp


def load_additions():
    """读本地增益清单。格式极简，手写解析，不引 PyYAML。

    OpenAI:
      - DOMAIN-SUFFIX,example.com
      - DOMAIN,exact.example.com
    """
    out = {v: [] for v in VENDORS}
    if not ADDITIONS.exists():
        return out
    cur = None
    for raw in ADDITIONS.read_text(encoding='utf-8').splitlines():
        line = raw.split('#')[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r'^([A-Za-z]+):\s*$', line)
        if m:
            cur = m.group(1)
            if cur not in out:
                raise SystemExit(f'[FAIL] 增益清单有未知厂商: {cur}')
            continue
        m = re.match(r'^\s+-\s*(DOMAIN-SUFFIX|DOMAIN),\s*([A-Za-z0-9._-]+)\s*$', line)
        if m and cur:
            out[cur].append((m.group(1), m.group(2).lower()))
    return out


def build(vendor, additions):
    """生成单个厂商条目，返回 (upstream_entries, local_entries, regexps)。

    上游条目直接来自 v2fly；本地条目来自 ai-local-additions.yaml 且未被上游覆盖。
    """
    all_full, all_suffix, all_regexp = set(), set(), set()
    for g in VENDORS[vendor]:
        s, f, r = parse(g)
        all_suffix |= s
        all_full |= f
        all_regexp |= r

    # 精确域名走 DOMAIN，其余走 DOMAIN-SUFFIX
    upstream = ([('DOMAIN', d) for d in sorted(all_full)]
                + [('DOMAIN-SUFFIX', d) for d in sorted(all_suffix)])

    # 本地增益：已被上游覆盖的跳过
    covered = set(upstream)
    local = []
    for kind, value in additions.get(vendor, []):
        key = (kind, value)
        if key in covered:
            continue
        # 父域已覆盖（如上游有 openai.com 后缀，本地再写 api.openai.com 无意义）
        if kind == 'DOMAIN' and any(
            k == 'DOMAIN-SUFFIX' and (value == v or value.endswith('.' + v))
            for k, v in covered
        ):
            continue
        if any(k == 'DOMAIN' and v == value for k, v in covered):
            continue
        covered.add(key)
        local.append(key)

    total = len(upstream) + len(local)
    if total < MIN_ENTRIES[vendor]:
        raise SystemExit(
            f'[FAIL] {vendor} 仅解析出 {total} 条，低于下限 {MIN_ENTRIES[vendor]}，'
            f'疑似上游异常，拒绝写入'
        )
    return upstream, local, sorted(all_regexp)


def render(vendor, upstream, local, regexps):
    """渲染成与现有 yaml 风格一致的文本。

    注意：不写生成时间戳。否则每次跑都产生 diff，CI 会天天提交空改动。
    同步时间看 git 提交记录即可。
    """
    lines = [
        f'# {vendor} — 由 scripts/sync_ai_domains.py 自动生成，请勿手改',
        f'# 数据源: v2fly/domain-list-community ({", ".join(VENDORS[vendor])})',
        f'# 本地增益: sources/ai-local-additions.yaml ({len(local)} 条)',
        f'# 条目: {len(upstream) + len(local)}',
        '# 想加域名请改 sources/ai-local-additions.yaml，下次生成自动并入',
        'payload:',
    ]

    lines.append(f'  # ===== 上游 v2fly ({len(upstream)} 条) =====')
    for kind, value in upstream:
        lines.append(f'  - {kind},{value}')

    if local:
        lines.append(f'  # ===== 本地增益 ({len(local)} 条) =====')
        for kind, value in local:
            lines.append(f'  - {kind},{value}')

    if regexps:
        lines.append('  # ===== 上游正则/关键字条目（clash classical 不支持，未纳入）=====')
        for r in regexps:
            lines.append(f'  #   {r}')

    return '\n'.join(lines) + '\n'


def main():
    check_only = '--check' in sys.argv
    additions = load_additions()

    outputs = {}
    counts = {}
    for vendor in VENDORS:
        upstream, local, regexps = build(vendor, additions)
        outputs[vendor] = render(vendor, upstream, local, regexps)
        counts[vendor] = {'upstream': len(upstream), 'local': len(local)}

    changed = []
    for vendor, text in outputs.items():
        path = ROOT / f'{vendor}.yaml'
        old = path.read_text(encoding='utf-8') if path.exists() else ''
        if old == text:
            print(f'  [同] {vendor}.yaml')
            continue
        changed.append(vendor)
        if check_only:
            print(f'  [异] {vendor}.yaml 需要更新')
        else:
            path.write_text(text, encoding='utf-8', newline='\n')
            print(f'  [写] {vendor}.yaml')

    print(json.dumps({'changed': changed, 'counts': counts}, ensure_ascii=False))

    if check_only and changed:
        sys.exit(1)


if __name__ == '__main__':
    main()
