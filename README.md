# my_clash_rule

Clash/Mihomo 分流规则仓库。OpenClash rule-provider（`behavior: classical`），路由器每天自动从 GitHub raw 拉取。

## 目录结构

### 入库（GitHub 可见）

| 路径 | 作用 |
|------|------|
| `root/*.yaml` | 11 个 rule-provider 规则文件。路由器运行时通过 OpenClash 自动从 GitHub raw 拉取，按 `payload:` 逐行匹配域名/IP 走对应代理组 |
| `README.md` | 本文件，仓库说明 |
| `overwrite/README.md` | 分流体系文档：规则优先级层次、出口设计、已知坑 |
| `.gitignore` | 排除本地/敏感文件 |

### 不入库（仅本机，.gitignore 排除）

| 路径 | 作用 |
|------|------|
| `config/` | 主配置文件（`Clash-smart-nofeisu-*.yaml`），含订阅 token、smart 参数、代理组定义。敏感，绝不入库 |
| `docs/` | 路由器 ImmortalWrt + OpenClash 体系速查文档，本机 Agent 共享，免重复排查 |
| `bench/` | 节点测试环境：mihomo Windows 内核、LightGBM 模型（`.bin`）、训练/测速 Python 脚本、geo 数据文件、缓存 |
| `logs/` | 本地排查/分析工作记录（BT_Tracker 待讨论材料等） |
| `.pi/` | 本机 pi Agent 技能定义（9 个 OpenClash 知识库 skill） |
| `.tmp/` | 临时文件（如 smart_weight_data.csv） |

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

1. 改 yaml → `git add <文件>` → commit（type: 规则）→ push
2. 手动热更新：`mihomo_api.py update <provider>` → 日志验证命中
