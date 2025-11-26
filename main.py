# -*- coding: utf-8 -*-
"""
AstrBot 每日单词卡片插件
每日定时生成玻璃拟态风格的英语单词卡片并推送到群聊
"""

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import MessageChain
import astrbot.api.message_components as Comp

import asyncio
import datetime
import json
import os
import random
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List


# 主题色列表 - 用于随机选择
THEME_COLORS = [
    "#2F4F4F",  # 深石板灰
    "#4B0082",  # 靛蓝
    "#006400",  # 深绿
    "#8B0000",  # 深红
    "#2F2F4F",  # 深紫蓝
    "#4A4A6A",  # 灰紫
    "#1a1a2e",  # 深夜蓝
    "#16213e",  # 海军蓝
    "#0f3460",  # 深蓝
    "#533483",  # 紫罗兰
]


@register("vocabcard", "Assistant", "每日英语单词卡片推送插件 - 玻璃拟态风格", "1.0.0")
class VocabCardPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.plugin_dir = Path(__file__).parent
        self.data_dir = self.plugin_dir / "data"
        self.template_path = self.plugin_dir / "templates" / "card.html"
        self.backgrounds_dir = self.plugin_dir / "photos"  # 离线背景图目录

        # 加载词汇数据和进度
        self.words: List[Dict] = self._load_words()
        self.progress: Dict = self._load_progress()
        self.offline_backgrounds: List[Path] = self._load_offline_backgrounds()

        # 定时任务相关
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cached_image_path: Optional[str] = None
        self._current_word: Optional[Dict] = None
        self._today_generated: bool = False
        self._last_check_date: str = ""

        # Playwright 浏览器实例（延迟初始化）
        self._browser = None
        self._playwright = None

    def _load_offline_backgrounds(self) -> List[Path]:
        """加载离线背景图列表"""
        if not self.backgrounds_dir.exists():
            return []
        # 支持多种图片格式
        patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"]
        backgrounds = []
        for pattern in patterns:
            backgrounds.extend(self.backgrounds_dir.glob(pattern))
            backgrounds.extend(self.backgrounds_dir.glob(pattern.upper()))
        logger.info(f"已加载 {len(backgrounds)} 张离线背景图")
        return backgrounds

    def _get_background_url(self, word: Dict) -> str:
        """获取背景图 URL（优先 AI 生成，失败则用离线图）"""
        # 临时禁用 AI 生图，直接使用本地图片
        # 如需恢复 AI 生图，将下面这行改为 True
        use_ai = False  # self.config.get("enable_ai_background", True)

        if use_ai:
            # === AI 生图代码（已注释，保留以便后续恢复）===
            # 使用 Pollinations.ai 动态生成 - 提高分辨率
            bg_prompt = self._generate_bg_prompt(word)
            # 使用更高分辨率：1920x2400（原来是1080x1350）
            return f"https://image.pollinations.ai/prompt/{bg_prompt}?width=1920&height=2400&nologo=true&model=flux&enhance=true"
        else:
            # 使用离线背景图（当前启用）
            return self._get_offline_background_url()

    def _get_offline_background_url(self) -> str:
        """获取一张离线背景图的 file:// URL"""
        if not self.offline_backgrounds:
            # 没有离线图，返回纯色背景的 data URL
            return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1080' height='1350'%3E%3Crect fill='%231a1a2e' width='100%25' height='100%25'/%3E%3C/svg%3E"

        bg_path = random.choice(self.offline_backgrounds)
        # 返回 file:// URL
        return f"file:///{bg_path.as_posix()}"

    def _load_words(self) -> List[Dict]:
        """加载词汇数据"""
        words_file = self.data_dir / "words.json"
        if words_file.exists():
            try:
                with open(words_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载词汇数据失败: {e}")
        return []

    def _load_progress(self) -> Dict:
        """加载学习进度"""
        progress_file = self.data_dir / "progress.json"
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载进度数据失败: {e}")
        return {"sent_words": [], "last_push_date": ""}

    def _save_progress(self):
        """保存学习进度"""
        progress_file = self.data_dir / "progress.json"
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度数据失败: {e}")

    async def initialize(self):
        """异步初始化"""
        logger.info(f"单词卡片插件初始化完成，已加载 {len(self.words)} 个单词")

    @filter.on_astrbot_loaded()
    async def on_loaded(self):
        """AstrBot 启动后启动定时任务"""
        self._scheduler_task = asyncio.create_task(self._schedule_loop())
        logger.info("单词卡片定时任务已启动")

    async def _schedule_loop(self):
        """定时任务主循环 - 智能睡眠，精准触发"""
        while True:
            try:
                now = datetime.datetime.now()
                today_str = now.strftime("%Y-%m-%d")

                # 解析配置的时间
                gen_time = self._parse_time(self.config.get("push_time_generate", "07:30"))
                push_time = self._parse_time(self.config.get("push_time_send", "08:00"))

                # 每天0点重置标记
                if self._last_check_date != today_str:
                    self._today_generated = False
                    self._last_check_date = today_str

                # 计算下一个目标时间
                next_target = self._calculate_next_target_time(now, gen_time, push_time)

                if next_target:
                    sleep_seconds = (next_target - now).total_seconds()

                    # 如果距离目标时间超过 60 秒，先睡到提前 30 秒
                    if sleep_seconds > 60:
                        sleep_until = sleep_seconds - 30
                        logger.debug(f"距离下次任务还有 {sleep_seconds:.0f} 秒，先睡眠 {sleep_until:.0f} 秒")
                        await asyncio.sleep(sleep_until)
                        continue

                    # 距离目标时间很近了，精确等待
                    if sleep_seconds > 0:
                        logger.debug(f"即将执行任务，精确等待 {sleep_seconds:.1f} 秒")
                        await asyncio.sleep(sleep_seconds)

                # 重新获取当前时间（睡眠后）
                now = datetime.datetime.now()

                # 执行生成任务
                if now.hour == gen_time[0] and now.minute == gen_time[1]:
                    if not self._today_generated:
                        logger.info("开始生成每日单词卡片...")
                        await self._generate_daily_card()
                        self._today_generated = True

                # 执行推送任务
                if now.hour == push_time[0] and now.minute == push_time[1]:
                    if self._cached_image_path and os.path.exists(self._cached_image_path):
                        logger.info("开始推送每日单词卡片...")
                        await self._push_daily_card()

                # 执行完任务后等待 10 秒，避免重复触发
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"定时任务出错: {e}")
                await asyncio.sleep(60)  # 出错后等待 60 秒重试

    def _parse_time(self, time_str: str) -> tuple:
        """解析时间字符串 HH:MM"""
        try:
            parts = time_str.split(':')
            return (int(parts[0]), int(parts[1]))
        except:
            return (8, 0)  # 默认 8:00

    def _calculate_next_target_time(self, now: datetime.datetime, gen_time: tuple, push_time: tuple) -> Optional[datetime.datetime]:
        """计算下一个目标时间点（生成时间或推送时间中最近的一个）"""
        today = now.date()

        # 构建今天的生成时间和推送时间
        gen_datetime = datetime.datetime.combine(today, datetime.time(gen_time[0], gen_time[1]))
        push_datetime = datetime.datetime.combine(today, datetime.time(push_time[0], push_time[1]))

        # 找出所有未来的目标时间
        targets = []

        # 如果还没生成过，且生成时间未到
        if not self._today_generated and gen_datetime > now:
            targets.append(gen_datetime)

        # 如果推送时间未到
        if push_datetime > now:
            targets.append(push_datetime)

        # 如果今天的任务都完成了，计算明天的第一个任务（生成时间）
        if not targets:
            tomorrow = today + datetime.timedelta(days=1)
            next_gen = datetime.datetime.combine(tomorrow, datetime.time(gen_time[0], gen_time[1]))
            targets.append(next_gen)

        # 返回最近的目标时间
        return min(targets) if targets else None

    def _select_word(self) -> Optional[Dict]:
        """选择一个未推送过的单词"""
        if not self.words:
            return None

        sent_words = set(self.progress.get("sent_words", []))
        available = [w for w in self.words if w["word"] not in sent_words]

        # 如果全部推送完毕
        if not available:
            if self.config.get("reset_on_complete", True):
                # 重置进度
                self.progress["sent_words"] = []
                self._save_progress()
                available = self.words
                logger.info("所有单词已推送完毕，已重置进度")
            else:
                logger.warning("所有单词已推送完毕，且未开启自动重置")
                return self.words[0] if self.words else None

        # 选择模式
        mode = self.config.get("learning_mode", "random")
        if mode == "sequential":
            return available[0]
        return random.choice(available)

    def _mark_word_sent(self, word: str):
        """标记单词已推送"""
        if word not in self.progress["sent_words"]:
            self.progress["sent_words"].append(word)
        self.progress["last_push_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        self._save_progress()

    def _generate_bg_prompt(self, word: Dict) -> str:
        """根据单词生成背景图提示词"""
        word_text = word["word"]
        meaning = word.get("definition_cn", "")
        pos = word.get("pos", "").lower()

        # 基于词性选择主题风格
        if "adj" in pos:
            theme = "abstract gradient aesthetic atmosphere"
        elif "n." in pos:
            theme = "realistic minimalist photography"
        elif "v." in pos:
            theme = "dynamic motion artistic blur"
        else:
            theme = "aesthetic minimalist background"

        # 构建提示词
        prompt = f"{word_text} concept, {theme}, high quality, 4k, no text, cinematic lighting"
        return urllib.parse.quote(prompt)

    def _render_template(self, word: Dict) -> str:
        """渲染 HTML 模板"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 获取背景图 URL
        bg_url = self._get_background_url(word)

        # 选择主题色
        theme_color = random.choice(THEME_COLORS)

        # 随机背景图位置（增加随机性）
        # 生成类似 "30% 70%" 的随机位置
        bg_x = random.randint(0, 100)
        bg_y = random.randint(0, 100)
        bg_position = f"{bg_x}% {bg_y}%"

        # 简单模板替换
        html = template.replace("{{word}}", word.get("word", ""))
        html = html.replace("{{phonetic}}", word.get("phonetic", ""))
        html = html.replace("{{pos}}", word.get("pos", "").upper() or "WORD")
        html = html.replace("{{definition_cn}}", word.get("definition_cn", ""))
        html = html.replace("{{example}}", word.get("example", ""))
        html = html.replace("{{bg_url}}", bg_url)
        html = html.replace("{{theme_color}}", theme_color)
        html = html.replace("{{bg_position}}", bg_position)

        return html

    async def _generate_card_image(self, word: Dict) -> str:
        """使用 Playwright 生成单词卡片图片"""
        from playwright.async_api import async_playwright

        # 渲染 HTML
        html_content = self._render_template(word)

        # 临时文件路径
        temp_html = self.plugin_dir / "temp_card.html"
        temp_png = self.plugin_dir / f"card_{word['word']}.png"

        # 保存 HTML
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)

        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=True)

                # 创建超高清页面 - device_scale_factor=3 实现 3x 清晰度
                # 输出分辨率：1296x1620 (432x3, 540x3)
                page = await browser.new_page(
                    viewport={'width': 432, 'height': 540},
                    device_scale_factor=3  # 3倍清晰度，比2倍更清晰
                )

                # 加载页面
                await page.goto(f'file:///{temp_html.as_posix()}')

                # 等待背景图加载完成
                # 方法1: 等待网络空闲（所有请求完成）
                try:
                    await page.wait_for_load_state('networkidle', timeout=20000)  # 增加到20秒
                except:
                    pass  # 超时也继续

                # 方法2: 额外等待确保图片渲染
                await page.wait_for_timeout(3000)  # 增加到3秒

                # 检查背景图是否加载成功
                bg_loaded = await page.evaluate('''() => {
                    const bgLayer = document.querySelector('.bg-layer');
                    if (!bgLayer) return false;
                    const style = window.getComputedStyle(bgLayer);
                    const bgImage = style.backgroundImage;
                    if (!bgImage || bgImage === 'none') return false;

                    // 创建一个图片对象来检测加载
                    return new Promise((resolve) => {
                        const url = bgImage.replace(/^url\\(['"']?/, '').replace(/['"']?\\)$/, '');
                        const img = new Image();
                        img.onload = () => resolve(true);
                        img.onerror = () => resolve(false);
                        img.src = url;
                        // 8秒超时（高分辨率图片需要更长时间）
                        setTimeout(() => resolve(false), 8000);
                    });
                }''')

                if not bg_loaded:
                    logger.warning("背景图加载可能未完成，继续截图...")
                    # 再等待一会儿
                    await page.wait_for_timeout(5000)

                # 超高清截图
                await page.screenshot(
                    path=str(temp_png),
                    type='png',
                    scale='device'  # 使用设备缩放
                    # quality 参数仅适用于 jpeg，PNG 已经是无损格式
                )

                await browser.close()

            logger.info(f"卡片图片已生成: {temp_png}")
            return str(temp_png)

        except Exception as e:
            logger.error(f"生成卡片图片失败: {e}")
            raise
        finally:
            # 清理临时 HTML
            if temp_html.exists():
                temp_html.unlink()

    async def _generate_daily_card(self):
        """生成每日单词卡片"""
        word = self._select_word()
        if not word:
            logger.warning("没有可用的单词")
            return

        try:
            image_path = await self._generate_card_image(word)
            self._cached_image_path = image_path
            self._current_word = word
            self._mark_word_sent(word["word"])
            logger.info(f"已生成每日单词卡片: {word['word']}")
        except Exception as e:
            logger.error(f"生成每日卡片失败: {e}")

    async def _push_daily_card(self):
        """推送卡片到已注册的群聊"""
        if not self._cached_image_path or not os.path.exists(self._cached_image_path):
            logger.warning("没有已生成的卡片可推送")
            return

        target_groups = self.config.get("target_groups", [])
        if not target_groups:
            logger.warning("没有已注册的推送目标")
            return

        success_count = 0
        word_text = self._current_word.get("word", "单词") if self._current_word else "单词"

        for umo in target_groups:
            try:
                # 构建消息链
                chain = MessageChain()
                chain.message(f"📚 每日单词: {word_text}")
                chain.file_image(self._cached_image_path)

                await self.context.send_message(umo, chain)
                success_count += 1
                logger.info(f"已推送到: {umo}")
            except Exception as e:
                logger.error(f"推送到 {umo} 失败: {e}")

        logger.info(f"每日单词推送完成: {success_count}/{len(target_groups)}")

        # 清理缓存的图片
        try:
            if os.path.exists(self._cached_image_path):
                os.remove(self._cached_image_path)
        except:
            pass
        self._cached_image_path = None

    # ========== 用户命令 ==========

    @filter.command("vocab")
    async def cmd_vocab(self, event: AstrMessageEvent):
        """手动获取一个单词卡片"""
        word = self._select_word()
        if not word:
            yield event.plain_result("没有可用的单词数据")
            return

        # 静默生成，不发送提示
        try:
            image_path = await self._generate_card_image(word)
            yield event.image_result(image_path)

            # 清理图片
            try:
                os.remove(image_path)
            except:
                pass
        except Exception as e:
            logger.error(f"生成卡片失败: {e}")
            yield event.plain_result(f"❌ 生成卡片失败: {e}")

    @filter.command("vocab_status")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看学习进度"""
        total = len(self.words)
        sent = len(self.progress.get("sent_words", []))
        percent = sent * 100 // total if total > 0 else 0
        last_date = self.progress.get("last_push_date", "未知")

        msg = f"""📊 单词学习进度
━━━━━━━━━━━━━━━━
✅ 已学习: {sent} 个
📚 总词汇: {total} 个
📈 完成度: {percent}%
📅 最后推送: {last_date}
━━━━━━━━━━━━━━━━"""
        yield event.plain_result(msg)

    @filter.command("vocab_register")
    async def cmd_register(self, event: AstrMessageEvent):
        """在当前会话注册接收每日单词推送"""
        umo = event.unified_msg_origin
        target_groups = self.config.get("target_groups", [])

        if umo in target_groups:
            yield event.plain_result("当前会话已注册过了 ✅")
            return

        target_groups.append(umo)
        self.config["target_groups"] = target_groups
        self.config.save_config()

        push_time = self.config.get("push_time_send", "08:00")
        yield event.plain_result(f"注册成功！🎉\n将在每天 {push_time} 推送单词卡片")

    @filter.command("vocab_unregister")
    async def cmd_unregister(self, event: AstrMessageEvent):
        """取消当前会话的每日单词推送"""
        umo = event.unified_msg_origin
        target_groups = self.config.get("target_groups", [])

        if umo not in target_groups:
            yield event.plain_result("当前会话未注册 ❌")
            return

        target_groups.remove(umo)
        self.config["target_groups"] = target_groups
        self.config.save_config()

        yield event.plain_result("已取消注册 👋")

    @filter.command("vocab_test")
    async def cmd_test_push(self, event: AstrMessageEvent):
        """测试推送功能（立即生成并推送一张卡片）"""
        try:
            # 生成卡片（静默）
            word = self._select_word()
            if not word:
                yield event.plain_result("没有可用的单词")
                return

            image_path = await self._generate_card_image(word)

            # 发送到当前会话
            yield event.plain_result(f"📚 测试单词: {word['word']}")
            yield event.image_result(image_path)

            # 清理
            try:
                os.remove(image_path)
            except:
                pass

        except Exception as e:
            logger.error(f"测试推送失败: {e}")
            yield event.plain_result(f"❌ 测试失败: {e}")

    @filter.command("vocab_preview")
    async def cmd_preview(self, event: AstrMessageEvent, word_input: str = ""):
        """
        预览单词卡片效果（调试用）
        用法: /vocab_preview [单词]
        不带参数则随机选一个单词
        """
        # 查找单词
        if word_input:
            # 搜索指定单词
            word = None
            for w in self.words:
                if w["word"].lower() == word_input.lower():
                    word = w
                    break
            if not word:
                yield event.plain_result(f"未找到单词: {word_input}")
                return
        else:
            word = self._select_word()
            if not word:
                yield event.plain_result("没有可用的单词数据")
                return

        # 显示单词详情
        info_msg = f"""🔍 单词预览
━━━━━━━━━━━━━━━━━━━━
📝 单词: {word.get('word', '')}
🔊 音标: {word.get('phonetic', '')}
📚 词性: {word.get('pos', '')}
📖 释义: {word.get('definition_cn', '')}
💬 例句: {word.get('example', '')[:50]}...
━━━━━━━━━━━━━━━━━━━━
⏳ 正在生成卡片图片..."""
        yield event.plain_result(info_msg)

        try:
            # 生成图片
            image_path = await self._generate_card_image(word)
            yield event.plain_result("✅ 图片生成成功！")
            yield event.image_result(image_path)

            # 清理
            try:
                os.remove(image_path)
            except:
                pass

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"预览失败: {error_detail}")
            yield event.plain_result(f"❌ 生成失败: {e}\n\n详细错误:\n{error_detail[:500]}")

    @filter.command("vocab_now")
    async def cmd_push_now(self, event: AstrMessageEvent):
        """立即执行一次完整的生成+推送流程（模拟定时任务）"""
        yield event.plain_result("🚀 开始执行完整推送流程...")

        # 检查是否有注册的群
        target_groups = self.config.get("target_groups", [])
        if not target_groups:
            yield event.plain_result("⚠️ 没有已注册的推送目标，请先使用 /vocab_register 注册")
            return

        yield event.plain_result(f"📋 已注册 {len(target_groups)} 个推送目标")

        try:
            # 1. 生成卡片
            yield event.plain_result("⏳ 步骤1: 生成单词卡片...")
            await self._generate_daily_card()

            if not self._cached_image_path:
                yield event.plain_result("❌ 卡片生成失败")
                return

            yield event.plain_result(f"✅ 卡片已生成: {self._current_word.get('word', '?')}")

            # 2. 推送
            yield event.plain_result("⏳ 步骤2: 推送到所有已注册群聊...")
            await self._push_daily_card()

            yield event.plain_result("✅ 推送完成！")

        except Exception as e:
            import traceback
            logger.error(f"立即推送失败: {traceback.format_exc()}")
            yield event.plain_result(f"❌ 推送失败: {e}")

    @filter.command("vocab_help")
    async def cmd_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_msg = """📚 每日单词卡片插件帮助
━━━━━━━━━━━━━━━━━━━━
/vocab - 立即获取一个单词卡片
/vocab_preview [单词] - 预览卡片效果
/vocab_now - 立即执行推送流程
/vocab_status - 查看学习进度
/vocab_register - 注册每日推送
/vocab_unregister - 取消每日推送
/vocab_test - 测试推送功能
/vocab_help - 显示此帮助
━━━━━━━━━━━━━━━━━━━━
💡 注册后每天 8:00 自动推送"""
        yield event.plain_result(help_msg)

    async def terminate(self):
        """插件卸载时取消定时任务"""
        if self._scheduler_task:
            self._scheduler_task.cancel()
        logger.info("单词卡片插件已卸载")
