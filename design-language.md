# Paper Reviewer Match — Design Language

> 极简叙事 · 高度统一 · 物理真实感

---

## 三条原则

### 1. 克制色彩，内容是主角
整个界面只有一个有彩色的区域——蓝色 primary（`#2563eb`）。
其余全是中性灰。颜色只在三种情况出现：
- 主要动作按钮
- 状态语义（success / warning / danger）
- 链接

论文标题、作者名、分数——全用灰阶层次，而不是颜色区分。

### 2. 层次靠阴影，不靠边框
Apple 的卡片几乎没有可见边框（border opacity ≈ 8%），
层次感来自两层阴影：

```
ambient layer：大范围、低不透明度（模拟环境散射光）
key layer：    小范围、稍高不透明度（模拟直射光）
```

`--shadow-card` 额外加了微弱蓝色环境光，让白色卡片在灰底上不死板。

### 3. 动效有质量感
| 场景 | 曲线 | 时长 | 效果 |
|------|------|------|------|
| 卡片悬停 | `ease-smooth`（expo-out） | 220ms | 上浮 2px + 阴影加深 |
| 按钮按压 | `ease-default` | 120ms | 缩放到 0.97 |
| Badge/分数出现 | `ease-spring`（带过冲） | 500ms | 弹入，有质量感 |
| 列表项进入 | `ease-smooth` | 380ms | 淡入 + 上滑 12px |
| 模态出现 | `ease-spring` | 500ms | 从 scale(0.96) 弹到 1 |

弹簧曲线 `cubic-bezier(0.34, 1.56, 0.64, 1.00)` 会轻微过冲再回位，
这是 iOS 界面"有质量"的核心原因。

---

## Token 速查

### 颜色语义

| Token | 值 | 用途 |
|-------|----|------|
| `--background` | `#f5f5f7` | 页面底，Apple 标志性的"不是纯白"灰 |
| `--surface` | `#ffffff` | 卡片、面板 |
| `--surface-subtle` | `#f9f9fb` | 内嵌区域、代码块背景 |
| `--text-primary` | `#1c1c1e` | 正文（Apple dark gray，不用纯黑） |
| `--text-secondary` | `#6e6e73` | 次级文字、时间戳、元信息 |
| `--primary` | `#2563eb` | 唯一强调色 |
| `--border` | `rgba(0,0,0,0.08)` | 8% 不透明度，几乎看不见 |

### 圆角
`squircle` 感来自连续曲率，用较大圆角体现：
- 主卡片：`--radius` = 10px
- 模态/底抽屉：`--radius-2xl` = 28px
- 按钮：`--radius` = 10px（不用胶囊形，避免"玩具感"）
- Badge/tag：`--radius-sm` = 6px

### 字体
优先使用系统字体（SF Pro），原因：
1. 渲染质量最高（亚像素优化）
2. 中英文混排自动匹配（PingFang SC 接续）
3. 零加载时间

正文 14px，输入框 16px（防 iOS 双指缩放），
标题最大 24px（克制，不用大标题抢戏）。

---

## 组件规范（与 shadcn/ui 对接）

### Button
```
default  → bg-primary text-primary-foreground, shadow-sm, press-down
outline  → border bg-surface hover:bg-surface-subtle
ghost    → no border, hover:bg-surface-subtle
danger   → bg-danger text-white
```
所有 button 都带 `press-down` class（按压下沉效果）。

### Card
```
bg-surface shadow-card rounded-lg
内边距：px-5 py-4（20px / 16px）
hover 版本加 hover-lift
```

### Badge（匹配分数专用）
```
分数 ≥ 80：success-surface + success 文字
分数 60-79：warning-surface + warning 文字
分数 < 60：surface-subtle + text-secondary
出现时：anim-spring-in
```

### 导航栏
```
glass（毛玻璃）+ shadow-sm + sticky top-0
高度 56px，z-sticky
```

---

## 审稿匹配系统专属场景

### 匹配分数可视化
不用色温条，用同心圆弧（像 Apple Watch 活动环）：
- 外弧：overall match
- 中弧：topic overlap
- 内弧：recency（近三年发表相关论文加权）

### Reviewer 卡片
```
左侧：头像占位 + 姓名 + 机构（一行）
右侧：分数 Badge + "View profile" ghost button
展开：近期论文列表（3 条）+ 匹配理由（一段自然语言）
```

### 利益冲突标记
红色 `--danger` 小圆点 + tooltip，不用整行变红（避免恐慌感）。

---

## 不做什么

- 不用渐变色装饰背景
- 不用多种强调色（不要绿色 tag + 蓝色 tag + 紫色 tag 共存）
- 不用厚重边框（1px solid 已经嫌多）
- 不用 bounce 动画超过一次（弹入只用一次，不来回反弹）
- 不在表格里用斑马条纹（用悬停高亮代替）
