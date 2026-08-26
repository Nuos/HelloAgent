# 8月26日全网热点追踪｜Article-Lab v1.6.5 总交付包

本目录保存一次完整的跨平台热点状态快照，覆盖抖音、今日头条、微信公众号、微信视频号、Bilibili、快手、新浪微博、X/Twitter、GitHub、YouTube。

## 交付内容

- `article_wechat.html`：微信公众号兼容 HTML，全部采用 inline style。
- `article.md`：完整 Markdown 主稿。
- `SOURCES.md`：事实核验入口与快照边界。
- `QUALITY_REPORT.md`：Article-Lab v1.6.5 质量门报告。
- `MANIFEST.json`：交付包文件清单。
- `assets/README.md`：素材目录说明。

## 核心方法

日报不重新复述所有旧热点，而采用：

**新增事件 + 已有事件的新节点 + 状态迁移 + 热度变化 + 结构趋势**

事件状态包括 NEW、RISING、PEAK、VALIDATION、STRUCTURAL、CRITICAL、RECOVERY、DECAY 等。

## 快照边界

本包保存北京时间 **2026-08-26 早间** 的热点状态。后续若出现新的机器人纪录、灾情更新、监管进展等，不回写本历史快照，而应创建下一期状态迁移记录。

## 发布边界

本包只负责文章内容、HTML格式、事实记录和质量核验，不包含微信公众号素材上传、草稿箱上传或正式发布动作。
