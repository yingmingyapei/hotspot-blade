# httpx NO_PROXY 通配符陷阱（2026-06-13）

## 问题
`.env` 中设置 `NO_PROXY=*.xiaomimimo.com`，OpenAI Python客户端底层使用 httpx，httpx 不支持 NO_PROXY 通配符格式。

## 表现
- curl 直连小米API正常（curl支持通配符）
- cron进程调用OpenAI客户端报 `APIConnectionError: Connection error.`
- 重试3次均失败，手动触发也失败
- 当前交互session正常（因为gateway启动时环境不同）

## 根因
httpx 库的代理处理逻辑不识别 `*.domain.com` 通配符，只识别精确域名匹配。而 `curl` 支持通配符，所以 curl 测试正常但 OpenAI 客户端失败。

## 修复
```bash
# ❌ 错误：通配符不生效
NO_PROXY=localhost,127.0.0.1,*.xiaomimimo.com,*.dfcfs.com

# ✅ 正确：使用精确域名
NO_PROXY=localhost,127.0.0.1,token-plan-cn.xiaomimimo.com,mkapi2.dfcfs.com
```

## 验证方法
```python
import os
os.environ['https_proxy'] = 'http://127.0.0.1:10808'
os.environ['NO_PROXY'] = 'token-plan-cn.xiaomimimo.com'  # 精确域名

from openai import OpenAI
client = OpenAI(api_key=key, base_url='https://token-plan-cn.xiaomimimo.com/v1', timeout=10)
resp = client.chat.completions.create(model='mimo-v2.5-pro', messages=[{'role':'user','content':'说一个字'}], max_tokens=5)
# 应该成功
```

## 附加：Gateway重启要求
修改 `.env` 或 `config.yaml` 后，必须 `hermes gateway restart` 才能生效。gateway进程在启动时加载配置，运行期间不会热更新。
