<<<<<<< HEAD
# AstrBot 每日单词卡片插件

<div align="center">

📚 每日英语单词卡片推送插件 - 玻璃拟态风格

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-orange.svg)](https://github.com/Soulter/AstrBot)

</div>

## ✨ 特性

- 🎨 **玻璃拟态设计**：精美的毛玻璃风格卡片，视觉效果出众
- 🖼️ **CDN 背景图库**：37 张精选背景图托管于阿里云 OSS，加载快速
- 📅 **定时推送**：每天自动生成并推送单词卡片到群聊
- 📖 **丰富词库**：包含 3722+ 个 CET-6 核心词汇
- 🎲 **随机学习**：支持随机或顺序学习模式
- 📊 **进度追踪**：自动记录学习进度，支持查看统计
- 🔧 **灵活配置**：可自定义推送时间、学习模式等
- 🎯 **多种命令**：支持手动获取、预览、测试等功能

## 📸 效果预览

每张卡片包含：
- 单词本体（大字号，serif 字体）
- 音标（等宽字体）
- 词性标签（高亮显示）
- 中文释义
- 英文例句（斜体，毛玻璃背景）
- 随机背景图（37 张 CDN 图库随机选择）
- 随机主题色（10 种配色）

卡片分辨率：**1296 × 1620 像素**（超高清 3x 清晰度）

## 📦 安装

### 1. 克隆插件

将本插件文件夹放入 AstrBot 的 `addons/plugins/` 目录：

```bash
cd addons/plugins/
git clone https://github.com/itismygo/astrbot_plugin_vocabcard.git
```

### 2. 安装依赖

```bash
cd astrbot_plugin_vocabcard
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 重启 AstrBot

重启 AstrBot 后插件将自动加载。

## 🎮 使用方法

### 基础命令

| 命令 | 说明 |
|------|------|
| `/vocab` | 立即获取一个单词卡片 |
| `/vocab_status` | 查看学习进度统计 |
| `/vocab_register` | 在当前会话注册每日推送 |
| `/vocab_unregister` | 取消当前会话的每日推送 |
| `/vocab_help` | 显示帮助信息 |

### 高级命令

| 命令 | 说明 |
|------|------|
| `/vocab_preview [单词]` | 预览指定单词的卡片效果（调试用） |
| `/vocab_test` | 测试推送功能（立即生成并发送） |
| `/vocab_now` | 立即执行完整推送流程到所有已注册群 |

### 使用流程

1. **注册推送**
   ```
   用户：/vocab_register
   机器人：注册成功！🎉 将在每天 08:00 推送单词卡片
   ```

2. **查看进度**
   ```
   用户：/vocab_status
   机器人：
   📊 单词学习进度
   ━━━━━━━━━━━━━━━━
   ✅ 已学习: 125 个
   📚 总词汇: 3722 个
   📈 完成度: 3%
   📅 最后推送: 2024-01-15
   ```

3. **手动获取**
   ```
   用户：/vocab
   机器人：[发送单词卡片图片]
   ```

## ⚙️ 配置说明

插件配置文件：`_conf_schema.json`

### 主要配置项

```json
{
  "target_groups": [],              // 推送目标群列表（自动管理）
  "push_time_generate": "07:30",    // 卡片生成时间
  "push_time_send": "08:00",        // 卡片推送时间
  "learning_mode": "random",        // 学习模式：random(随机) / sequential(顺序)
  "reset_on_complete": true,        // 学完所有单词后是否自动重置
  "use_cdn_background": true        // 是否使用 CDN 背景图（关闭则使用本地图片）
}
```

### 自定义推送时间

修改 `push_time_generate` 和 `push_time_send` 可调整生成和推送时间：

```json
{
  "push_time_generate": "06:00",  // 早上 6 点生成
  "push_time_send": "07:00"       // 早上 7 点推送
}
```

### 学习模式

- **random（随机）**：每次随机选择一个未学习的单词
- **sequential（顺序）**：按照词库顺序逐个学习

## 📂 目录结构

```
astrbot_plugin_vocabcard/
├── main.py                 # 插件主程序
├── metadata.yaml           # 插件元数据
├── _conf_schema.json       # 配置文件
├── requirements.txt        # Python 依赖
├── data/
│   ├── words.json         # 词汇数据（3722 个单词）
│   └── progress.json      # 学习进度记录
├── templates/
│   └── card.html          # 卡片 HTML 模板
├── photos/                # 本地备用背景图（5 张，CDN 不可用时使用）
│   └── *.jpg
└── scripts/
    ├── clean_data.py      # 数据清洗脚本
    └── download_backgrounds.py  # 背景图下载脚本
```

## 🎨 卡片设计

### 玻璃拟态实现

卡片采用五层叠加实现玻璃拟态效果：

1. **背景图层**：随机选择 + 随机裁剪位置
2. **主题色叠加**：10 种深色主题随机选择
3. **渐变遮罩**：增强文字可读性
4. **毛玻璃模糊**：backdrop-filter 实现
5. **边框光环**：半透明边框

### 随机性设计

每张卡片包含三重随机性：
- 📷 随机背景图（37 张 CDN 图库）
- 🎨 随机主题色（10 种配色）
- ✂️ 随机裁剪位置（0-100% X/Y）

### 字体选择

- **单词标题**：Georgia, Noto Serif SC（优雅衬线体）
- **音标**：Consolas, Source Code Pro（等宽字体）
- **中文文本**：Noto Sans SC, Microsoft YaHei（无衬线字体）

## 🔧 开发相关

### 数据格式

`data/words.json` 中每个单词的数据结构：

```json
{
  "word": "abandon",
  "phonetic": "/əˈbændən/",
  "pos": "v.",
  "definition_cn": "放弃；抛弃",
  "example": "He decided to abandon the project due to lack of funding."
}
```

### 添加自定义词库

1. 编辑 `data/words.json` 添加新单词
2. 或使用 `scripts/clean_data.py` 处理原始 txt 文件

原始数据格式：
```
单词&[音标]&词性+释义&例句
```

### 添加背景图

背景图托管于阿里云 OSS，如需添加更多背景图：

1. 将图片上传到 OSS 的 `photos/` 目录
2. 在 `main.py` 的 `CDN_BACKGROUNDS` 列表中添加对应 URL

本地 `photos/` 文件夹中的图片仅作为 CDN 不可用时的备用。

### 关闭 CDN 使用本地图片

如需关闭 CDN，在插件配置中设置：
```json
{
  "use_cdn_background": false
}
```

## 📝 技术栈

- **AstrBot**：插件框架
- **Playwright**：无头浏览器截图
- **HTML/CSS**：卡片设计
- **asyncio**：异步调度

## 🐛 常见问题

### Q: 卡片生成失败？

A: 确保已安装 Playwright 浏览器：
```bash
playwright install chromium
```

### Q: 推送不生效？

A: 检查：
1. 是否已使用 `/vocab_register` 注册
2. 配置的推送时间是否正确
3. 查看日志是否有错误信息

### Q: 如何清空学习进度？

A: 删除或清空 `data/progress.json` 中的 `sent_words` 数组。

### Q: 能否自定义卡片样式？

A: 可以编辑 `templates/card.html` 自定义 CSS 样式。

## 📄 许可证

AGPL-3.0 License

## 🙏 致谢

- 背景图片来源：[Unsplash](https://unsplash.com)
- 字体：Google Fonts (Noto Sans/Serif SC)
- 图床服务：阿里云 OSS

## 📮 反馈与建议

如有问题或建议，欢迎提交 Issue 或 Pull Request。
=======
# AstrBot 每日单词卡片插件

<div align="center">

📚 每日多语种单词卡片推送插件 - 玻璃拟态风格

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-orange.svg)](https://github.com/Soulter/AstrBot)

</div>

## 📸 效果预览

<div align="center">
<img src="example.png" width="300" alt="卡片效果"/>
</div>

> 玻璃拟态风格卡片，分辨率 **1728 × 2160 像素**（4K级别）

## 🎮 快速上手

| 命令 | 说明 |
|------|------|
| `/vocab` | 立即获取一张单词卡片 |
| `/vocab_lang [语种ID]` | 切换卡组（不带参数显示列表） |
| `/vocab_status` | 查看学习进度 |
| `/vocab_register` | 注册每日推送 |
| `/vocab_unregister` | 取消每日推送 |
| `/vocab_help` | 显示帮助 |

## 📚 支持的卡组

| 卡组 | 词条数 | 说明 |
|------|--------|------|
| english | 3,722 | 英语六级核心词汇 |
| japanese | 10,147 | 日语JLPT N1-N5（支持等级筛选） |
| idiom | 824 | 常用成语 |
| classical | 27 | 古文经典句子 |
| radio | 361 | 无线电法规题库 |

## 📦 安装

### 1. 克隆插件

```bash
cd addons/plugins/
git clone https://github.com/itismygo/astrbot_plugin_vocabcard.git
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> 首次生成卡片时会自动下载 Chromium 浏览器（约 150MB）

### 3. 重启 AstrBot

## ⚙️ 主要配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| current_language | 当前卡组 | english |
| japanese_level | 日语等级筛选 | all |
| push_time_generate | 卡片生成时间 | 07:30 |
| push_time_send | 推送时间 | 08:00 |
| learning_mode | 学习模式 | random |

## 🐛 常见问题

**Q: 首次使用较慢？**
> 首次运行会自动下载 Chromium 浏览器，请耐心等待

**Q: 推送不生效？**
> 1. 检查是否已使用 `/vocab_register` 注册
> 2. 检查推送时间配置

**Q: 清空学习进度？**
> 删除 `data/progress_<语种>.json` 文件

## 📄 许可证

AGPL-3.0 License
>>>>>>> e631f42 (初始提交: 单词卡片插件)
