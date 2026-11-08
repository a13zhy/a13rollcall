# A13Rollcall V6.8.2｜第六代A13引擎 PyQt重构版
> 🎲 A13Rollcall V6.8.2｜第六代A13抽取引擎｜课堂点名抽背系统

[![GitHub stars](https://img.shields.io/github/stars/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/fork)
[![Python Version](https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/releases)
[![License](https://img.shields.io/badge/license-NonCommercial-blue?style=flat-square)](#-开源许可)

🔥 **本地离线 PyQt5 GUI 点名抽背工具｜零广告｜零氪金｜无捆绑｜全部数据本地存储**

> V6.8.2 在 V6.8 的基础上把界面推到「专业桌面软件」水平：跟随系统字体与分辨率自动适配、统计面板重做、插件中心改为 ClassIsland 式目录插件、新增插件市场、权重可视化全面跟随皮肤。**完全兼容 V6.2 旧版数据**，直接复制 `students.txt`、`texts.txt` 即可迁移班级。

老师上课点名反复纠结，怕偏心、怕重复；学生上课走神，寄希望于「不会抽到我」。交给**第六代 A13 智能抽取引擎**，算法接管抽签，消除主观偏好，兼顾公平与薄弱学生强化练习。

---

## ✨ V6.8.2 更新要点

### 🖥 屏幕自适应（本版重点）
- ✅ **跟随系统字体大小自动缩放**：读取系统界面字号与 DPI，全局字号、行高、控件尺寸一起放大，不再出现「字大了但框没变高」
- ✅ **读取分辨率优化组件**：按屏幕可用宽度/高度计算页面边距、卡片内边距、容器间距、侧栏宽度、右栏宽度、按钮高度、标题字号
- ✅ 窗口初始尺寸与最小尺寸按分辨率推算，上限不超过可用区域，居中打开
- ✅ 修掉旧版启动卡死与「窗口越开越大」两个底层问题，冷启动稳定

### 📊 统计面板重设计
- ✅ 顶部指标卡：总抽取｜已背过｜未背熟｜未背过｜平均积分，大数字 + 彩点，一眼看完这堂课
- ✅ 上下分栏：上半「总览 / 积分 / 课文」三页图表，下半「抽取记录 / 学生明细」两页表格，可拖动分隔
- ✅ 轮次选择条：直接选历史轮次、看当前轮次数、危险色「删除此轮」
- ✅ 柱状图刻度改为整数步进，不再出现 0/0/1/1 这种重复刻度
- ✅ 表格列宽重排，课文列不再被挤成一条缝
- ✅ 图表与卡片全部跟随皮肤，暗色下不再白底刺眼

### 🧩 插件中心 · 插件市场（ClassIsland 式组织）
- ✅ 每个插件一个目录 + 一份 `manifest.json`，字段含 `id` / `name` / `version` / `author` / `description` / `icon` / `entry` / `permissions` / `tags`
- ✅ 插件中心双页签：**已安装** / **插件市场**
- ✅ 卡片式管理：图标、名称、版本徽章、作者、简介、启用开关、设置、运行、卸载
- ✅ 启用状态写入 `plugins/plugin_states.json`，重启后完全生效
- ✅ 插件市场：本地索引优先，读不到再尝试在线索引；连不上就安静地显示离线空态，不弹红字
- ✅ 安装支持目录、`.arcx`、`.arcxpkg`、`.zip`，解压后自动下钻找 manifest
- ✅ 版本比较、清单校验：缺字段、版本不兼容会在安装前提示

### 🎨 皮肤与视觉打磨
- ✅ **右侧学生权重全面跟随皮肤**：学生名、权重值、轨道底色、分段渐变都由皮肤取色，不再写死深灰
- ✅ 权重条固定高度，不再被压成一条细线
- ✅ SVG 图标改为纯描边渲染，暗色皮肤下不再被实心色块盖成黑块
- ✅ QSS 增加块级上下文重算：彩底按钮上的文字自动换成对比色
- ✅ 8 套皮肤统一回归：云白 / 夜曜 / 霓虹 / 极光 / 校园 / 纸上 / 极简 / 石墨

### ⚙️ 设置与插件工程化
- ✅ 设置窗口与主界面共用一套皮肤引擎，换肤后所有卡片、输入框、下拉框、页签同步刷新
- ✅ 插件异常隔离：插件报错只影响自己，不会带走主程序
- ✅ 关于页、版本号、页脚统一显示 6.8.2

---

## 💥 沿用的课堂能力（V6.8 起）

### 🎲 第六代 A13 智能抽取引擎
- 动态权重：背诵差、抽取少的学生自动提升被抽中概率，兼顾公平 + 补差训练
- 课堂轮次完整记录：每轮抽取存档，可查看历史轮次、恢复上一轮或指定轮次
- 课文维度统计：知道哪篇课文抽得太少
- 会话防重复 + 全局权重两套模式自由切换
- 抽取记录持久保存，重启不丢本节课历史
- 随机课文与抽取学生同步展示

### 🛠 课堂实用功能
1. **撤销 / 重做**：标记背诵状态、重置抽取、修改积分支持多级撤销（最多 50 步），`Ctrl+Z` / `Ctrl+Y`
2. **分组抽取**：自定义学生分组，只抽某一组，适合分层教学
3. **自动保存**：可自定义保存间隔，防断电丢数据
4. **课文右键菜单**：新增、编辑、上下移动、删除课文，不用手动改 txt
5. **系统托盘**：关闭窗口最小化到托盘，后台继续运行
6. **悬浮小窗**：不遮挡 PPT，随时一键抽取

### 📂 数据与兼容性
- **完全兼容 V6.2 旧版数据**：直接读取旧版 `students.txt`、`texts.txt`、ini 配置
- 配置、学生、课文、轮次历史本地 JSON 持久化
- 严格校验 UTF-8，自动过滤空行脏数据，防止「抽到空气同学」

---

## 🚀 快速上手

### 环境依赖
- Python `3.9` 及以上
- 依赖：`PyQt5`

```bash
pip install PyQt5
```

**运行程序**
```bash
# 主程序启动
python main_qt.py

# 新手配置向导
python wizard_launcher.py

# 可视化插件打包工具
python arcx_packager.py
```

> 运行后弹出 GUI 窗口，**非控制台操作**。

📦 不想装 Python：前往 [Releases](https://github.com/a13zhy/a13rollcall/releases) 下载打包好的安装包，直接双击使用。

### 班级数据准备
1. 旧版迁移：复制 V6.2 的 `students.txt`、`texts.txt` 到程序目录，启动自动加载。
2. 新建班级：
   - 「学生管理」批量粘贴名单，一行一名学生
   - 「课文管理」添加抽背课文；不需要抽背就不加课文，自动进入纯点名模式

---

## ⌨️ 常用快捷键
| 快捷键 | 功能 |
|---|---|
| 空格 | 开始抽取 |
| `Ctrl+Z` | 撤销操作 |
| `Ctrl+Y` / `Ctrl+Shift+Z` | 重做 |
| `Ctrl+S` | 手动保存全部数据 |
| `Ctrl+= / Ctrl+-` | 放大 / 缩小界面 |
| `Ctrl+0` | 重置界面缩放 100% |
| W | 切换动态权重开关 |
| ← / → | 切换上一篇 / 下一篇课文 |

---

## 🧩 插件开发（最简版）

一个插件就是一个目录：

```
plugins/
└─ 我的插件/
   ├─ manifest.json
   ├─ main.py
   └─ icon.png
```

`manifest.json`：

```json
{
  "id": "my_plugin",
  "name": "我的插件",
  "version": "1.0.0",
  "author": "你的名字",
  "description": "一句话说明这个插件做什么",
  "entry": "main.py",
  "permissions": [],
  "tags": ["课堂"]
}
```

`main.py`：

```python
def main(context):
    now = datetime.now()
    config = context.get_plugin_config()
    context.show_message(f"插件运行成功！当前时间:{now},你的配置:{config}")
```

执行环境已预注入 `datetime` / `json` / `os` / `random` / `re` 等常用模块，不用重复 import。
图形化搭建设置页可用 `arcx_packager.py`，拖拽模块后一键打包成 `.arcx`。

---

## 💡 课堂使用小技巧
1. **分层教学**：建学生分组，抽取时选中该组，只抽查这一层。
2. **课后复盘**：打开统计窗口，看轮次记录、课文抽查分布，找薄弱学生和薄弱篇目。
3. **投影上课**：开暗色主题 + 界面缩放；打开悬浮小窗，不遮课件。
4. **纯点名模式**：不导入课文，系统自动关闭抽背。
5. **插件扩展**：用可视化打包工具拖出设置页，写十几行逻辑就能做出自己的功能。

> 避坑提醒：导入外部 txt 必须 `UTF-8` 编码；名单、题库不要留多余空行。

---

## 📜 更新日志

### V6.8.2｜2026‑11‑08
- 🖥 新增屏幕自适应模块：跟随系统字体缩放、读取分辨率调整组件尺寸、窗口尺寸按分辨率推算
- 📊 统计面板整体重设计：指标卡 + 分栏图表 + 双页签表格 + 轮次选择条
- 🧩 插件中心重做：ClassIsland 式目录插件 + `manifest.json` + 卡片管理 + 启用开关
- 🛒 新增插件市场页签：本地索引优先、在线索引兜底、离线空态提示
- 🎨 右侧学生权重全面跟随皮肤，修掉写死字色、权重条压扁
- 🛠 修掉柱状图刻度重复、表格列宽挤压、SVG 图标参数报错、皮肤下 SVG 被色块遮盖
- 🐛 修掉冷启动卡死、窗口尺寸二次放大两个底层问题
- 📝 版本号、页脚、关于页统一到 6.8.2

### V6.8｜2026‑09‑26
- 🚀 整体迁移 PyQt5 重构，告别 Tkinter，全界面现代化
- 🎲 第六代引擎增强，新增课堂轮次历史系统，支持查看、加载、恢复历史轮次
- 📊 可视化统计图表：饼图、柱状图、抽取日志表格；课文维度统计
- 🛠 多级撤销 / 重做、自定义周期自动保存、全局界面缩放、学生分组抽取
- 🧩 插件系统升级：可视化拖拽打包编辑器、预注入常用标准库、插件管理页美化
- ⚙️ 设置系统重构：清理冗余项、动画全部生效、区分立即生效 / 需重启
- 🪟 系统托盘最小化后台运行；悬浮浮窗体验优化
- 🐛 修复动画设置不生效、datetime 导入报错、打包安装异常、绘图浮点数崩溃等

### V6.2｜2026‑08‑27
- 🚀 重磅升级第六代 A13 随机引擎，概率分配更科学
- 🔨 整体重构代码，架构清晰
- 🧙‍♂️ 新增交互式配置向导
- 🛡 强化数据校验，过滤空行脏数据
- 🪟 新增悬浮快捷浮窗
- ⌨️ 全套全局快捷键
- 🖥 全平台兼容性优化，降低闪退概率

---

## 💬 开发者碎碎念
坚持做面向一线教师的实用课堂工具，拒绝堆砌华而不实的鸡肋功能。全程本地离线运行，**不会上传任何学生名单、课堂数据到外网**。
永久免费用于教学，无广告无会员。
觉得好用请点 ⭐Star；BUG、课堂新需求欢迎提 Issue 与 PR。

---

## 📄 开源许可
本项目仅限**教育学习、个人教学场景使用**。
禁止直接打包倒卖、二次封装后用于商业盈利。二次改编分发请标注原项目与原作者。

> GitHub 仓库：[https://github.com/a13zhy/a13rollcall](https://github.com/a13zhy/a13rollcall)
> 项目下载页：[https://dkfile.istester.com/zhysppa13/a13callname.html](https://dkfile.istester.com/zhysppa13/a13callname.html)

## 👨‍💻 Author
a13zhy，二次创作、二次分发请标注原作者！

---

### 项目目录说明
```
a13rollcall_v6.8/
├─ main_qt.py                # PyQt5 主程序入口
├─ settings_window.py        # 设置窗口（分页 + 插件中心）
├─ stats_dialog.py           # 统计窗口（指标卡 + 图表 + 表格）
├─ skin_engine.py            # 皮肤引擎（配色 / QSS / SVG / 换肤）
├─ display_fit.py            # 屏幕自适应（字体、DPI、分辨率、布局尺寸）
├─ plugin_market.py          # 插件市场（manifest / 索引 / 安装卸载）
├─ plugin_manager.py         # 插件运行与沙箱
├─ stats_charts.py           # 统计图表绘制组件
├─ weight_visualization.py   # 权重可视化组件
├─ wizard_launcher.py        # 新手配置向导
├─ arcx_packager.py          # 可视化插件打包工具
├─ plugin_installer.py       # 插件安装程序
├─ constants.py              # 全局常量
├─ exceptions.py             # 异常定义
├─ modern_ui.py              # 通用现代化 UI 组件
├─ error_dialog.py           # 现代化错误弹窗（一键复制堆栈）
├─ operation_history.py      # 撤销重做管理器
├─ group_manager.py          # 学生分组管理
├─ visual_page_editor.py      # 插件可视化拖拽编辑器
├─ data_manager.py           # 数据持久化、轮次历史
├─ draw_engine.py            # 抽取引擎
├─ echo_hole.py              # 悬浮小窗
├─ config_manager.py         # 配置读写
└─ plugin_ui_injector.py     # 插件 UI 注入
```
