# Open Edit · 本地操作网页（webui）

给非技术用户点的本地网页界面，包在现有 AI 视频生成引擎外面。
**选角色 → 写场景 → 出关键帧 → 关键帧出片**，一条龙在浏览器里点完。

这一层只是 UI，所有生成逻辑都复用 `engine/`（角色 LoRA、相机预设、prompt lint、成本台账），没有重写。

---

## 启动

```bash
cd open-edit
# 首次：装依赖（只多一个 flask）
backend/.venv/bin/pip install -r webui/requirements.txt
# 启动
backend/.venv/bin/python webui/app.py
```

浏览器打开 **http://127.0.0.1:5050**
（手机和电脑同一 WiFi 时，把 127.0.0.1 换成电脑的局域网 IP 也能在手机上看）

启动时会自动读 `config/secrets.env` 里的 API key（FAL_API_KEY 等），无需手动 export。

---

## 怎么用

1. **选角色**：下拉里选 baba / yuer（保持同一张脸的身份角色）。
2. **写场景描述**：一句话画面长什么样，例「烛光城堡宴会厅，暖色低调光，浅景深」。
3. **选相机运镜**：66 个 DoP 预设下拉（如 Dolly In），也可「不指定」。
4. **选 provider**：
   - **mock**（默认）：生成占位图/占位视频，**零成本**，用来先把流程跑通、体验交互。
   - **fal**：**真生成，会花钱** 💸（关键帧约 \$0.003，出片约 \$0.45/5 秒，要等几分钟）。
5. 点 **「生成关键帧」** → 出一张关键帧图 + 显示成本。
6. 在第二步写 **运动描述**（这个镜头里发生什么动作 / 怎么运镜），点 **「关键帧 → 出片」**
   → 出一段 5 秒视频 + 显示成本。
7. 页面底部实时显示**累计花费 + keeper rate**（生成台账）。

生成前会做 prompt 预检（seedance_lint），有问题在图/视频下方黄色提示，不阻断。

---

## 产物位置

- 关键帧图 / 成片视频都存在 `webui/outputs/`，网页通过 `/outputs/<文件名>` 路由读取。
- 生成台账记在 `engine/.work/ledger/webui.jsonl`（项目名固定为 `webui`）。

---

## 技术说明（给后续 agent）

| 步骤 | 引擎调用 |
|---|---|
| 关键帧（fal） | `FalProvider._flux_lora_t2i(mcsla(...), lora_url, trigger, 768, 1344)` |
| 关键帧（mock） | FFmpeg 合成占位竖屏图，零成本 |
| 出片 | `get_provider(provider).submit(GenSpec(kind="i2v", image_path=关键帧, prompt=运动, duration_s=5, width=720, height=1280))` |
| prompt 预检 | `engine.seedance_lint.lint(prompt)` |
| 记账 / 预算 | `engine.ledger.log_gen(...)` / `engine.ledger.budget("webui")` |
| 角色 / 相机 | `engine.character.list_characters()` / `taxonomy/dop_camera_presets.json` |

- 端口 **5050**（避开旧 `web/` 原型）。
- 生成是同步阻塞调用（fal 要几分钟），前端用 loading 转圈提示，没引队列/celery。
- i2v 模型：mock 走 `seedance-2.0`（MockProvider 不在意 model）；fal 真出片走 `kling-i2v`
  （FAL_MODELS 里 `kind=i2v` 的那个，真正吃首帧图）。
- 旧的 `web/app.py` 是无关原型，本目录与它独立，互不影响。
