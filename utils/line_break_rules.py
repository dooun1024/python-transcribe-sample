import re
import unittest


def get_visual_width(text):
    """
    【仕様 3.2】文字幅の計算
    全角（漢字・ひらがな・カタカナ・全角記号）: 2
    半角（英数字・半角記号・半角スペース）: 1
    """
    width = 0
    for char in text:
        if ord(char) <= 0x7F:
            width += 1
        else:
            width += 2
    return width

import re

def get_visual_width(text):
    """【仕様 3.2】文字幅の計算（全角:2, 半角:1）"""
    return sum(2 if ord(char) > 0x7F else 1 for char in text)

def reformat_vtt_text(text, max_width=60):
    """
    VTT字幕の改行ロジック
    """
    text = text.replace('\n', '').replace('\r', '').strip()
    
    # 【仕様 5】改行位置ルール
    punctuation_rules = {
        '。': 'after', '、': 'after', '，': 'after', '．': 'after',
        '!': 'after', '！': 'after', '?': 'after', '？': 'after',
        ')': 'after', '）': 'after', '」': 'after',
        '(': 'before', '（': 'before', '「': 'before'
    }

    lines = []
    while text:
        # トークン化
        tokens = re.findall(r'[A-Za-z0-9\-]+|[^\x00-\x7f]|\s', text)
        
        current_line_tokens = []
        current_line_width = 0
        split_index = -1
        
        for i, token in enumerate(tokens):
            token_width = get_visual_width(token)
            
            # --- 61, 62文字目の特殊ルール判定 ---
            # 次のトークンが「後ろ改行」の記号で、含めると61 or 62幅になる場合
            if current_line_width == 60 and token in punctuation_rules:
                if punctuation_rules[token] == 'after' and token_width <= 2:
                    # この記号を現在の行に含めて、その直後で分割する
                    current_line_tokens.append(token)
                    split_index = len("".join(current_line_tokens))
                    break

            # 通常の幅制限(60)超過判定
            if current_line_width + token_width > max_width:
                # トークン単体で60超（超長英数）の場合
                if current_line_width == 0 and token_width > max_width:
                    temp_text = ""
                    temp_w = 0
                    for char in token:
                        char_w = get_visual_width(char)
                        if temp_w + char_w > max_width: break
                        temp_text += char
                        temp_w += char_w
                    split_index = len(temp_text)
                    break

                # 【仕様 4】49～60幅の範囲内での記号探索
                found_punct = False
                accumulated_text = "".join(current_line_tokens)
                
                for j in range(len(accumulated_text) - 1, -1, -1):
                    char = accumulated_text[j]
                    # 現在の文字までの累積幅を計算
                    width_at_j = get_visual_width(accumulated_text[:j+1])
                    
                    if 49 <= width_at_j <= 60:
                        if char in punctuation_rules:
                            pos = punctuation_rules[char]
                            split_index = j + 1 if pos == 'after' else j
                            found_punct = True
                            break
                
                # 記号がない場合は、現在のトークンの手前で改行（英数ブロック保護）
                if not found_punct:
                    split_index = len(accumulated_text)
                break
            
            current_line_tokens.append(token)
            current_line_width += token_width
            
        if split_index == -1:
            lines.append(text.strip())
            break
        else:
            lines.append(text[:split_index].strip())
            text = text[split_index:].lstrip()

    return "\n".join(lines)

class TestVttReformat(unittest.TestCase):

    def test_basic_zenkaku(self):
        """全角文字のみ：49-60幅の句読点で改行されること"""
        input_text = "これはテスト用の長い文章です。適切な場所で改行が行われるかを確認するためのものです。"
        # "これはテスト用の長い文章です。" (30幅) + "適切な場所で..."
        output = reformat_vtt_text(input_text)
        self.assertIn("これはテスト用の長い文章です。適切な場所で改行が行われるかを\n", output)

    def test_after_punctuation(self):
        """記号の後ろで改行（。や、など）"""
        input_text = "現在の進捗状況を報告します。修正が完了しましたので、確認をお願いいたします。"
        output = reformat_vtt_text(input_text)
        print("++++++++++++++++++",output)
        # 「報告します。」の後ろで改行されるべき
        self.assertTrue(output.startswith("現在の進捗状況を報告します。修正が完了しましたので、\n"))

    def test_before_punctuation(self):
        """記号の前で改行（「 や （ など）"""
        # ちょうど50幅付近に「が来るように調整
        input_text = "今後のスケジュールについては、以下の通りですと。「プロジェクト完了は来月末」を予定しています。"
        output = reformat_vtt_text(input_text)
        # 「 の前で改行されるべき
        self.assertIn("\n「プロジェクト完了", output)

    def test_english_word_protection(self):
        """英単語の途中で分割されないこと（Super-fastの維持）"""
        input_text = "このシステムは非常に動作が軽快で、Super-fastな処理速度を実現しているのが特徴です。"
        output = reformat_vtt_text(input_text)
        # Super-fast が 1つの単語として扱われ、途中で改行されないこと
        self.assertNotIn("Super-\nfast", output)

    def test_long_alphanumeric_force_split(self):
        """60幅を超える連続した英数字の強制改行"""
        input_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ12345678901234567890"
        output = reformat_vtt_text(input_text)
        lines = output.split('\n')
        self.assertEqual(len(lines[0]), 60) # 60文字目で切れること

    def test_61_62_special_rule(self):
        """61,62文字目に句読点がある場合の許容ルール"""
        # 30文字(60幅)の直後に「。」があるケース
        input_text = "あ" * 30 + "。" + "次の文章がここから始まります。"
        output = reformat_vtt_text(input_text)
        # 「。」が次の行に送られず、1行目の末尾に残ること
        self.assertTrue(output.startswith("あ" * 30 + "。\n"))

    def test_multi_line_pre_process(self):
        """前処理：LLMが生成した複数行を1行にまとめること"""
        input_text = "一行目です。\n二行目です。\n三行目です。"
        output = reformat_vtt_text(input_text)
        self.assertNotIn("\n二行目", output.replace("\n", " ", 1)) # 内部で一度結合されているか

    def test_mixed_language(self):
        """混在する言語（日本語と英語）の処理確認"""
        input_text = "これはテストです。Please ensure that the Super-fast processing works correctly! ありがとうございます。"
        output = reformat_vtt_text(input_text)
        self.assertIn("\nprocessing works correctly! ありがとうございます。", output)

    def test_mixed_language(self):
        """混在する言語（日本語と英語）の処理確認"""
        input_text = "これはテストです。Please ensure that the Super-fast processing works correctly! ありがとうございます。"
        output = reformat_vtt_text(input_text)
        self.assertIn("\nprocessing works correctly! ありがとうございます。", output)

# 単体テスト用の関数:
def get_visual_width(text):
    """
    文字の表示幅（占有幅）を計算する関数
    - 全角 (漢字、ひらがな、カタカナ、全角記号): 2
    - 半角 (英数字、半角記号、半角スペース): 1
    """
    width = 0
    for char in text:
        # Unicode範囲で判定: 0x00-0x7F が標準的な半角（ASCII）
        if ord(char) <= 0x7F:
            width += 1
        else:
            # それ以外（日本語など）は全角としてカウント
            width += 2
    return width


# --- 動作確認用サンプル ---
if __name__ == "__main__":
    unittest.main(verbosity=2)

    input="一二三四伍六七八九十一二三四伍六七八九十一二三四123456789012."
    print(reformat_vtt_text(input))

    input="一二三四伍六七八九十一二三四伍六七八九十一二三四 a b c d e f g h i 456789012."
    print(reformat_vtt_text(input))

    input="hellohello 123456789012345678901234567890123456789012345678901"
    print(reformat_vtt_text(input))
