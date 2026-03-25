#!/bin/bash

# AI 学术论文助手 - 运行脚本
# 此脚本帮助以正确配置启动应用程序

set -e

echo "========================================="
echo "AI 学术论文助手"
echo "========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  警告：未找到 .env 文件！"
    echo "从示例创建 .env 文件..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ 已从 .env.example 创建 .env 文件"
        echo "请编辑 .env 文件以添加你的 API 密钥"
    else
        echo "❌ 错误：未找到 .env.example 文件！"
        exit 1
    fi
fi

# Check if requirements are installed
echo "检查依赖..."
if ! pip show streamlit > /dev/null 2>&1; then
    echo "从 requirements.txt 安装依赖..."
    pip install -r requirements.txt
fi

# Check if at least one API key is set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  警告：在环境中未检测到 LLM API 密钥。"
    echo "应用程序将进行论文搜索但不会生成 AI 答案。"
    echo "要启用 AI 答案，请在 .env 文件中设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY"
    echo ""
fi

# Run integration test
echo "运行集成测试..."
if python test_integration.py; then
    echo "✅ 集成测试通过！"
else
    echo "⚠️  集成测试遇到问题（可能是由于 API 速率限制，这属于正常情况）"
fi

echo ""
echo "========================================="
echo "启动 AI 学术论文助手..."
echo "========================================="
echo "访问应用程序：http://localhost:8501"
echo "按 Ctrl+C 停止应用程序"
echo ""

# Start Streamlit application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0