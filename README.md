# a13rollcall
> 🎲 第六代A13引擎｜专治课堂摸鱼的开源点名抽背神器

[![GitHub stars](https://img.shields.io/github/stars/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/fork)
[![Python Version](https://img.shields.io/badge/python-3.8+-3776AB?style=flat-square)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/releases)
[![License](https://img.shields.io/badge/license-OpenSource‑NonCommercial‑blue?style=flat-square)](#-开源许可)

🔥 **告别人工点名精神内耗！离线本地运行｜零广告｜零氪金｜无乱七八糟捆绑**

上课点名全靠直觉？学生总赌自己是“天选摸鱼人”？
交给**A13第六代随机引擎**，抽签全看运气，拒绝人情滤镜，开盲盒式点名，课堂氛围感直接拉满✨

---

## 💥 谁懂啊！课堂两大永恒痛点
- 👨‍🏫 **老师侧：点名选择困难症**
  纠结点谁，怕偏心、怕重复，点名半节课，讲课五分钟。
- 👩‍🎓 **学生侧：摸鱼侥幸心理**
  低头神游，内心疯狂祈祷：千万别点我！

于是 `a13rollcall` 诞生！
> 不看心情，不凭印象，**算法说了算，人人机会均等**，击碎摸鱼幻想，拯救老师的选择困难。

---

## ✨ 项目亮点
### 🎲 第六代 A13 自研随机引擎
拒绝地摊伪随机！专门优化抽签逻辑：
- ❌ 杜绝同一个人连续“中奖”
- ❌ 拒绝扎堆点名、长期透明人
- ✅ 概率分布均衡，真正公平开盲盒，没有暗箱操作

### 📚 点名 + 抽背 双模式一体
一套程序搞定多种课堂场景，不用来回切软件：
- **随机点名**：课堂提问、作业抽查、值日抽签、小组选人
- **随机抽背**：课文背诵、知识点默写、习题抽查，专治摆烂不背书

### 🧱 模块化解耦架构，不是玩具堆砌代码
结构清晰，新手看得懂，大佬随便魔改二次开发：
- `draw_engine.py` — A13核心抽签引擎
- `data_manager.py` — 名单&题库读取、清洗校验
- `config_manager.py` — 全局配置管理
- `wizard_launcher.py` — 交互式新手向导
- `main.py` — 主程序调度入口

### ⚡ 极致轻量化
纯 Python 标准库实现，**零第三方依赖**。
无需联网、不用安装一堆包，老办公电脑也能秒开，拒绝卡顿闪退。

### 🎛️ 自由度拉满
完全自定义：班级名单、抽背题库、单次抽取人数、去重开关，中小学/培训机构全部适配。

---

## 📁 项目文件结构
```
a13rollcall/
├── main.py               # 主程序入口｜极速启动
├── wizard_launcher.py    # 新手向导｜交互式傻瓜操作
├── config_manager.py     # 配置中心｜个性化规则
├── data_manager.py       # 数据处理｜名单题库校验
├── draw_engine.py        # A13第六代核心随机引擎
├── students.txt         # 学生名单库（自行编辑）
├── texts.txt            # 抽背题目库（自行编辑）
└── README.md            # 项目说明文档
```

---

## 🚀 快速上手

### 环境要求
- Python `3.8` 及以上
> 无pip依赖，开箱即用。

### 1️⃣ 拉取项目
```bash
git clone https://github.com/a13zhy/a13rollcall.git
cd a13rollcall
```

### 2️⃣ 填入你的数据
- `students.txt`：**一行一个姓名**，不要空行、多余空格，不然会抽中空气😂
- `texts.txt`：一行一道题目/背诵片段，按需填充。

### 3️⃣ 两种启动姿势
```bash
# 老玩家：直接冲主程序
python main.py

# 小白玩家：向导模式，一步步带你玩
python wizard_launcher.py
```

> 📦 不想装Python？直接去 [Releases](https://github.com/a13zhy/a13rollcall/releases) 下载打包好的exe，双击直接跑。

---

## ⚙️ 高阶玩法
修改/通过程序配置中心开启能力：
- ✅ 开启去重：避免同一个倒霉蛋连续被点名，雨露均沾
- ✅ 设置单次抽取人数：单人拷问 / 批量拷打自由切换
- ✅ 自定义输出提示文案，玩出你的风格
- ✅ 内置脏数据过滤，自动跳过空行垃圾内容，防止程序翻车

## 💡 老玩家私藏小技巧
1. **纯点名模式**：直接清空 `texts.txt`，自动关闭抽背，只玩点名。
2. **极速扫荡模式**：关闭去重，适合快速轮询全班。
3. ⚠️ 编码避坑：txt文件保存为 **UTF‑8**，防止中文乱码。
4. ❗不要留空行，不然会随机抽中“空气同学”。

---

## 📜 更新日志
### V6.0 ｜ 2026‑08‑27
- 🚀 升级 **第六代A13随机引擎**，概率分配更科学
- 🔨 整体重构代码，结构更整洁，可读性大幅提升
- 🧙 新增交互式向导启动，零基础友好
- 🛡️ 强化数据校验，自动过滤无效脏数据
- 🖥️ 全平台兼容性优化，降低闪退概率

---

## 💬 开发者碎碎念
> 不堆花里胡哨的无效功能，只做真正好用的课堂工具。
> 无会员、无广告、永久免费开源。
> 希望用算法代替主观偏心，少一点老师的纠结，多一点学生的听课压力（不是）。

欢迎 Star ⭐ 鼓励，有想法欢迎提 Issue / PR 一起折腾。

---

## 📄 开源许可
本项目仅供教育学习、个人教学使用。
**禁止直接打包倒卖、二次封装用于商业盈利。**

## 👨‍💻 Author
**a13zhy**

---

> 复制全部直接粘贴到你的仓库 `README.md`，完全符合 GitHub Markdown 渲染规范，徽章、代码块、链接全部可用。
如果你需要，我可以再给你一段简短的**项目简介（仓库About描述）**，填到GitHub仓库主页。
