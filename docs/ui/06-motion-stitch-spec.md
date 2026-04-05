# FireSing 动效规范与 Stitch 实现规格

---

## 1. 动效规范

### 页面过渡
```css
@keyframes page-enter {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.duration: 200ms
.easing: ease-out
```

### 卡片交互
```css
.card-hover {
  transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
}
.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  border-color: #48484A;
}
.card-hover:active {
  transform: translateY(0);
  transition-duration: 100ms;
}
```

### 进度条动画
```css
/* 填充过渡 */
.progress-fill {
  transition: width 500ms ease-out;
}

/* 条纹动画 (处理中) */
@keyframes progress-stripes {
  0% { background-position: 1rem 0; }
  100% { background-position: 0 0; }
}
.progress-active {
  background-image: linear-gradient(
    45deg,
    rgba(255,255,255,0.12) 25%, transparent 25%,
    transparent 50%, rgba(255,255,255,0.12) 50%,
    rgba(255,255,255,0.12) 75%, transparent 75%,
    transparent
  );
  background-size: 1rem 1rem;
  animation: progress-stripes 0.5s linear infinite;
}
```

### 步骤脉冲
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.step-active-indicator {
  animation: pulse 2s ease-in-out infinite;
}
```

### 按钮反馈
```css
/* 点击缩放 */
.btn-primary:active { transform: scale(0.98); }

/* Loading spinner */
@keyframes spin {
  to { transform: rotate(360deg); }
}
.btn-loading::after {
  content: '';
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
```

### Toast 滑入/滑出
```css
@keyframes toast-in {
  from { transform: translateY(-100%); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}
@keyframes toast-out {
  from { transform: translateY(0); opacity: 1; }
  to   { transform: translateY(-100%); opacity: 0; }
}
.duration: 300ms
```

### 数字跳动（进度百分比）
```css
.number-animate {
  transition: all 300ms ease-out;
  font-variant-numeric: tabular-nums;
}
```

---

## 2. 全局时间参数

```
极快   100ms   按钮active、toggle
快速   150ms   hover变色、focus
标准   200ms   页面过渡、卡片hover
中速   300ms   步骤切换、toast滑入
慢速   500ms   进度条填充、modal出现
脉冲   2000ms  步骤指示器脉冲周期
```

---

## 3. 无障碍基础

- 所有按钮 `aria-label`
- 表单 `<label>` 关联
- 颜色对比度 ≥ 4.5:1 (WCAG AA)
  - #F5F5F7 on #000000 = 18.3:1 ✓
  - #98989D on #1C1C1E = 5.2:1 ✓
  - #FF6B35 on #000000 = 3.5:1 ⚠ (大文字可用)
  - #FF6B35 on #1C1C1E = 3.9:1 ✓
- 进度条 `role="progressbar"` + `aria-valuenow`
- 步骤列表 `role="list"` + `role="listitem"`
- focus-visible: 2px #0A84FF outline

---

## 4. Stitch 实现规格

### CSS 变量清单
```css
:root {
  /* 背景层级 */
  --surface-0: #000000;
  --surface-1: #1C1C1E;
  --surface-2: #2C2C2E;
  --surface-3: #3A3A3C;
  
  /* 文字 */
  --text-1: #F5F5F7;
  --text-2: #98989D;
  --text-3: #636366;
  
  /* 边框 */
  --border: #38383A;
  --divider: #48484A;
  
  /* 强调 */
  --accent: #FF6B35;
  --accent-hover: #FF6B35CC;
  --accent-bg: #FF6B351A;
  
  /* 状态 */
  --success: #30D158;
  --error: #FF453A;
  --warning: #FF9F0A;
  --info: #0A84FF;
  
  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* 阴影 */
  --shadow-card: 0 2px 12px rgba(0,0,0,0.4);
  --shadow-modal: 0 24px 80px rgba(0,0,0,0.6);
  --shadow-dropdown: 0 8px 24px rgba(0,0,0,0.5);
  
  /* 毛玻璃 */
  --glass-bg: rgba(28,28,30,0.72);
  --glass-blur: 20px;
}
```

### Tailwind 配置扩展
```js
// tailwind.config.ts
module.exports = {
  theme: {
    extend: {
      colors: {
        surface: { 0: '#000', 1: '#1C1C1E', 2: '#2C2C2E', 3: '#3A3A3C' },
        accent: '#FF6B35',
        success: '#30D158',
        error: '#FF453A',
        warning: '#FF9F0A',
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)'],
        mono: ['var(--font-geist-mono)'],
      },
      borderRadius: {
        'card': '12px',
        'modal': '16px',
      }
    }
  }
}
```

### 页面尺寸速查
```
Landing     max-w-7xl (1280px)
Dashboard   max-w-6xl (1152px)
Song Detail max-w-4xl (896px)
Processing  max-w-2xl (672px)
Login       w-96 (384px) 居中
Pricing     max-w-5xl (1024px)
Payment     max-w-lg (512px)
```

---

## 5. 设计参考

Apple HIG Dark Mode 参考:
- 系统 Settings app 的卡片分组风格
- Apple Music 的播放进度条
- App Store 的定价卡片
- Face ID 认证成功的动画 (完成态)

配色灵感:
- 主色调 #FF6B35 = "热力橙"，呼应 FireSing 的"火"元素
- 深色背景 = 专业创作工具感 (DaVinci Resolve, Logic Pro 风格)
- 高对比度文字 = 长时间使用不疲劳

案例参考:
- 抖音创作者服务中心 (竖版视频 + 深色)
- 剪映专业版 (创作工具 + 深色)
- Suno.ai (AI音乐 + 深色 + 橘色强调)
