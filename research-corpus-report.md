# Research Corpus — 语料收集报告

> 任务执行时间：2026-05-13 15:10 ~ 15:45
> 执行 Agent：Hermes（多Agent协作）

---

## 完成情况

### 论文下载：14/14 ✅

| 分类 | 数量 | 状态 |
|------|------|------|
| P1 必读核心 | 5篇 | ✅ 全部成功 |
| P2 重要参考 | 5篇 | ✅ 全部成功 |
| P3 延伸阅读 | 4篇 | ✅ 全部成功 |

所有论文 PDF 均从 arXiv 下载（04-fullshots 从 Nature Scientific Reports 下载）。
每篇论文包含：
- paper.pdf ✅
- metadata.json ✅
- notes.md（占位）✅

### GitHub 仓库克隆：3/3 ✅

| 仓库 | 状态 | 备注 |
|------|------|------|
| ShotClassification | ✅ | litchiar/ShotClassification, 1.1MB |
| movie_shot_classification_dataset | ✅ | magcil/movie_shot_classification_dataset, **1.7GB** ⚠️ 较大 |
| shotdeck-scraper | ✅ | talhapythoneer/shotdeck-scraper, 2.2MB |

### 网页抓取：4/4 ✅

| 网页 | 状态 | 大小 |
|------|------|------|
| Stable Cinemetrics 主页 | ✅ | 96KB |
| Stability SCINE 论文页 | ✅ | 277KB |
| Seedance 技术报告 | ✅ | 145KB |
| Open-Sora v1.0 公告 | ✅ | 88KB |

---

## 下载失败记录

无失败记录。所有资源均可正常访问。

---

## 磁盘占用统计

| 类别 | 路径 | 大小 |
|------|------|------|
| 论文 PDF | references/papers/ | ~185MB |
| GitHub 仓库 | references/repos/ | ~1.7GB |
| 网页 | references/web/ | ~606KB |
| **总计** | | **~1.9GB** |

> ⚠️ 警告：movie_shot_classification_dataset 仓库（1.7GB）占绝大部分空间。
> 如果磁盘空间紧张，可以考虑仅保留该仓库的标注 schema 文档，删除原始数据文件。

---

## 发现的额外有用资源

1. **ShotClassification 仓库**（litchiar/ShotClassification）— FullShots 论文配套代码，包含镜头分类的 PyTorch 实现，可作为分类 pipeline 参考
2. **shotdeck-scraper**（talhapythoneer/shotdeck-scraper）— ShotDeck 抓取工具，可用于后续自动拉取电影剧照作为风格分析素材
3. **Stable Cinemetrics 主页** — 包含 SCINE taxonomy 的可视化交互界面（需浏览器查看）
4. **movie_shot_classification_dataset** — 包含 46K 镜头的标注数据，可直接用于训练或验证分类模型

---

## 下一步建议

1. 由 Claude（Web）阅读论文，做内容梳理
2. 重点关注：各论文中分类清单的精确对比
3. 找出 Open Edit Library 需要覆盖的"剪辑手法"和"风格维度"
4. 设计统一的 taxonomy schema
