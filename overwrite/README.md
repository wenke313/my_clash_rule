# 分流规则体系 v2（2026-08-22 重构）

> 载体：本目录 `main.ini` 覆写模块，路由器每天 4 点自动从 GitHub 拉取（OpenClash 覆写条目 `main`）。

## 规则优先级（自上而下）

```
第1层  覆写头插（本仓库 main.ini，最高优先）
       ① GEOSITE,private,DIRECT            局域网安全置顶
       ② GEOIP,private,DIRECT,no-resolve
       ③ RULE-SET,Gemini,Gemini            Gemini 独立分流
第2层  OpenClash 注入（路由器 uci 控制，不改）
       ④ easytier-core / BT/下载/代理客户端 进程直连
       ⑤ public-tracker DIRECT / GEOIP,cn DIRECT / 80,443→漏网之鱼 / MATCH→DIRECT
第3层  订阅规则（geosite 分类 → 功能组）
       ⑥ 家规 RULE-SET ×5（Custom_Proxy/Custom_Direct/Google_CDN/Digital_currency/python）
       ⑦ GeoSite 分类（AI/通讯/社交/流媒体/游戏/电商...）→ 功能组
```

## 规则文件清单（全在仓库）

| 文件 | provider | 出口 | 用途 |
|---|---|---|---|
| Custom_Proxy_Classical.yaml | Custom_Proxy | 国外 | 走代理的家规 |
| Custom_Direct.yaml | Custom_Direct | 国内(直连) | 直连家规（含 cloudflare.com） |
| Google_CDN.yaml | Google_CDN | 国内 | Google CDN 直连 |
| Digital_currency.yaml | Digital_currency | 数字货币 | 交易所/链 |
| python.yaml | python | Python | Python 资源 |
| Gemini.yaml | Gemini | Gemini 组 | Gemini 三件套域名 |
| overwrite/main.ini | — | — | 覆写模块（本文件） |
| PlatformIO.yaml | — | 未引用 | 库存 |
| BT_Tracker.yaml | — | ⚠️ 挂起 | 2026-08-16 定论前禁动 |

## 出口设计（锚定区域）

| 服务 | 出口 | 说明 |
|---|---|---|
| **Gemini** | Gemini 组 → 日本-手选 | 落地 SAKURA 日本本土 IDC；Google 系 AI 对 CDN 系 DC（G-Core/Datacamp/FREAK/AWS）判"不支持地区"，勿切 smart |
| ChatGPT/Copilot/AI服务 | 日本-smart | OpenAI 对 DC IP 宽容；异常时手动切日本-手选 |
| 流媒体/通讯/谷歌/数字货币 | 新加坡-smart | smart 自动优化（已开 lgbm+collect+500KB 吞吐测速） |
| GitHub | 日本-smart | |
| Python | 韩国-smart | |
| Steam | 香港-smart | |
| 国内/微软/苹果/PT/PayPal/漏网之鱼 | 直连 | |

## 已知坑（勿重蹈）

- **节点标称 ≠ 落地**：VIP1-HY04"日本"落地 US FREAK、smart 曾选 AWS SG——用 `mihomo_api.py ipcheck <组> [成员]` 查真实落地
- **Quick Start 陷阱**：改覆写后必须 `rm -rf /tmp/openclash.change && service openclash restart` 强制完整重启，否则覆写不生效
- **切组用 UTF-8 请求**：curl 中文组名会 `proxy not exist`，用 mihomo_api.py ipcheck 或 python

## 变更流程

1. 改 yaml/ini → `git add <文件>` → commit → push
2. 自动：每天 4 点路由器拉取 | 手动：`DOWNLOAD_FILE_CURL <raw_url> /etc/openclash/overwrite/main`（ssh-skill）
3. 生效：`rm -rf /tmp/openclash.change && service openclash restart`
4. 验证：`mihomo_api.py rules 10` 看顺序 / `connections` 看命中 / `/tmp/openclash.log` 看 `match ... using`
