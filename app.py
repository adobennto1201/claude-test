#!/usr/bin/env python3
"""AIニュースサマリー Webアプリ"""

import json
import anthropic
from datetime import date
from flask import Flask, Response, render_template, stream_with_context

app = Flask(__name__)

SYSTEM_PROMPT = """あなたはAIニュースの専門家です。
最新のAIに関するニュースを検索し、以下の形式でMarkdown形式の日本語でまとめてください：

1. 各ニュースを番号付きリスト（1〜10件）で提示する
2. 各ニュースに：
   - タイトル（## 見出し）
   - 概要（2〜3文）
   - 重要度（⭐️〜⭐️⭐️⭐️）
3. 最後に「## 📊 本日のトレンド総括」セクションを追加する

情報は正確で信頼性の高いソースから取得してください。"""


def stream_ai_news():
    """AIニュースをSSEでストリーミングする"""
    client = anthropic.Anthropic()
    today = date.today().strftime("%Y年%m月%d日")

    try:
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
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
                    block = event.content_block
                    if hasattr(block, "type") and block.type == "server_tool_use":
                        if getattr(block, "name", "") == "web_search":
                            yield f"data: {json.dumps({'type': 'searching'})}\n\n"

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "type") and event.delta.type == "text_delta":
                        yield f"data: {json.dumps({'type': 'text', 'text': event.delta.text})}\n\n"

            final = stream.get_final_message()
            usage = {
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            }
            yield f"data: {json.dumps({'type': 'done', 'usage': usage})}\n\n"

    except anthropic.AuthenticationError:
        yield f"data: {json.dumps({'type': 'error', 'message': 'APIキーが無効です。ANTHROPIC_API_KEY を確認してください。'})}\n\n"
    except anthropic.RateLimitError:
        yield f"data: {json.dumps({'type': 'error', 'message': 'APIレート制限に達しました。しばらく待ってから再試行してください。'})}\n\n"
    except anthropic.APIConnectionError:
        yield f"data: {json.dumps({'type': 'error', 'message': 'APIに接続できません。ネットワーク接続を確認してください。'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.route("/")
def index():
    today = date.today().strftime("%Y年%m月%d日")
    return render_template("index.html", today=today)


@app.route("/stream")
def stream():
    return Response(
        stream_with_context(stream_ai_news()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
