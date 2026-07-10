import json
import urllib.request
import sys

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c2804843-dbf9-4d2a-ba07-cfab4f489703"


def send_wecom_markdown(content):
    """发送markdown格式消息到企微群机器人，确保UTF-8编码"""
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode("utf-8"))
    return result


def send_daily_simple(date_str, titles, pages_url="https://merryjiajia-creator.github.io/wuma/"):
    """
    发送简化版日报到企微群（推荐格式）

    titles格式: 用 ||| 分隔的标题列表
    示例: "标题1|||标题2|||标题3|||标题4|||标题5"
    """
    article_lines = "\n".join(
        [f"{i+1}. {title}" for i, title in enumerate(titles)]
    )

    content = f"""**今日物码传播文章推送 - {date_str}**

[点击查看今日文章]({pages_url})

**今日精选5篇深度文章：**
{article_lines}

---
**关键词覆盖：** 饮料开盖扫码营销活动、休闲食品一物一码营销、一物一码营销互动、红包机制和奖品设计、提升复购、再来一瓶
**技术支持：** 智选数字技术(广州)股份有限公司-精明购（IsmartGo）"""

    return send_wecom_markdown(content)


def send_daily_report(date_str, articles, pages_url="https://merryjiajia-creator.github.io/wuma/"):
    """
    发送日报摘要到企微群（完整摘要版）

    articles格式: 每篇文章用 title##summary 表示，多篇文章用 ||| 分隔
    示例: "标题1##摘要1|||标题2##摘要2"
    """
    article_blocks = []
    for i, article in enumerate(articles):
        parts = article.split("##", 1)
        if len(parts) == 2:
            title, summary = parts
            # 企微markdown限制，摘要控制在200字以内
            summary = summary.strip()
            if len(summary) > 200:
                summary = summary[:197] + "..."
            article_blocks.append(
                f"**{i+1}. {title.strip()}**\n> {summary}"
            )
        else:
            article_blocks.append(f"**{i+1}. {article.strip()}**")

    article_lines = "\n\n".join(article_blocks)

    content = f"""## 快消品一物一码领域日报
> **{date_str}** | 休食·饮料·酒水

{article_lines}

---
[点击查看完整日报]({pages_url})

_技术支持：精明购 IsmartGo · 一码三域_"""

    return send_wecom_markdown(content)


def send_daily_titles(date_str, titles, pages_url="https://merryjiajia-creator.github.io/wuma/"):
    """
    仅发送标题列表（轻量版）
    titles格式: 用 ||| 分隔的标题列表
    """
    article_lines = "\n".join(
        [f"{i+1}. {title}" for i, title in enumerate(titles)]
    )
    content = f"""## 快消品一物一码领域日报
> **{date_str}** | 休食·饮料·酒水

**今日5条精选动态已更新：**

{article_lines}

[点击查看完整日报]({pages_url})

_技术支持：精明购 IsmartGo · 一码三域_"""

    return send_wecom_markdown(content)


if __name__ == "__main__":
    # 用法1: 简化版（推荐，匹配截图格式）
    # python wecom_send.py "2026年6月5日" "标题1|||标题2|||标题3|||标题4|||标题5"
    #
    # 用法2: 带摘要（完整版）
    # python wecom_send.py "2026年6月5日" "标题1##摘要1|||标题2##摘要2|||..."

    if len(sys.argv) >= 3:
        date_str = sys.argv[1]
        raw = sys.argv[2]
        # 判断是否包含##分隔符
        if "##" in raw:
            articles = raw.split("|||")
            result = send_daily_report(date_str, articles)
        else:
            titles = raw.split("|||")
            result = send_daily_simple(date_str, titles)
    else:
        # 默认测试数据（简化版）
        date_str = "2026年6月18日"
        titles = [
            "摘要酒春节扫码量涨17%：高端白酒一物一码营销互动如何撬动年轻人开瓶潮",
            "2026快消品一物一码头部服务商格局：纳宝科技、易全科技与米多如何定义行业新标准",
            "电解质水\"补水大战\"：东鹏补水啦与元气森林外星人的饮料开盖扫码营销活动博弈",
            "三得利与东方树叶一物一码BC联动对决：无糖茶饮存量增长的新密码",
            "2026年休闲食品一物一码营销：从防窜货管控到消费者复购增长的全链路进化"
        ]
        result = send_daily_simple(date_str, titles)

    print(json.dumps(result, ensure_ascii=False))
