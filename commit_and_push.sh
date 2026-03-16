#!/bin/bash
# 提交并推送所有更改到 GitHub

echo "📦 准备提交 ClawFlow 更新..."

# 检查 git 状态
echo "🔍 检查 Git 状态..."
git status

echo ""
echo "📝 添加所有更改..."
git add .

echo ""
echo "💾 提交更改..."
git commit -m "feat: 内置 Actor-Critic 自更新引擎

- 实现内置的演员-评论家机制
- 添加 YAML 配置文件定义行为
- 实现 3 轮迭代后暂停的受控模式
- 重构架构以避免外部监管进程
- 优化更新流程和评估逻辑"

echo ""
echo "📤 推送到 GitHub..."
git push origin master

echo ""
echo "✅ 完成！所有更改已推送至 GitHub"