# 分流规则体系 v3（2026-10-24 对齐 20261023 主配置）

> 载体：主配置 yaml（本机 `config/`，不入库）+ 本仓库 11 个被引用的 rule-provider。
> 路由器每 8 小时（`interval: 28800`）从 GitHub raw 拉取 provider；改规则 push 后可手动热更新，无需重启。
> 旧版（v2，`main.ini` 覆写模块）已废弃，不再使用。

## 规则优先级（自上而下）

```
第1层  OpenClash 注入（路由器 uci 控制，不改）
       ① easytier-core / BT/下载/代理客户端 进程直连
       ② category-public-tracker DIRECT / 80,443→漏网之鱼 / MATCH→DIRECT
第2层  主配置 rules（源规则）
       ③ PROCESS-NAME,curl-ai-probe → AI探测（AI 节点筛选专用通道，勿删）
       ④ Custom_Proxy → 国外
       ⑤ private → 国内
       ⑥ 家规直连：Custom_Direct / Google_CDN / google-cn → 国内
       ⑦ Digital_currency → 数字货币
       ⑧ 游戏/下载/tracker 国内分类 → 国内
       ⑨ 通讯/社交/Talkatone → 对应组
       ⑩ AI：OpenAI / Claude / Gemini（→ Google服务）/ Grok / OpenCode（RULE-SET）
       ⑪ OneDrive / Copilot(bing) / AI服务(category-ai-!cn) / GitHub+Tools → Tools
       ⑫ 测速 / 流媒体 / 苹果 / 微软
       ⑬ Google（RULE-SET）→ Google服务；GEOSITE,googlefcm → 谷歌FCM；GEOSITE,google → Google服务
       ⑭ 游戏平台 / 国外媒体 / PT / PayPal / 电商 / GEOSITE,gfw → 国外
       ⑮ GEOIP 大厂（telegram/twitter/facebook/google/netflix）
       ⑯ GEOSITE,cn / GEOIP,cn → 国内 → MATCH → 漏网之鱼
```

家规（自维护 rule-provider）先于 GeoSite 命中，不会被 GeoSite 误判。

## 规则文件清单（全在仓库根）

| 文件 | provider | 出口组 | 用途 |
|---|---|---|---|
| Custom_Proxy_Classical.yaml | Custom_Proxy | 国外 | 走代理的家规 |
| Custom_Direct.yaml | Custom_Direct | 国内（直连） | 直连家规，条目最多 |
| Google_CDN.yaml | Google_CDN | 国内 | Google CDN 直连 |
| Google.yaml | Google | Google服务 | Google 系自维护 |
| Digital_currency.yaml | Digital_currency | 数字货币 | 交易所/链 |
| Tools.yaml | Tools | Tools | 开发工具 / Python / 语言 / 发行版 |
| OpenAI.yaml | OpenAI | OpenAI | OpenAI 域名 |
| Claude.yaml | Claude | Claude | Claude / Anthropic 域名 |
| Gemini.yaml | Gemini | Google服务 | Gemini / Google AI 全域名体系（2026-10-24 起并入 Google服务，原 Gemini 组已删） |
| Grok.yaml | Grok | Grok | Grok 域名 |
| OpenCode.yaml | OpenCode | OpenCode | OpenCode 域名 |
| PlatformIO.yaml | — | 未引用 | 库存 |

## 出口设计（三层）

```
功能组（select）→ 地区 smart 组（LightGBM 选点）→ 节点（三家机场订阅）
```

| 类别 | 功能组 | 可选出口 |
|---|---|---|
| 普通业务 | 国外 / 流媒体 / 通讯 / 谷歌FCM / Tools / 数字货币 / Copilot 等 | 直连 + 所有-smart + 18 个地区 smart 组 + 拒绝 |
| AI 业务 | OpenAI / Claude / Grok / OpenCode / AI服务 / **Google服务** | 直连 + 日本/新加坡/美国/韩国 `-AI-Smart` + 所有-smart（逃生门） + 拒绝 |
| 直连类 | 国内 / 微软 / 苹果 / PT / 漏网之鱼 等 | 同普通模板，默认项为"直连"；实际当前选择以路由器现网为准 |

- **Google服务 = Gemini + Google 合并组**（2026-10-24）：Gemini、Google 两个 RULE-SET 及 `GEOSITE,google` / `GEOIP,google` 全部走它，与 AI 组同用 `&default-ai` 锚点（AI-Smart 池）。`谷歌FCM`（推送长连接）单独留在普通模板，锚定单区 smart（现为日本-smart），不进 AI 池。`
- **AI-Smart 组**：成员由 `ai_screen.py`（路由器 `/etc/openclash/ai/`）每日 03:30 筛选，结果写进组的 `filter` 白名单和 `policy-priority`；组结构手工维护。
- **筛选判据**：google.com 最终落地为 `.com` 判干净、落到 `.com.hk` 判脏；OpenAI `/v1/models` 返回 401 判支持、403 判封区。
- **脏节点必须物理隔离**：smart 只看"能连"，不会自己避开被判地区不支持的节点。
- 筛选体系细节见本机 `docs/ai-node-screening.md`。

## 已知坑（勿重蹈）

- **节点标称 ≠ 落地**：用 `mihomo_api.py ipcheck <组> [成员]` 查真实落地。
- **落地 ASN ≠ Google 的地区判定**：本土 ISP 的 IP 也可能被判 HK，判据以 google.com 最终落地为准。
- **Quick Start 陷阱**：改主配置后必须 `rm -rf /tmp/openclash.change && service openclash restart`，否则不生效。
- **切组用 UTF-8 请求**：curl 中文组名会 `proxy not exist`，用 `mihomo_api.py` 或先 URL 编码。
- **payload 格式错会静默不命中**：双前缀如 `GEOSITE,geosite,xxx` 不报错也不生效。
- **主配置 rules 会被 OpenClash 增量覆盖**：可持续的改动放 rule-provider。

## 变更流程

**改规则**（不重启）：
1. 改 yaml `payload:` → `git add <文件>` → commit → push
2. 热更新：`mihomo_api.py update <provider>`
3. 验证：`ruleCount` 对 payload 行数、`updatedAt` 对账；命中看 `/tmp/openclash.log` 的 `match ... using ...`

**改主配置**（需重启）：
1. 本地改 `config/` 源文件，**文件名日期换成当天**
2. 上传前先从路由器下载现网文件对比
3. `uci set openclash.config.config_path=/etc/openclash/config/<新名>`（必须全路径），并复制旧 db 为新名
4. `rm -rf /tmp/openclash.change && service openclash restart`
5. 验证：`mihomo_api.py rules 10` 看顺序 / `connections` 看命中
