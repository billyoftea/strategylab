// API客户端配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ApiResponse<T> {
  data?: T
  error?: string
}

// 通用请求函数
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return { data }
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' }
  }
}

// 获取因子列表
export async function getFactors() {
  return fetchApi('/api/factors')
}

// 解析策略
export async function parseStrategy(message: string, currentParams: Record<string, any> = {}) {
  return fetchApi('/api/strategy/parse', {
    method: 'POST',
    body: JSON.stringify({
      message,
      current_params: currentParams,
    }),
  })
}

// 运行回测
export async function runBacktest(
  strategyParams: Record<string, any>,
  startDate: string = '2022-01-01',
  endDate: string = '2024-12-31'
) {
  return fetchApi('/api/backtest/run', {
    method: 'POST',
    body: JSON.stringify({
      strategy_params: strategyParams,
      start_date: startDate,
      end_date: endDate,
    }),
  })
}
