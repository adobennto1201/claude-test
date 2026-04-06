#!/usr/bin/env python3
"""毎日のAIニュースを10件取得してまとめるアプリ"""

import anthropic
from datetime import date


SYSTEM_PROMPT = """あなたはAIニュースの専門家です。
最新のAIに関するニュースを検索し、以下の形式で日本語でまとめてください：

1. 各ニュースを番号付きリスト（1〜10件）で提示する
2. 各ニュースに：
   - タイトル（太字）
   - 概要（2〜3文）
   - 重要度（⭐️〜⭐️⭐️⭐️）
3. 最後に本日のAIトレンド全体の総括（3〜5文）を追加する

情報は正確で信頼性の高いソースから取得してください。"""


def fetch_and_summarize_ai_news() -> None:
    client = anthropic.Anthropic()
    today = date.today().strftime("%Y年%m月%d日")

    print(f"{'='*60}")
    print(f"  📰 AIニュースサマリー - {today}")
    print(f"{'='*60}\n")
    print("AIニュースを取得中...\n")

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[
            {"type": "web_search_20260209", "name": "web_search"},
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"本日（{today}）の最新AIニュースを10件検索して、"
                    "日本語でわかりやすくまとめてください。"
                    "大規模言語モデル、AI研究、AI企業動向、AI規制、"
                    "AI製品リリースなど幅広いトピックをカバーしてください。"
                ),
            }
        ],
    ) as stream:
        for event in stream:
            if event.type == "content_block_start":
                if hasattr(event.content_block, "type"):
                    if event.content_block.type == "text":
                        pass  # テキストブロック開始
                    elif event.content_block.type == "server_tool_use":
                        tool_name = getattr(event.content_block, "name", "")
                        if tool_name == "web_search":
                            print("🔍 ウェブ検索中...\n")

            elif event.type == "content_block_delta":
                if hasattr(event.delta, "type"):
                    if event.delta.type == "text_delta":
                        print(event.delta.text, end="", flush=True)

        final = stream.get_final_message()

    print(f"\n\n{'='*60}")
    print(f"  ✅ 取得完了")
    print(f"  入力トークン: {final.usage.input_tokens:,}")
    print(f"  出力トークン: {final.usage.output_tokens:,}")
    print(f"{'='*60}\n")


def main() -> None:
    try:
        fetch_and_summarize_ai_news()
    except anthropic.AuthenticationError:
        print("❌ エラー: ANTHROPIC_API_KEY が無効または未設定です。")
        print("   export ANTHROPIC_API_KEY='your-api-key' を実行してください。")
        raise SystemExit(1)
    except anthropic.RateLimitError:
        print("❌ エラー: APIレート制限に達しました。しばらく待ってから再試行してください。")
        raise SystemExit(1)
    except anthropic.APIConnectionError:
        print("❌ エラー: APIに接続できません。ネットワーク接続を確認してください。")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
