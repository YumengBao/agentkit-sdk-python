# AgentKit 非交互式配置指南

## 概述

AgentKit 现在支持三种配置模式：
- **交互式模式**：通过问答式界面逐步配置（默认）
- **非交互式模式**：通过命令行参数直接配置
- **混合模式**：部分参数通过命令行指定，其他交互式输入

## 使用场景

### 交互式模式（适合首次配置）

```bash
# 无参数运行，进入交互式配置向导
agentkit config
```

### 非交互式模式（适合脚本化/自动化）

#### 1. 完整配置示例

```bash
# 配置 Cloud 部署模式
agentkit config \
    --agent_name myAgent \
    --entry_point agent.py \
    --dependencies_file requirements.txt \
    --launch_type cloud \
    --region cn-beijing \
    --tos_bucket agentkit \
    --image_tag 0.0.1 \
    --runtime_envs VOLCENGINE_ACCESS_KEY=xxxxx-key \
    --runtime_envs VOLCENGINE_SECRET_KEY=xxxxx-key \
    --runtime_envs AGENTKIT_TOOL_ID=xxxxx-id
```

#### 2. 增量更新（只修改部分配置）

```bash
# 只修改入口文件
agentkit config --entry_point new_agent.py

# 只添加/更新环境变量
agentkit config \
    --runtime_envs NEW_KEY=new_value \
    --runtime_envs ANOTHER_KEY=another_value

# 修改多个配置项
agentkit config \
    --entry_point agent.py \
    --description "Updated description" \
    --image_tag 0.0.2
```

#### 3. 配置预览（Dry-run）

```bash
# 预览配置变更但不保存
agentkit config --entry_point agent.py --dry-run
```

### 混合模式

```bash
# 部分参数通过命令行指定，其他交互式输入
agentkit config --agent_name myAgent --interactive
```

### 查看当前配置

```bash
# 显示当前配置
agentkit config --show
```

## 参数说明

### 通用配置参数（CommonConfig）

| 参数 | 说明 | 示例 |
|------|------|------|
| `--agent_name` | Agent应用名称 | `myAgent` |
| `--entry_point` | 入口文件 | `agent.py` |
| `--description` | 应用描述 | `"My AI Agent"` |
| `--python_version` | Python版本 | `3.12` |
| `--dependencies_file` | 依赖文件 | `requirements.txt` |
| `--launch_type` | 部署模式 | `local`, `hybrid`, `cloud` |

### Workflow 配置参数

#### 环境变量配置（重要改进 ⭐）

AgentKit 现在支持两级环境变量配置：

| 参数 | 级别 | 说明 | 使用场景 |
|------|------|------|----------|
| `--runtime_envs` / `-e` | **应用级** | 所有部署模式共享的环境变量 | API密钥、模型端点等跨环境配置 |
| `--workflow-runtime-envs` | **Workflow级** | 仅当前部署模式使用的环境变量 | 调试标志、特定环境配置等 |

**使用示例**：

```bash
# 应用级环境变量（local/hybrid/cloud 都会使用）
agentkit config \
    -e API_KEY=my-api-key \
    -e MODEL_ENDPOINT=https://api.example.com

# Workflow 级环境变量（仅当前 launch_type 使用）
agentkit config \
    --workflow-runtime-envs DEBUG=true \
    --workflow-runtime-envs LOCAL_CACHE=/tmp/cache

# 混合使用
agentkit config \
    -e API_KEY=shared-key \
    --workflow-runtime-envs DEBUG=true
```

**配置合并规则**：
- 应用级环境变量会被所有 workflow 继承
- Workflow 级环境变量只在当前模式下生效
- 同名变量：Workflow 级会覆盖应用级

#### Cloud/Hybrid 模式参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--region` | 区域 | `cn-beijing` |
| `--tos_bucket` | TOS存储桶 | `agentkit` |
| `--image_tag` | 镜像标签 | `0.0.1` |
| `--ve_cr_instance_name` | 火山引擎 CR 实例名称 | `my-instance` |
| `--ve_cr_namespace_name` | 火山引擎 CR 命名空间 | `my-namespace` |
| `--ve_cr_repo_name` | 火山引擎 CR 仓库名称 | `my-repo` |

### 控制参数

| 参数 | 说明 |
|------|------|
| `--config` / `-c` | 指定配置文件路径 |
| `--interactive` / `-i` | 强制交互式模式 |
| `--dry-run` | 预览模式（不保存） |
| `--show` / `-s` | 显示当前配置 |

## 高级用法

### 1. 指定配置文件路径

```bash
agentkit config --config /path/to/custom/agentkit.yaml --entry_point agent.py
```

### 2. 环境变量最佳实践

```bash
# 应用级配置：API密钥等跨环境共享的配置
agentkit config \
    -e VOLCENGINE_ACCESS_KEY=xxxxx \
    -e VOLCENGINE_SECRET_KEY=xxxxx \
    -e MODEL_ENDPOINT=https://api.example.com

# 开发环境：添加调试配置
agentkit config \
    --launch_type local \
    --workflow-runtime-envs DEBUG=true \
    --workflow-runtime-envs LOG_LEVEL=debug

# 生产环境：使用生产级配置
agentkit config \
    --launch_type cloud \
    --workflow-runtime-envs LOG_LEVEL=info \
    --workflow-runtime-envs ENABLE_MONITORING=true
```

**优势**：API密钥只需配置一次（应用级），不同环境的特定配置分别管理

### 3. 配合其他命令使用

```bash
# 配置后立即构建
agentkit config --entry_point agent.py && agentkit build

# 在脚本中使用
#!/bin/bash
agentkit config \
    --agent_name myAgent \
    --entry_point agent.py \
    --launch_type local

if [ $? -eq 0 ]; then
    echo "配置成功"
    agentkit launch
fi
```

## 配置验证

非交互式配置会自动进行验证：

- ✅ **必填项检查**：确保必填字段不为空
- ✅ **格式验证**：验证字段格式（如 entry_point 必须是 .py 文件）
- ✅ **选项约束**：确保选择值在允许范围内（如 launch_type）

如果验证失败，会显示详细的错误信息并退出。

## 配置变更显示

非交互式配置会清晰显示配置变更：

```
通用配置 - 变更项:
┌───────────────────┬─────────────────┬─────────────────┐
│ 配置项            │ 原值            │ 新值            │
├───────────────────┼─────────────────┼─────────────────┤
│ entry_point       │ old_agent.py    │ new_agent.py    │
│ image_tag         │ 0.0.1           │ 0.0.2           │
└───────────────────┴─────────────────┴─────────────────┘

✅ 配置更新完成!
配置文件: /path/to/agentkit.yaml
```

## 最佳实践

1. **首次配置使用交互式模式**：更友好的引导体验
   ```bash
   agentkit config
   ```

2. **日常修改使用非交互式模式**：快速高效
   ```bash
   agentkit config --entry_point new_agent.py
   ```

3. **CI/CD 环境使用非交互式模式**：完全自动化
   ```bash
   agentkit config \
       --agent_name ${CI_PROJECT_NAME} \
       --entry_point agent.py \
       --image_tag ${CI_COMMIT_TAG}
   ```

4. **修改前先预览**：避免错误
   ```bash
   agentkit config --entry_point agent.py --dry-run
   ```

5. **查看当前配置**：确认状态
   ```bash
   agentkit config --show
   ```

## 常见问题

### Q: 如何知道需要配置哪些参数？

A: 使用 `agentkit config --help` 查看所有可用参数及其说明。

### Q: 环境变量会覆盖还是合并？

A: 环境变量会**合并**到现有配置中。如果键名相同，新值会覆盖旧值。

### Q: 如何重置配置？

A: 删除 `agentkit.yaml` 文件，然后重新运行 `agentkit config`。

### Q: 非交互式模式会验证配置吗？

A: 是的，所有配置都会经过验证，包括必填项检查和格式验证。

## 示例脚本

### 批量配置多个环境

```bash
#!/bin/bash

# 开发环境
agentkit config \
    --config dev/agentkit.yaml \
    --agent_name myAgent-dev \
    --image_tag dev \
    --runtime_envs ENV=development

# 测试环境
agentkit config \
    --config test/agentkit.yaml \
    --agent_name myAgent-test \
    --image_tag test \
    --runtime_envs ENV=testing

# 生产环境
agentkit config \
    --config prod/agentkit.yaml \
    --agent_name myAgent-prod \
    --image_tag v1.0.0 \
    --runtime_envs ENV=production
```

### CI/CD 集成示例

```yaml
# .github/workflows/deploy.yml
- name: Configure AgentKit
  run: |
    agentkit config \
      --agent_name ${{ github.repository }} \
      --entry_point agent.py \
      --launch_type cloud \
      --image_tag ${{ github.sha }} \
      --runtime_envs DEPLOY_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      
- name: Build and Deploy
  run: |
    agentkit launch
```

## 总结

非交互式配置让 AgentKit 更适合：
- ✅ 自动化脚本
- ✅ CI/CD 流水线
- ✅ 快速配置修改
- ✅ 批量配置管理

同时保持了交互式模式的友好体验，适合不同的使用场景。
