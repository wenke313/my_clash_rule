# 分流规则体系 v4（2026-11-07 对齐 20261106-v2 主配置）

> 载体：主配置 yaml（本机 `config/`，不入库）+ 本仓库的 rule-provider + MetaCubeX 上游 mrs。
> 路由器每 8 小时（`interval: 28800`）拉取 provider；改规则 push 后可手动热更新，无需重启。
> v3（AI-Smart 专用池 + ai_screen 每晚筛选）已于 2026-11-06 退役，见下「出口设计」。

## 规则优先级（自上而下）

```
第1层  OpenClash 注入（路由器 uci 控制，不改）
       ① easytier-core / BT/下载/代理客户端 进程直连
       ② category-public-tracker DIRECT / 80,443→漏网之鱼 / MATCH→DIRECT
第2层  主配置 rules（源规则）
       ③ Custom_Proxy → 国外
       ④ private → 国内
       ⑤ 人机验证/收款与 AI 同出口：challenges.cloudflare.com → Claude；stripe / hcaptcha → AI服务
       ⑥ 家规直连：Custom_Direct / Google_CDN / google-cn → 国内
       ⑦ Digital_currency → 数字货币
       ⑧ 游戏/下载/tracker 国内分类 → 国内
       ⑨ 通讯 / 社交 / Talkatone → 对应组
       ⑩ AI：OpenAI / Claude / Gemini + UpGemini（→ Google服务）/ Grok / OpenCode
       ⑪ OneDrive / Copilot(bing) / AI服务(category-ai-!cn) / GitHub+Tools → Tools
       ⑫ 测速 / YouTube / 流媒体 / 苹果 / 微软
       ⑬ Google（RULE-SET）→ Google服务；GEOSITE,googlefcm → 谷歌FCM；GEOSITE,google → Google服务
       ⑭ TikTok / 流媒体 / 游戏平台 / 国外媒体 / PT / PayPal / 电商 / GEOSITE,gfw → 国外
       ⑮ GEOIP 大厂（telegram/twitter/facebook/google/netflix）
       ⑯ GEOSITE,cn / GEOIP,cn → 国内 → MATCH → 漏网之鱼
```

家规（自维护 rule-provider）先于 GeoSite 命中，不会被 GeoSite 误判；反过来，要让某域名落到后面的 GeoSite 分组（如 `mtalk.google.com` → 谷歌FCM），必须先把它从前面的家规里删掉。

## 规则来源清单

| provider | 来源 | 出口组 | 用途 |
|---|---|---|---|
| Custom_Proxy | 仓库 `Custom_Proxy_Classical.yaml` | 国外 | 走代理的家规 |
| Custom_Direct | 仓库 `Custom_Direct.yaml` | 国内（直连） | 直连家规，条目最多 |
| Google_CDN | 仓库 `Google_CDN.yaml` | 国内 | Google 国内可直连的 CDN/API |
| Google | 仓库 `Google.yaml` | Google服务 | GEOSITE,google 覆盖不到的 Google 域名 |
| Digital_currency | 仓库 `Digital_currency.yaml` | 数字货币 | 交易所/链 |
| Tools | 仓库 `Tools.yaml` | Tools | 开发工具 / Python / 语言 / 发行版 |
| Gemini | 仓库 `Gemini.yaml` | Google服务 | 上游 mrs 之外的 Gemini 增益域名 |
| OpenCode | 仓库 `OpenCode.yaml` | OpenCode | OpenCode 域名 |
| OpenAI | 上游 `geosite/openai.mrs` | OpenAI | — |
| Claude | 上游 `geosite/anthropic.mrs` | Claude | — |
| UpGemini | 上游 `geosite/google-gemini.mrs` | Google服务 | — |
| Grok | 上游 `geosite/xai.mrs` | Grok | — |
| — | 仓库 `PlatformIO.yaml` | 未引用 | 库存 |

AI 四厂商主体跟上游 mrs（2026-10-26 起），仓库只留上游缺的增益域名。

## 出口设计（三层）

```
功能组（select）→ 6 个区域 smart 组（LightGBM 选点 + 内核故障守卫）→ 节点（三家机场订阅）
```

| 类别 | 功能组 | 可选出口（锚点） |
|---|---|---|
| 普通业务 | 国外 / 流媒体 / 通讯 / 谷歌FCM / Tools / 数字货币 / Copilot 等 | `&default`：直连 / 所有 / 香港 / 台湾 / 日本 / 新加坡 / 韩国 / 美国 / 拒绝 |
| AI 业务 | OpenAI / Claude / Grok / OpenCode / AI服务 / Google服务 | `&default-ai`：日本 / 美国 / 新加坡 / 韩国 / 台湾 / 所有 / 直连 / 拒绝（首项是回落默认，不能是直连） |
| 直连类 | 国内 / 微软 / 苹果 / PT / 漏网之鱼 等 | 同普通模板，默认选"直连" |

- 区域 smart 组 `include-all` + 区域 filter，节点不筛、不钉；`所有` 是全部节点的手选组。各功能组当前选哪个区域，以路由器现网为准。
- **故障守卫**：每 10 秒探测在用节点，三重确认判死后从候选里拿掉并关闭其连接；同协议 60 秒内 3 个判死即整条协议暂停 2 分钟；只在本区域组内换节点，不跨国。
- **Google服务 = Gemini + Google 合并组**：Gemini、UpGemini、Google 三个 RULE-SET 及 `GEOSITE,google` / `GEOIP,google` 全部走它。`谷歌FCM`（推送长连接 :5228）单独一组，用普通模板。
- **已退役（2026-11-06）**：四个 `*-AI-Smart`、`AI大脑`、`AI探测` 组和路由器 `ai_screen.py` 白名单筛选。

## 已知坑（勿重蹈）

- **节点标称 ≠ 落地**：用 `mihomo_api.py ipcheck <组> [成员]` 查真实落地。
- **落地 ASN ≠ Google 的地区判定**：本土 ISP 的 IP 也可能被判 HK，判据以 google.com 最终落地为准。
- **Quick Start 陷阱**：改主配置后必须 `rm -rf /tmp/openclash.change && service openclash restart`，否则不生效。
- **切组用 UTF-8 请求**：curl 中文组名会 `proxy not exist`，用 `mihomo_api.py` 或先 URL 编码。
- **payload 格式错会静默不命中**：双前缀如 `GEOSITE,geosite,xxx` 不报错也不生效。
- **主配置 rules 会被 OpenClash 增量覆盖**：可持续的改动放 rule-provider。
- **改规则后长连接不会自动换路**：已建立的连接保留原命中，需等它重连或在 API 里断开（`DELETE /connections/<id>`）。

## 变更流程

**改规则**（不重启）：
1. 改 yaml `payload:` → `git add <文件>` → commit → push
2. 热更新：`mihomo_api.py update <provider>`
3. 验证：`ruleCount` 对 payload 行数、`updatedAt` 对账；命中看 `/tmp/openclash.log` 的 `match ... using ...` 或 `connections`

**改主配置**（需重启）：
1. 本地改 `config/` 源文件，**文件名日期换成当天**
2. 上传前先从路由器下载现网文件对比
3. `uci set openclash.config.config_path=/etc/openclash/config/<新名>`（必须全路径），并复制旧 db 为新名
4. `rm -rf /tmp/openclash.change && service openclash restart`
5. 验证：`mihomo_api.py rules 10` 看顺序 / `connections` 看命中
