'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, ChevronRight, BarChart3, Code, RotateCcw } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

// 类型定义
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'options' | 'strategy'
  options?: Option[]
  strategy?: Strategy
}

interface Option {
  field: string
  label: string
  values: { value: string | number; label: string }[]
}

interface Strategy {
  name: string
  params: Record<string, any>
  codePreview: string
}

interface BacktestResult {
  total_return: number
  annual_return: number
  max_drawdown: number
  sharpe_ratio: number
  total_trades: number
  win_rate: number
}

// 模拟数据
const mockEquityData = [
  { date: '2024-01', value: 100, benchmark: 100 },
  { date: '2024-02', value: 105, benchmark: 102 },
  { date: '2024-03', value: 103, benchmark: 101 },
  { date: '2024-04', value: 108, benchmark: 104 },
  { date: '2024-05', value: 112, benchmark: 103 },
  { date: '2024-06', value: 115, benchmark: 106 },
]

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '你好！我是 StrategyLab 策略助手。请描述你想验证的交易策略，比如："我想做一个60日动量轮动策略"',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentStrategy, setCurrentStrategy] = useState<Strategy | null>(null)
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'preview' | 'result'>('chat')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // 模拟API响应
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '我理解了你的策略想法。为了更准确地回测，请确认以下参数：',
        type: 'options',
        options: [
          {
            field: 'factor_name',
            label: '因子类型',
            values: [
              { value: 'mom_20', label: '20日动量（短期）' },
              { value: 'mom_60', label: '60日动量（中期）' },
              { value: 'mom_120', label: '120日动量（长期）' },
            ],
          },
          {
            field: 'top_n',
            label: '持仓数量',
            values: [
              { value: 30, label: '前30只' },
              { value: 50, label: '前50只' },
              { value: 100, label: '前100只' },
            ],
          },
          {
            field: 'rebalance_freq',
            label: '调仓频率',
            values: [
              { value: 'weekly', label: '周频' },
              { value: 'monthly', label: '月频' },
            ],
          },
        ],
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1000)
  }

  // 选择选项
  const handleSelectOption = (field: string, value: string | number) => {
    const strategy: Strategy = {
      name: '60日动量轮动策略',
      params: {
        factor_name: field === 'factor_name' ? value : 'mom_60',
        top_n: field === 'top_n' ? value : 50,
        rebalance_freq: field === 'rebalance_freq' ? value : 'monthly',
      },
      codePreview: `# 60日动量轮动策略
factor_name = "mom_60"  # 60日动量
top_n = 50  # 持仓数量
rebalance_freq = "monthly"  # 调仓频率

# 策略逻辑
1. 按60日动量对所有股票排序
2. 选取前50只股票
3. 每月调仓一次
4. 等权配置`,
    }

    setCurrentStrategy(strategy)
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: '策略已确认！你可以查看右侧的策略预览，或点击"开始回测"。',
        type: 'strategy',
        strategy,
      },
    ])
    setActiveTab('preview')
  }

  // 运行回测
  const handleBacktest = () => {
    setIsLoading(true)
    setTimeout(() => {
      setBacktestResult({
        total_return: 0.25,
        annual_return: 0.15,
        max_drawdown: 0.18,
        sharpe_ratio: 1.2,
        total_trades: 120,
        win_rate: 0.58,
      })
      setIsLoading(false)
      setActiveTab('result')
    }, 2000)
  }

  // 格式化百分比
  const formatPct = (v: number) => `${(v * 100).toFixed(1)}%`

  return (
    <div className="flex h-screen bg-background">
      {/* 左侧：对话面板 */}
      <div className="flex-1 flex flex-col border-r border-border">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-text-primary">StrategyLab</h1>
              <p className="text-xs text-text-muted">AI策略验证</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'bg-surface-active text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              对话
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                activeTab === 'preview'
                  ? 'bg-surface-active text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              预览
            </button>
            <button
              onClick={() => setActiveTab('result')}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                activeTab === 'result'
                  ? 'bg-surface-active text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              结果
            </button>
          </div>
        </header>

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-primary text-white'
                    : 'bg-surface text-text-primary'
                }`}
              >
                <p className="text-sm leading-relaxed">{msg.content}</p>

                {/* 选项按钮 */}
                {msg.type === 'options' && msg.options && (
                  <div className="mt-4 space-y-3">
                    {msg.options.map((opt) => (
                      <div key={opt.field}>
                        <p className="text-xs text-text-secondary mb-2">{opt.label}</p>
                        <div className="flex flex-wrap gap-2">
                          {opt.values.map((v) => (
                            <button
                              key={v.value}
                              onClick={() => handleSelectOption(opt.field, v.value)}
                              className="px-3 py-1.5 rounded-md bg-background-secondary border border-border hover:border-primary hover:text-primary transition-colors text-sm"
                            >
                              {v.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 策略确认 */}
                {msg.type === 'strategy' && msg.strategy && (
                  <div className="mt-4">
                    <button
                      onClick={handleBacktest}
                      disabled={isLoading}
                      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-accent rounded-lg text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                    >
                      {isLoading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          回测中...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-4 h-4" />
                          开始回测
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入框 */}
        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="描述你的策略想法..."
              className="flex-1 bg-surface border border-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="px-4 py-3 bg-primary rounded-xl text-white hover:bg-primary-dark transition-colors disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* 右侧：预览/结果面板 */}
      <div className="w-[480px] bg-background-secondary flex flex-col">
        {activeTab === 'preview' && currentStrategy && (
          <>
            <div className="px-6 py-4 border-b border-border">
              <h2 className="font-semibold text-text-primary flex items-center gap-2">
                <Code className="w-4 h-4" /
                策略预览
              </h2>
            </div>
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="space-y-4">
                <div className="bg-surface rounded-xl p-4 border border-border">
                  <h3 className="text-sm font-medium text-text-secondary mb-3">策略参数</h3>
                  <div className="space-y-2">
                    {Object.entries(currentStrategy.params).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-sm">
                        <span className="text-text-muted">{k}</span>
                        <span className="text-text-primary font-mono">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-surface rounded-xl p-4 border border-border">
                  <h3 className="text-sm font-medium text-text-secondary mb-3">代码预览</h3>
                  <pre className="text-xs font-mono text-text-primary overflow-x-auto">
                    {currentStrategy.codePreview}
                  </pre>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'result' && backtestResult && (
          <>
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h2 className="font-semibold text-text-primary flex items-center gap-2">
                <BarChart3 className="w-4 h-4" /
                回测结果
              </h2>
              <button
                onClick={() => setActiveTab('chat')}
                className="text-xs text-text-secondary hover:text-text-primary flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" /
                重新测试
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* 核心指标 */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface rounded-xl p-4 border border-border">
                  <p className="text-xs text-text-muted mb-1">年化收益</p>
                  <p className={`text-2xl font-bold ${backtestResult.annual_return > 0 ? 'text-success' : 'text-danger'}`}>
                    {formatPct(backtestResult.annual_return)}
                  </p>
                </div>
                <div className="bg-surface rounded-xl p-4 border border-border">
                  <p className="text-xs text-text-muted mb-1">最大回撤</p>
                  <p className="text-2xl font-bold text-danger">{formatPct(backtestResult.max_drawdown)}</p>
                </div>
                <div className="bg-surface rounded-xl p-4 border border-border">
                  <p className="text-xs text-text-muted mb-1">夏普比率</p>
                  <p className="text-2xl font-bold text-primary">{backtestResult.sharpe_ratio.toFixed(2)}</p>
                </div>
                <div className="bg-surface rounded-xl p-4 border border-border">
                  <p className="text-xs text-text-muted mb-1">胜率</p>
                  <p className="text-2xl font-bold text-accent">{formatPct(backtestResult.win_rate)}</p>
                </div>
              </div>

              {/* 收益曲线 */}
              <div className="bg-surface rounded-xl p-4 border border-border">
                <h3 className="text-sm font-medium text-text-secondary mb-4">收益曲线</h3>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={mockEquityData}>
                      <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2d2d40" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                      <YAxis stroke="#64748b" fontSize={10} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e1e2e',
                          border: '1px solid #2d2d40',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#3b82f6"
                        fillOpacity={1}
                        fill="url(#colorValue)"
                      />
                      <Line
                        type="monotone"
                        dataKey="benchmark"
                        stroke="#64748b"
                        strokeDasharray="5 5"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* 交易统计 */}
              <div className="bg-surface rounded-xl p-4 border border-border">
                <h3 className="text-sm font-medium text-text-secondary mb-4">交易统计</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-xs text-text-muted">总交易</p>
                    <p className="text-lg font-semibold text-text-primary">{backtestResult.total_trades}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">总收益</p>
                    <p className="text-lg font-semibold text-success">{formatPct(backtestResult.total_return)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">盈亏比</p>
                    <p className="text-lg font-semibold text-text-primary">1.4</p>
                  </div>
                </div>
              </div>

              {/* 策略分析 */}
              <div className="bg-surface rounded-xl p-4 border border-border">
                <h3 className="text-sm font-medium text-text-secondary mb-4">策略分析</h3>
                <div className="space-y-4 text-sm">
                  <div>
                    <h4 className="text-text-primary font-medium mb-2">📊 策略表现总结</h4>
                    <p className="text-text-secondary leading-relaxed">
                      策略采用60日动量因子进行选股，回测期内年化收益15%，跑赢基准。
                      夏普比率1.2，风险调整后收益良好。最大回撤18%，在可接受范围内。
                    </p>
                  </div>
                  <div>
                    <h4 className="text-text-primary font-medium mb-2">⚠️ 潜在风险点</h4>
                    <ul className="text-text-secondary space-y-1 list-disc list-inside">
                      <li>动量策略在风格切换时可能面临较大回撤</li>
                      <li>月频调仓可能错过短期动量变化</li>
                      <li>等权配置未考虑个股流动性差异</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-text-primary font-medium mb-2">💡 改进建议</h4>
                    <ul className="text-text-secondary space-y-1 list-disc list-inside">
                      <li>考虑加入市场趋势过滤器，避免熊市满仓</li>
                      <li>测试不同调仓频率对收益的影响</li>
                      <li>加入波动率加权，降低高波动股票权重</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {!currentStrategy && activeTab !== 'chat' && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Sparkles className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">在左侧描述你的策略想法</p>
              <p className="text-text-muted text-sm mt-2">例如："我想做一个60日动量轮动策略"</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
