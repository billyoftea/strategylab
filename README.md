# StrategyLab

基于LLM的A股策略验证工具

## 项目简介

StrategyLab 是一个面向量化爱好者和金融学生的低代码策略验证平台。用户通过自然语言描述交易策略，系统自动完成回测并给出优化建议。

## 核心特性

- 🤖 **自然语言交互** - 用对话方式构建策略，无需编程
- 📊 **快速回测** - 基于Backtrader引擎，支持A股日线数据
- 🧠 **AI解读建议** - LLM分析回测结果，给出改进方向
- 💾 **本地存储** - 策略历史保存在浏览器，无需注册

## 技术栈

- 前端：Next.js + Tailwind CSS
- 后端：FastAPI + Python
- 回测：Backtrader
- 数据：AkShare / Tushare
- LLM：DeepSeek API

## 快速开始

```bash
# 克隆仓库
git clone git@github.com:billyoftea/strategylab.git
cd strategylab

# 安装依赖（后续补充）
```

## 项目状态

🚧 MVP开发中...

## 文档

- [产品需求文档](./docs/PRD.md)

## License

MIT
