# my_clash_rule

Clash/Mihomo 分流规则仓库。OpenClash rule-provider（`behavior: classical`），路由器每天自动从 GitHub raw 拉取。

## 目录结构

### 入库（GitHub 可见）

| 路径 | 作用 |
|------|------|
| `*.yaml`（仓库根） | 12 个 rule-provider 规则文件。路由器运行时通过 OpenClash 自动从 GitHub raw 拉取，按 `payload:` 逐行匹配域名/IP 走对应代理组。其中 `PlatformIO.yaml` 当前未被主配置引用（库存）；`OpenAI.yaml` / `Claude.yaml` / `Gemini.yaml` / `Grok.yaml` 四个为**自动生成，勿手改** |
| `scripts/sync_ai_domains.py` | 四大 AI 厂商域名同步生成器：拉 v2fly 上游分组 + 合并本地增益 + 重写上面 4 个 yaml |
| `sources/ai-local-additions.yaml` | 本地增益清单：上游未收录但需走对应 AI 组的域名。手改这里，生成时自动并入，永不被覆盖 |
| `.github/workflows/sync-ai-domains.yml` | 每天 UTC 20:17 自动跑生成器，有差异才 commit+push |
| `README.md` | 本文件，仓库说明 |
| `overwrite/README.md` | 分流体系文档：规则优先级层次、出口设计、已知坑 |
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

### AI 域名（OpenAI / Claude / Gemini / Grok）— 全自动

这 4 个 yaml **不要手改**，它们由脚本生成：

```bash
python scripts/sync_ai_domains.py          # 生成
python scripts/sync_ai_domains.py --check  # 只比对，有差异退出码 1
```

- **上游更新**：GitHub Actions 每天 UTC 20:17 自动拉 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)，有差异才提交
- **路由器跟进**：rule-provider `interval: 28800`（8 小时）自动从 GitHub raw 拉新，push 后无需任何手工操作
- **加新域名**：改 `sources/ai-local-additions.yaml`，提交后 CI 会自动重新生成（上游收录后自动去重，不会重复）

### 其他 provider（手工维护）

1. 改 yaml → `git add <文件>` → commit（type: 规则）→ push
2. 手动热更新：`mihomo_api.py update <provider>` → 日志验证命中
