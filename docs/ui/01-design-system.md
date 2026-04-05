# FireSing UI 设计系统 — 深色主题

> Apple HIG Dark Mode · Stitch-ready · 2026-04

---

## 1. 设计哲学

FireSing 是创作工具，界面要让用户"想上手试试"。深色主题降低视觉疲劳，突出内容本身。

三个原则：
1. **内容为王** — 歌词、波形、视频预览占据视觉重心，控件退居边缘
2. **状态透明** — 用户永远知道系统在干什么、卡在哪
3. **操作可逆** — 上传、分配、处理，每步都可以反悔

---

## 2. 调色板

### 基础色

```
背景层级:
  Surface-0   #000000  纯黑（页面底色）
  Surface-1   #1C1C1E  卡片底色（iOS 系统 card）
  Surface-2   #2C2C2E  悬浮层 / 侧边栏
  Surface-3   #3A3A3C  输入框底色

文字:
  Text-1      #F5F5F7  主文字（白灰，Apple 标准暗色文字）
  Text-2      #98989D  次要文字
  Text-3      #636366  占位符 / 禁用文字

边框与分割:
  Border      #38383A  卡片边框
  Divider     #48484A  分割线

高光（仅用于微妙的光泽感）:
  Highlight   rgba(255,255,255, 0.05)  卡片内微光
```

### 强调色

```
Primary      #FF6B35   暖橘（主操作按钮、进度条、关键高亮）
Primary/80   #FF6B35CC hover 态
Primary/20   #FF6B3533 按钮所在行高亮背景
Primary/10   #FF6B351A 极浅背景
```

### 状态色

```
Success      #30D158   Apple 暗色绿（完成/成功）
Error        #FF453A   Apple 暗色红（失败）
Warning      #FF9F0A   Apple 暗色橙（处理中）
Info         #0A84FF   Apple 暗色蓝（信息提示，仅此用途）
```

### 音色调色板（10色循环）

```
Voice-1   #FF6B6B   珊瑚红
Voice-2   #4ECDC4   薄荷绿
Voice-3   #45B7D1   天空蓝
Voice-4   #96CEB4   灰绿
Voice-5   #FFEAA7   淡金
Voice-6   #DDA0DD   梅紫
Voice-7   #F0E68C   卡其
Voice-8   #87CEEB   粉蓝
Voice-9   #FFA07A   浅鲑
Voice-10  #98D8C8   薄荷灰
```
超过 10 个音色时循环复用。在段落列表、字幕、进度步骤中统一使用。

---

## 3. 字体

```
标题    Geist Sans   600 (Semibold)   — SF Pro Display 等价，Next.js 已内置
正文    Geist Sans   400 (Regular)
次要    Geist Sans   400              color: #98989D
数字    Geist Mono   500 (Medium)     — 时间戳、行号、文件大小
代码    Geist Mono   400              — API 端点、技术信息
```

### 字号层级

```
Display    32px / 40px line-height   页面主标题
H1         24px / 32px               区域标题
H2         20px / 28px               卡片标题
H3         16px / 24px               小节标题
Body       14px / 20px               正文、表单标签
Caption    12px / 16px               辅助文字、时间戳、badge
Mono       13px / 18px               代码、时间范围、行号
```

---

## 4. 间距与圆角

### 间距（基数 4px）

```
xs   4px     组件内紧密元素
sm   8px     同组元素
md   16px    卡片内边距
lg   24px    区块间距
xl   32px    页面区域间距
2xl  48px    主要留白
3xl  64px    页面顶部留白
```

### 圆角

```
按钮 / 输入框     8px    rounded-lg
卡片              12px   rounded-xl
对话框 / Modal    16px   rounded-2xl
头像 / Badge      9999px rounded-full
进度条             4px    rounded
Tooltip           6px    rounded-md
```

---

## 5. 阴影与层级

```
卡片默认      无阴影，仅 1px #38383A 边框
卡片 hover    box-shadow: 0 2px 12px rgba(0,0,0,0.4)
Modal         box-shadow: 0 24px 80px rgba(0,0,0,0.6)
Dropdown      box-shadow: 0 8px 24px rgba(0,0,0,0.5)
Toast         box-shadow: 0 4px 16px rgba(0,0,0,0.3)
按钮          无阴影（扁平化）
```

深色模式下的阴影更深，因为背景本身就是深色。

---

## 6. 毛玻璃效果

```
Header     backdrop-filter: blur(20px) saturate(180%)
           background: rgba(28,28,30, 0.72)

Modal      backdrop-filter: blur(12px)
           background: rgba(0,0,0, 0.5)

Sidebar    backdrop-filter: blur(40px) saturate(200%)
           background: rgba(44,44,46, 0.65)
```
