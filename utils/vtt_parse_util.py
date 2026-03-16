import re
from dataclasses import dataclass
from typing import List


@dataclass
class Subtitle:
    """字幕对象"""
    index: int              # 数字编号
    start_time: str         # 开始时间戳 (如 "00:00:01.000")
    end_time: str           # 结束时间戳 (如 "00:00:06.000")
    content: str            # 字幕内容


def parse_vtt(vtt_content: str) -> List[Subtitle]:
    """
    解析 VTT 文件内容，返回字幕对象数组

    Args:
        vtt_content: VTT 文件的字符串内容

    Returns:
        字幕对象列表
    """
    subtitles = []

    # 移除 BOM 和首尾空白
    vtt_content = vtt_content.strip().lstrip('\ufeff')

    # 按空行分割成块
    blocks = re.split(r'\n\s*\n', vtt_content)

    # 时间戳正则表达式
    timestamp_pattern = re.compile(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
    )

    for block in blocks:
        block = block.strip()
        if not block or block == 'WEBVTT':
            continue

        lines = block.split('\n')
        if len(lines) < 2:
            continue

        index = None
        start_time = None
        end_time = None
        content_lines = []

        line_idx = 0

        # 尝试解析编号（可选）
        if lines[line_idx].strip().isdigit():
            index = int(lines[line_idx].strip())
            line_idx += 1

        # 解析时间戳
        if line_idx < len(lines):
            match = timestamp_pattern.search(lines[line_idx])
            if match:
                start_time = match.group(1)
                end_time = match.group(2)
                line_idx += 1

        # 如果没有时间戳，跳过此块
        if not start_time:
            continue

        # 剩余的行是字幕内容
        content_lines = lines[line_idx:]
        content = '\n'.join(content_lines)

        # 如果没有编号，使用当前数组长度+1
        if index is None:
            index = len(subtitles) + 1

        subtitles.append(Subtitle(
            index=index,
            start_time=start_time,
            end_time=end_time,
            content=content
        ))

    return subtitles


def restore_vtt(subtitles: List[Subtitle]) -> str:
    """
    将字幕对象数组还原为 VTT 文件字符串

    Args:
        subtitles: 字幕对象列表

    Returns:
        VTT 格式的字符串
    """
    lines = ['WEBVTT', '']

    for subtitle in subtitles:
        # 添加编号
        lines.append(str(subtitle.index))
        # 添加时间戳
        lines.append(f'{subtitle.start_time} --> {subtitle.end_time}')
        # 添加字幕内容
        lines.append(subtitle.content)
        # 添加空行分隔
        lines.append('')

    return '\n'.join(lines)


if __name__ == '__main__':
    # 测试代码
    test_vtt = """WEBVTT

1
00:00:01.000 --> 00:00:06.000
大家好，欢迎来到本期视频。

2
00:00:10.000 --> 00:00:18.000
这是第二条字幕。
"""
    
    subtitles = parse_vtt(test_vtt)

    # 遍历数组，在每条字幕的 content 末尾加上 "test"
    for subtitle in subtitles:
        subtitle.content = subtitle.content + " test"

    # 查看修改后的结果
    for sub in subtitles:
        print(f"{sub.index}: {sub.content}")

    # 还原成 VTT 格式
    result_vtt = restore_vtt(subtitles)
    print(result_vtt)
