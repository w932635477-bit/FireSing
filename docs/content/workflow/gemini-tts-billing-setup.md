# Gemini TTS 付费开通指南（中国用户，无信用卡）

> 目标：开通 Google Cloud 付费账户，使用 Gemini 2.5 Flash TTS（高质量多声音 TTS）
> 前提：已有科学上网工具，已有 Google 账号

## 当前状况

- 项目已有 Gemini API Key（Google AI Studio 免费层）
- 免费层有 rate limit 和用量限制，需要付费层才能稳定生产
- Gemini TTS 通过 Vertex AI 调用，需要 Google Cloud Billing 账户
- 中国用户没有国际信用卡，需要虚拟信用卡

## Step 1：开通虚拟信用卡

### 方案对比（2026 年 4 月）

| 平台 | 开卡费 | 充值方式 | Visa/MC | 稳定性 |
|------|--------|----------|---------|--------|
| DuPay | ~$10/年 | USDT/支付宝 | Visa | 稳定 |
| PokePay | 免费 | USDT/支付宝 | Visa | 稳定 |
| CoinPay | ~$5 | USDT/支付宝 | MC | 较新 |
| WasabiCard | ~$10 | USDT | Visa | 稳定 |

**推荐 DuPay**（支付宝直接充值，不需要 USDT）

### DuPay 开卡步骤

1. 访问 dupay.one（需要科学上网）
2. 注册账号（邮箱 + 手机验证）
3. 完成身份认证（护照/身份证）
4. 开通 Visa 虚拟卡（选 1 年期，约 $10）
5. 用支付宝充值 $20-50（够用几个月）
6. 记录卡号、有效期、CVV、账单地址

### PokePay 开卡步骤（备选）

1. 访问 pokepay.jp
2. 注册账号
3. 完成身份认证
4. 免费开卡
5. USDT 或支付宝充值

## Step 2：注册 Google Cloud 并开通 Billing

1. 科学上网（美国/日本节点，不要用香港）
2. 访问 console.cloud.google.com
3. 用现有 Google 账号登录
4. 如果是第一次使用，会提示设置 Billing：
   - 账号类型选「个人」
   - 付款方式选「信用卡或借记卡」
   - 输入虚拟卡的：卡号、有效期、CVV
   - 账单地址填虚拟卡提供的美国地址
5. Google 会做 $1 预授权验证（几分钟后退回）
6. 验证通过后 Billing 激活

### 常见问题

**Q: 虚拟卡被拒？**
- 换美国节点 VPN
- 确认虚拟卡余额 > $1
- 账单地址必须和虚拟卡注册地址一致
- 如果 DuPay 不行，换 PokePay 试

**Q: 需要绑定真实地址吗？**
- 不需要。虚拟卡会提供一个美国地址，填那个就行。

**Q: 会被封号吗？**
- 正常使用不会。Google Cloud 检测的是欺诈行为（大量免费 trial 滥用），不是虚拟卡本身。

## Step 3：启用 Vertex AI API

1. 进入 Google Cloud Console
2. 搜索「Vertex AI API」
3. 点击「启用」
4. 确认计费项目正确

## Step 4：创建 Service Account（API 调用用）

```bash
# 安装 gcloud CLI（如果没装）
# https://cloud.google.com/sdk/docs/install

# 登录
gcloud auth login

# 设置项目
gcloud config set project YOUR_PROJECT_ID

# 创建 Service Account
gcloud iam service-accounts create gemini-tts \
  --display-name="Gemini TTS Service Account"

# 授予 Vertex AI 权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:gemini-tts@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# 生成 Key 文件
gcloud iam service-accounts keys create ~/gemini-tts-key.json \
  --iam-account=gemini-tts@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Step 5：配置环境变量

在 `docs/content/.env` 中添加：

```bash
# Google Cloud Vertex AI (付费版 TTS)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/gemini-tts-key.json"
```

## Step 6：验证付费 TTS 可用

```bash
source docs/content/.env

# 测试 Vertex AI TTS（需要安装 google-cloud-aiplatform）
pip install google-cloud-aiplatform

python3 -c "
from google.cloud import aiplatform
from vertexai.preview.tts import TextToSpeechClient
print('Vertex AI TTS 连接成功')
"
```

## 费用估算

| 用途 | 月用量 | 预估费用 |
|------|--------|----------|
| Medvi 视频 TTS | ~50 段/月 × 500 字 | $2-5 |
| Sings 视频 TTS | ~30 段/月 × 300 字 | $1-3 |
| 测试调试 | ~20 次 | $0.5 |
| **合计** | | **$3-8/月（约 ¥25-60）** |

Gemini 2.5 Flash TTS 定价参考：
- 输入：$0.075 / 1M 字符
- 输出音频：免费（限时）或极低

## 下一步

完成以上步骤后：
1. 把 `GOOGLE_CLOUD_PROJECT` 和 key 文件路径写入 `.env`
2. 告诉我，我来写 Gemini TTS 的集成代码（替换现有 MiniMax）

## 参考链接

- [DuPay 官网](https://dupay.one)
- [PokePay 官网](https://pokepay.jp)
- [Google Cloud Console](https://console.cloud.google.com)
- [Vertex AI TTS 文档](https://cloud.google.com/text-to-speech/docs)
- [WildCard 替代方案汇总](https://bayase.com/post/wildcard-login-error-alternative/)
