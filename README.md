# my_clash_rule

Clash/Mihomo 分流规则仓库。OpenClash rule-provider（`behavior: classical`），路由器每天自动从 GitHub raw 拉取。

## 目录结构

| 路径 | 用途 | 入库 |
|------|------|------|
| `root/*.yaml` | 11 个 rule-provider 规则文件 | ✅ |
| `config/` | 主配置（含订阅 token、smart 参数） | ❌ |
| `docs/` | 路由器 OpenClash 体系速查（Agent 共享） | ❌ |
| `bench/` | 节点测试（mihomo 内核、LightGBM 模型、训练/测速脚本、geo 数据） | ❌ |
| `logs/` | 本地排查/分析工作记录 | ❌ |
| `overwrite/` | 覆写模块文档（优先级/出口设计/已知坑） | ✅ |
| `.pi/` | 本机 Agent 技能定义 | ❌ |
| `.tmp/` | 临时文件 | ❌ |

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
