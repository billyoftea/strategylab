# StrategyLab Frontend

## 技术栈

- **框架**: Next.js 14 + React 18
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **图表**: Recharts
- **图标**: Lucide React

## 设计特点

### 视觉风格（参考Panda AI）
- **深色主题**: 专业金融感
- **配色方案**: 
  - 背景: `#0a0a0f` → `#12121a`
  - 主色: 蓝色 `#3b82f6`
  - 强调: 青色 `#06b6d4`
- **玻璃态效果**: backdrop-blur
- **渐变边框**: 按钮和卡片

### 交互设计
- **左侧对话**: 自然语言输入 + 选项选择
- **右侧预览**: 实时策略结构 + 代码
- **结果展示**: 核心指标卡片 + 收益曲线 + 深度分析

## 页面结构

```
app/
├── layout.tsx      # 根布局
├── page.tsx        # 主页面（Playground）
└── globals.css     # 全局样式
lib/
└── utils.ts        # 工具函数
```

## 开发

```bash
npm install
npm run dev
```

访问 http://localhost:3000

## 功能模块

1. **对话面板**
   - 消息历史
   - 选项选择（因子、持仓、频率）
   - 策略确认

2. **预览面板**
   - 策略参数展示
   - 代码预览

3. **结果面板**
   - 核心指标（年化收益、最大回撤、夏普、胜率）
   - 收益曲线图
   - 交易统计
   - LLM深度分析
