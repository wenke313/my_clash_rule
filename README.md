# my_clash_rule

Clash/Mihomo 分流规则仓库。OpenClash rule-provider（`behavior: classical`），路由器每天自动从 GitHub raw 拉取。

## 目录结构

### 入库（GitHub 可见）

| 路径 | 作用 |
|------|------|
| `*.yaml`（仓库根） | 9 个 rule-provider 规则文件。路由器每 8h（`interval: 28800`）自动从 GitHub raw 拉取，按 `payload:` 逐行匹配域名/IP 走对应代理组。其中 `PlatformIO.yaml` 当前未被主配置引用（库存）；`Gemini.yaml` 为增益清单，AI 四厂商主体已切上游 mrs（见 `docs/ai-rules-upstream-mrs.md`，本机） |
| `scripts/sync_ai_domains.py` | [已退役] 昔日四大 AI 域名同步生成器，保留作历史参考 |
| `sources/ai-local-additions.yaml` | [已退役] 昔日生成器增益清单，增益现直接手改 `Gemini.yaml` |
| `README.md` | 本文件，仓库说明 |
| `overwrite/README.md` | 分流体系文档：规则优先级层次、出口设计、已知坑 |
| `.gitattributes` | 统一 LF，防 Windows/Linux 假 diff |
| `.gitignore` | 排除目录/敏感文件 |

### 不入库（仅本机，.gitignore 排除）

| 路径 | 作用 |
|------|------|
| `config/` | 主配置文件（`Clash-smart-nofeisu-*.yaml`，文件名日期 = 版本号）、路由器文件备份。含订阅 token，敏感，绝不入库 |
| `docs/` | 路由器 ImmortalWrt + OpenClash 体系速查文档，本机 Agent 共享，免重复排查 |
| `bench/` | 节点测试环境：mihomo Windows 内核、LightGBM 模型（`.bin`）、训练/测速 Python 脚本、geo 数据文件、缓存 |
| `mihomo-smart/` | Smart 内核 fork 工作区（独立 git 仓库） |
| `logs/` | 本地排查/分析工作记录 |
| `.agents/`、`.opencode/` | 本机 Agent 技能定义（mihomo-api、openclash-* 系列 skill） |
| `.superpowers/` | 本机 Agent 工作区 |
| `.tmp/` | 临时文件 |

> 完整架构/运行模型/规则优先级/出口设计见 `docs/immortalwrt-router.md` 和 `overwrite/README.md`。

## 提交规范

Conventional Commits 中文模板：

```
<type>: <简述，中文，50字内>
```

| type | 何时用 |
|------|--------|
| `规则` | 增删改 rule-provider 的 payload 行 |
| `配置` | 主配置变更（config/） |
| `文档` | docs/、README、overwrite/README 更新 |
| `整理` | .gitignore、目录整理、废弃代码清理 |

原则：一个提交只做一件事；简述中文，不中英混杂；不写 "update"/"fix stuff" 这类无信息量的话。

## 维护流程

### AI 域名（OpenAI / Claude / Gemini / Grok）— 上游 mrs + 自家增益

2026-10-26 起 AI 主体直接引上游（主配置 rule-provider 指向 MetaCubeX mrs，路由器 8h 自动跟进，无需任何同步动作）：

- OpenAI ← `openai.mrs` / Claude ← `anthropic.mrs` / Grok ← `xai.mrs` / UpGemini ← `google-gemini.mrs`
- 自家仓库只保留 **`Gemini.yaml`（10 条增益）** 和 **`OpenCode.yaml`（上游仅覆盖 1/6，全量自维护）**
- **加新域名**：直接手改对应 yaml → commit → push（路由器 8h 内拉取；急事 `mihomo_api.py update <provider>` 立即生效）
- 对账明细与架构变更记录：`docs/ai-rules-upstream-mrs.md`（本机）
- 旧的生成器与 CI 已退役（scripts/、sources/ 保留作历史参考）

### 其他 provider（手工维护）

1. 改 yaml → `git add <文件>` → commit（type: 规则）→ push
2. 手动热更新：`mihomo_api.py update <provider>` → 日志验证命中
