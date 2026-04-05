# FireSing 组件规范 — 深色主题

---

## 1. 按钮

### 主按钮 (Primary)
```
┌─────────────────────────────────┐
│         开始处理                 │
│  bg: #FF6B35                    │
│  text: #FFFFFF                  │
│  h-10 px-6 rounded-lg           │
│  font-medium text-sm            │
│  hover: bg #FF6B35CC            │
│  active: scale(0.98)            │
│  disabled: opacity 0.4          │
└─────────────────────────────────┘
```

### 次按钮 (Secondary)
```
┌─────────────────────────────────┐
│         Round-Robin             │
│  bg: transparent                │
│  text: #F5F5F7                  │
│  border: 1px #48484A           │
│  hover: bg #2C2C2E             │
└─────────────────────────────────┘
```

### 危险按钮 (Destructive)
```
┌─────────────────────────────────┐
│         删除歌曲                 │
│  bg: transparent                │
│  text: #FF453A                  │
│  border: 1px #FF453A66         │
│  hover: bg #FF453A1A           │
└─────────────────────────────────┘
```

### 图标按钮 (Icon Button)
```
圆形按钮: 36×36px, rounded-full
背景: transparent 或 #2C2C2E
图标: 16px, color #98989D
hover: bg #3A3A3C, icon color #F5F5F7
```

---

## 2. 卡片

### 基础卡片
```
┌──────────────────────────────────┐
│  bg: #1C1C1E                    │
│  border: 1px solid #38383A      │
│  border-radius: 12px            │
│  padding: 24px                  │
│                                 │
│  hover →                        │
│    border-color: #48484A        │
│    box-shadow: 0 2px 12px       │
│    rgba(0,0,0,0.4)              │
└──────────────────────────────────┘
```

### 歌曲卡片（可点击）
```
┌──────────────────────────────────┐
│  🎵 歌曲标题                     │
│  ● 已上传        2024/04/04     │
│                                  │
│  bg: #1C1C1E                    │
│  hover → translateY(-2px)       │
│          shadow + border亮       │
│  cursor: pointer                │
│  transition: all 200ms ease     │
└──────────────────────────────────┘
```

### 卡片内嵌微光（Apple 风格）
```css
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255,255,255,0.06), 
    transparent
  );
}
```

---

## 3. 状态 Badge

```
完成态:
  ┌──────────┐
  │ ✓ 完成   │  bg: #30D1581A  text: #30D158  dot: #30D158
  └──────────┘

处理中:
  ┌──────────┐
  │ ● 处理中  │  bg: #FF9F0A1A  text: #FF9F0A  dot: #FF9F0A (脉冲动画)
  └──────────┘

错误态:
  ┌──────────┐
  │ ✗ 失败   │  bg: #FF453A1A  text: #FF453A  dot: #FF453A
  └──────────┘

空闲态:
  ┌──────────┐
  │ ○ 已上传  │  bg: #2C2C2E   text: #98989D  dot: #636366
  └──────────┘

尺寸: h-6 px-2.5 rounded-full text-xs font-medium
```

---

## 4. 输入框

```
┌─────────────────────────────────┐
│ 请输入独白文本...                │
│ bg: #3A3A3C                    │
│ border: 1px #48484A            │
│ border-radius: 8px              │
│ padding: 10px 14px              │
│ font-size: 14px                 │
│ color: #F5F5F7                  │
│ placeholder: #636366            │
│                                 │
│ focus → border: #FF6B35         │
│         box-shadow: 0 0 0 3px   │
│         #FF6B3533               │
└─────────────────────────────────┘
```

### 下拉菜单（Select）
```
触发器: 同输入框样式 + 右侧 chevron-down 图标
展开面板:
  bg: #2C2C2E
  border: 1px #48484A
  rounded-lg
  shadow: 0 8px 24px rgba(0,0,0,0.5)
  
  选项:
    padding: 8px 12px
    hover: bg #3A3A3C
    selected: bg #FF6B351A, text #FF6B35
```

---

## 5. 文件上传区域

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                                 │
│       将音频文件拖到这里         │
│    或点击选择文件                │
│                                 │
│    MP3 / WAV / FLAC · 50MB     │
│                                 │
│  border: 2px dashed #48484A    │
│  border-radius: 12px            │
│  min-height: 160px              │
│  bg: #1C1C1E                   │
│                                 │
│  hover → border: #636366        │
│                                 │
│  drag-over →                    │
│    border-color: #FF6B35        │
│    background: #FF6B350D        │
│    图标变色: #FF6B35            │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘

上传中态:
  虚线变实线，区域内部显示:
  ┌─────────────────────────────┐
  │  song.mp3                   │
  │  ████████████░░░░  67%      │
  │  33.5MB / 50MB              │
  └─────────────────────────────┘
```

---

## 6. Toast 通知

```
顶部居中，距顶 16px

成功: bg #30D1581A, border #30D15833, text #30D158
错误: bg #FF453A1A, border #FF453A33, text #FF453A
信息: bg #0A84FF1A, border #0A84FF33, text #0A84FF

高度: 44px
圆角: 10px
左侧图标 + 文字
5 秒后自动消失（滑出动画）
```

---

## 7. Modal / 对话框

```
背景遮罩: rgba(0,0,0,0.5) + backdrop-filter: blur(12px)

对话框:
  bg: #2C2C2E
  border-radius: 16px
  padding: 24px
  max-width: 480px
  box-shadow: 0 24px 80px rgba(0,0,0,0.6)
  顶部微光线: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)

标题区: 20px Semibold, #F5F5F7, 右上角 ✕ 关闭按钮
内容区: 14px Regular, #98989D
操作区: 右对齐，次按钮 + 主按钮
```

---

## 8. 进度条

```
轨道:
  bg: #3A3A3C
  height: 8px (非 Tailwind 默认 4px)
  border-radius: 4px

填充:
  渐变: left #FF6B35 → right #FF9F0A
  完成态: #30D158
  失败态: #FF453A
  transition: width 500ms ease-out

条纹动画 (处理中):
  45deg 斜条纹, rgba(255,255,255,0.12)
  animation: 0.5s linear infinite
```
