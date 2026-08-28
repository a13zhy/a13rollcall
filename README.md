

# a13rollcall
> 🎲 A13Rollcall｜第六代A13引擎 Tkinter课堂点名抽背神器

[![GitHub stars](https://img.shields.io/github/stars/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/fork)
[![Python Version](https://img.shields.io/badge/python‑3.8+-3776AB?style=flat-square)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/a13zhy/a13rollcall?style=flat-square)](https://github.com/a13zhy/a13rollcall/releases)
[![License](https://img.shields.io/badge/license‑NonCommercial‑blue?style=flat-square)](#📄-开源许可)

🔥 **本地离线GUI点名工具｜零广告｜零氪金｜无捆绑｜纯本地运行**

> ⚠️ 本项目是 **Tkinter图形桌面程序**，运行弹出可视化窗口，**不是黑乎乎的控制台命令行工具！**

老师点名纠结半天选谁？
学生上课开启摸鱼模式，内心疯狂祈祷「千万别点我」🙏。

交给自研**第六代A13抽签引擎**，把命运交给算法，拒绝主观偏心。
随机点名、课堂抽背、悬浮快捷小浮窗、全套快捷键，课堂整活神器就位✨。

---

## 💥 课堂两大史诗级痛点，谁懂啊家人们
- 👨‍🏫 **老师侧｜点名精神内耗**
每次提问疯狂纠结，点A怕偏心，点B刚点过，选择困难直接犯，点名十分钟，讲课五分钟。
- 👩‍🎓 **学生侧｜摸鱼侥幸玄学**
低头走神，表面听课实则神游天外，坚信自己就是那个永远不会被抽到的幸运儿。

`a13rollcall` 登场！
> 抛开主观印象，算法说了算，人人都有“中奖”概率，击碎摸鱼幻想，拯救老师选择困难症。

---

## ✨ 项目核心特性
### 🎲 第六代 A13 自研抽签引擎
拒绝地摊伪随机算法！
- ✅ 会话内防重复逻辑，减少“天选倒霉蛋”连续上榜
- ✅ 兼顾点名、抽背题库双重随机抽取
- ✅ 会话状态记忆，概率分配更均衡，拒绝长期透明人

### 🖥️ Tkinter 原生图形界面
不用浏览器，打开直接窗口交互：
- 🖼️ 主点名窗口，抽签效果可视化
- 🪟 **悬浮快捷抽取浮窗**，上课缩成小窗口，不遮挡课件PPT，随用随点
- ⌨️ **全套快捷键绑定**，手不用碰鼠标，键盘直接完成抽签、重置、切换模式

### 🧙‍♂️ 傻瓜式新手配置向导
不会改配置文件？不用慌！
向导一步一步带你设置参数，小白也能零门槛上手。

### 📂 数据持久化，搬家超方便
- `students.txt` / `texts.txt` 存放名单和抽背题库
- INI配置文件保存全部设置，关掉程序参数不丢失
- 纯文本格式，复制粘贴就能备份、切换不同班级，迁移零成本

### ⚡ 极致轻量化
纯Python标准库开发，**零第三方pip依赖**。
支持打包exe，没装Python的电脑双击直接跑。

> ⚠️避坑提醒：txt文件务必保存为**UTF‑8编码**，防止中文乱码；不要乱留空行，不然会抽中“空气同学”😂

---

## 🚀 快速上手
### 环境依赖
- Python `3.8` 及以上
- Windows官方Python安装包自带Tkinter，无需额外安装组件

**命令行启动**
```bash
# 直接启动主图形界面
python main.py

# 第一次玩，优先跑向导配置
python wizard_launcher.py
```
> 执行后弹出图形窗口，**不是黑框里面敲字操作！**

**懒人双击启动**
直接双击项目文件夹内的 `main.py` 即可运行。

📦 不想装Python？
去 [Releases](https://github.com/a13zhy/a13rollcall/releases) 下载打包好的exe，双击即玩。

**准备你的班级数据**
1. 修改 `students.txt`，一行一个学生姓名。
2. 修改 `texts.txt`，填入抽背题目，不用抽背直接清空。

---

## ⚙️ 可玩的自定义配置
全部可以在向导界面调整，自动存入ini配置：
- 单次抽取多少人，单人拷问 / 批量拷打自由切换
- 会话去重开关：开启尽量雨露均沾，关闭允许反复“中奖”
- 悬浮浮窗开关、窗口大小位置记忆
- 名单、题库文件路径自定义

> ✨小科普：
> 开启去重：同一节课尽量不点重复同学，适合常规课堂。
> 关闭去重：适合快速扫荡抽查，看谁运气爆棚连续中招。

## 💡 老玩家私藏骚操作
1. **纯点名模式**：直接清空 `texts.txt`，程序自动关闭抽背功能，专心点名整活。
2. **极速扫荡模式**：关掉去重，快速轮询全班，主打一个刺激。
3. **编码保命**：txt保存为UTF‑8，不然中文直接乱码，体验感爆炸。
4. **拒绝空气人**：名单不要留空行，不然会随机抽到不存在的同学，属于程序整活bug。

---

## 📜 更新日志
### V6.0｜2026‑08‑27
- 🚀 重磅升级**第六代A13随机引擎**，概率分配更加科学合理
- 🔨 整体重构代码，架构清爽整洁，可读性、可维护性拉满
- 🧙‍♂️ 新增交互式配置向导，零基础小白友好
- 🛡️ 强化数据校验，自动过滤空行、无效脏数据
- 🪟 新增悬浮快捷浮窗，上课不挡PPT，体验大提升
- ⌨️ 全套全局快捷键加持，解放你的鼠标
- 🖥️ 全平台兼容性优化，降低闪退翻车概率

---

## 💬 开发者碎碎念
> 拒绝花里胡哨的鸡肋功能，只做真正能用的课堂工具。
> 无会员、无广告、永久免费开源。
> 用算法代替主观偏心，减少老师点名内耗，顺便给学生一点点听课压力（狗头）。

喜欢就点个 ⭐Star 支持一波！
有脑洞、bug欢迎提 Issue / PR，一起来折腾。

---

## 📄 开源许可
本项目仅供教育学习、个人教学场景使用。
**禁止直接打包倒卖、二次封装用于商业盈利。**

产品GITHUB仓库-https://github.com/a13zhy/a13rollcall

产品目录网址-https://dkfile.istester.com/zhysppa13/a13callname.html

## 👨‍💻 Author
**a13zhy**二创请标注原作者！！！！！谢谢各位大神
```
产品GITHUB仓库-https://github.com/a13zhy/a13rollcall
产品目录网址-https://dkfile.istester.com/zhysppa13/a13callname.html
```
