# Pull Request 管理指南

## 分支管理策略

### 分支命名规范

```
feature/<功能名称>
bugfix/<问题描述>
hotfix/<紧急修复>
refactor/<重构内容>
docs/<文档更新>
```

示例：
- `feature/user-authentication`
- `bugfix/login-timeout`
- `hotfix/critical-security-patch`

## PR 创建流程

### 1. 创建分支

```bash
git checkout -b feature/my-new-feature
```

### 2. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能"
```

### 3. 提交规范

#### Commit 消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建/工具变动

#### 示例

```
feat(api): 添加用户认证接口

- 添加登录接口
- 添加注册接口
- 添加Token验证

Closes #123
```

## PR 审查流程

### 1. PR 描述模板

```markdown
## 描述
[简要描述本次变更]

## 变更类型
- [ ] 新功能 (feat)
- [ ] 修复bug (fix)
- [ ] 重构 (refactor)
- [ ] 文档更新 (docs)

## 影响的范围
[描述变更影响的功能模块]

## 测试情况
- [ ] 已添加测试
- [ ] 本地测试通过
- [ ] 无需测试

## Checklist
- [ ] 代码遵循项目规范
- [ ] 已更新相关文档
- [ ] PR 标题清晰明了
```

### 2. 审查要点

#### 代码审查
- [ ] 代码逻辑正确
- [ ] 没有安全漏洞
- [ ] 性能表现良好
- [ ] 错误处理完善

#### 代码风格
- [ ] 遵循 PEP8 (Python)
- [ ] 遵循 ESLint (JavaScript/TypeScript)
- [ ] 命名规范清晰
- [ ] 注释适度

#### 测试
- [ ] 新功能有测试
- [ ] 现有测试通过
- [ ] 测试覆盖率未下降

## PR 合并

### 合并条件

- [ ] 至少 1 人审批通过
- [ ] 所有 CI 检查通过
- [ ] 没有冲突
- [ ] 测试全部通过

### 合并方式

- **Squash and merge**: 推荐用于功能分支
- **Merge commit**: 用于保留完整历史
- **Rebase and merge**: 用于保持线性历史

## Issue 关联

在 PR 描述中使用以下关键词自动关联 Issue：

- `Closes #123`
- `Fixes #123`
- `Resolves #123`

## 常见问题

### Q: 如何处理冲突？

```bash
git fetch origin
git rebase origin/main
# 解决冲突后
git add .
git rebase --continue
```

### Q: PR 需要多少审批？

- 普通 PR: 至少 1 人审批
- 核心模块变更: 至少 2 人审批
- 紧急修复: 可先合并后审查

### Q: 如何撤回 PR？

```bash
git push origin --delete feature/my-feature
```

或在 GitHub 页面点击 "Close pull request"
