#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AstrBot 单词卡片插件功能测试脚本
测试所有核心功能是否正常工作
"""

import sys
import os
import json
from pathlib import Path

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
plugin_dir = Path(__file__).parent
sys.path.insert(0, str(plugin_dir))

def test_file_structure():
    """测试文件结构"""
    print("=" * 60)
    print("测试 1: 文件结构")
    print("=" * 60)

    required_files = [
        "main.py",
        "metadata.yaml",
        "_conf_schema.json",
        "requirements.txt",
        "core/__init__.py",
        "core/base_handler.py",
        "core/language_manager.py",
        "core/card_renderer.py",
        "core/image_renderer.py",
        "languages/english/handler.py",
        "languages/japanese/handler.py",
        "languages/idiom/handler.py",
        "languages/classical/handler.py",
        "languages/radio/handler.py",
        "templates/card.html",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = plugin_dir / file_path
        if full_path.exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[FAIL] {file_path} - 文件不存在")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n缺少 {len(missing_files)} 个文件")
        return False
    else:
        print(f"\n所有 {len(required_files)} 个必需文件都存在")
        return True

def test_word_data():
    """测试词汇数据文件"""
    print("\n" + "=" * 60)
    print("测试 2: 词汇数据文件")
    print("=" * 60)

    word_files = {
        "english": "languages/english/words.json",
        "japanese": "languages/japanese/words.json",
        "idiom": "languages/idiom/words.json",
        "classical": "languages/classical/words.json",
        "radio": "languages/radio/words.json",
    }

    all_ok = True
    for lang_id, file_path in word_files.items():
        full_path = plugin_dir / file_path
        if not full_path.exists():
            print(f"[FAIL] {lang_id}: 文件不存在")
            all_ok = False
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                print(f"[OK] {lang_id}: {len(data)} 个词条")
            else:
                print(f"[FAIL] {lang_id}: 数据格式错误（应该是数组）")
                all_ok = False
        except Exception as e:
            print(f"[FAIL] {lang_id}: 加载失败 - {e}")
            all_ok = False

    return all_ok

def test_config_schema():
    """测试配置文件"""
    print("\n" + "=" * 60)
    print("测试 3: 配置文件")
    print("=" * 60)

    try:
        config_file = plugin_dir / "_conf_schema.json"
        if not config_file.exists():
            print("[FAIL] 配置文件不存在")
            return False

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        required_keys = [
            "current_language",
            "japanese_level",
            "target_groups",
            "push_time_generate",
            "push_time_send",
            "use_cdn_background",
            "learning_mode",
            "reset_on_complete"
        ]

        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            print(f"[FAIL] 缺少配置项: {missing_keys}")
            return False

        print(f"[OK] 配置文件完整，包含 {len(config)} 个配置项")
        for key in required_keys:
            default_val = config[key].get('default', 'N/A')
            print(f"  - {key}: {default_val}")

        return True
    except Exception as e:
        print(f"[FAIL] 配置文件测试失败: {e}")
        return False

def test_templates():
    """测试模板文件"""
    print("\n" + "=" * 60)
    print("测试 4: 模板文件")
    print("=" * 60)

    templates_dir = plugin_dir / "templates"
    required_templates = [
        "card.html",
        "card_japanese.html",
        "card_idiom.html",
        "card_classical.html",
        "card_radio.html"
    ]

    all_ok = True
    for template_name in required_templates:
        template_path = templates_dir / template_name
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"[OK] {template_name}: {size} 字节")
        else:
            print(f"[FAIL] {template_name}: 文件不存在")
            all_ok = False

    return all_ok

def test_metadata():
    """测试元数据文件"""
    print("\n" + "=" * 60)
    print("测试 5: 元数据文件")
    print("=" * 60)

    try:
        import yaml
        metadata_file = plugin_dir / "metadata.yaml"

        if not metadata_file.exists():
            print("[FAIL] metadata.yaml 不存在")
            return False

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f)

        required_fields = ["name", "desc", "version", "author", "repo"]
        missing_fields = [field for field in required_fields if field not in metadata]

        if missing_fields:
            print(f"[FAIL] 缺少字段: {missing_fields}")
            return False

        print("[OK] 元数据文件完整")
        print(f"  - 名称: {metadata['name']}")
        print(f"  - 版本: {metadata['version']}")
        print(f"  - 作者: {metadata['author']}")
        print(f"  - 仓库: {metadata['repo']}")

        return True
    except ImportError:
        print("[SKIP] PyYAML 未安装，跳过元数据测试")
        return True
    except Exception as e:
        print(f"[FAIL] 元数据测试失败: {e}")
        return False

def test_main_py_syntax():
    """测试 main.py 语法"""
    print("\n" + "=" * 60)
    print("测试 6: main.py 语法检查")
    print("=" * 60)

    try:
        import py_compile
        main_file = plugin_dir / "main.py"

        py_compile.compile(str(main_file), doraise=True)
        print("[OK] main.py 语法正确")
        return True
    except Exception as e:
        print(f"[FAIL] main.py 语法错误: {e}")
        return False

def test_cdn_backgrounds():
    """测试 CDN 背景图列表"""
    print("\n" + "=" * 60)
    print("测试 7: CDN 背景图配置")
    print("=" * 60)

    try:
        main_file = plugin_dir / "main.py"
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "CDN_BACKGROUNDS" in content:
            # 简单统计 CDN 链接数量
            cdn_count = content.count("tuchuang12.oss-cn-hangzhou.aliyuncs.com")
            print(f"[OK] 找到 {cdn_count} 个 CDN 背景图链接")
            return True
        else:
            print("[FAIL] 未找到 CDN_BACKGROUNDS 配置")
            return False
    except Exception as e:
        print(f"[FAIL] CDN 配置检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AstrBot 单词卡片插件 - 功能测试")
    print("=" * 60)

    tests = [
        ("文件结构", test_file_structure),
        ("词汇数据", test_word_data),
        ("配置文件", test_config_schema),
        ("模板文件", test_templates),
        ("元数据", test_metadata),
        ("语法检查", test_main_py_syntax),
        ("CDN配置", test_cdn_backgrounds),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 '{test_name}' 发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    if passed == total:
        print("状态: 所有测试通过!")
    else:
        print(f"状态: {total - passed} 个测试失败")
    print("=" * 60)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
