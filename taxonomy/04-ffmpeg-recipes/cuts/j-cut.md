# J-cut：先听到下一个镜头

## 1. 描述层

画面仍停留在镜头 A 时，先让镜头 B 的声音进入。到画面切点时，B 的声音继续播放，同一时刻的画面和声音仍然对齐。单独移动整条 B 音轨会改变切点之后的同步关系。

## 2. 参数层

| 参数 | 示例值 | 含义 |
| --- | --- | --- |
| `audio_offset_s` | `-0.5` | B 的声音提前半秒进入 |
| `crossfade_duration_s` | `0.5` | 在画面切点前完成 A、B 的线性淡入淡出 |
| `video_transition` | `hard-cut` | 在输出第 `2.0` 秒硬切画面 |

A 使用源片的 `0.0–2.0` 秒。B 保留从源片第 `0.0` 秒开始的音频，画面从源片第 `0.5` 秒开始。这样输出第 `2.0` 秒的 B 画面与声音都对应 B 源片第 `0.5` 秒。

## 3. 执行层

这个例子需要两个从零开始且画音同步的输入。`a.mp4` 的画面和音频各至少 `2.0` 秒，`b.mp4` 各至少 `2.5` 秒。两个文件都需要音轨。命令将画面统一为 1280 × 720、24 fps，并将音频转为 48 kHz 双声道。

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  '[0:v]trim=start=0:end=2,setpts=PTS-STARTPTS,fps=24,scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[va];
   [1:v]trim=start=0.5:end=2.5,setpts=PTS-STARTPTS,fps=24,scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[vb];
   [va][vb]concat=n=2:v=1:a=0[v];
   [0:a]atrim=start=0:end=2,asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[aa];
   [1:a]atrim=start=0:end=2.5,asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[ab];
   [aa][ab]acrossfade=d=0.5:c1=tri:c2=tri[a]' \
  -map '[v]' -map '[a]' -c:v libx264 -c:a aac -movflags +faststart j-cut.mp4
```

输出约 4 秒。`0.0–1.5` 秒只有 A 的声音，`1.5–2.0` 秒仍是 A 的画面，B 的声音在这一段逐渐进入。从 `2.0` 秒起是 B 的画面和声音。这里对音频做了裁剪和混合，对画面做了裁剪和拼接，因此需要重新编码。

改用自己的切点时，先选 B 要显示的第一帧，再从该帧对应的源时间向前找半秒可用的声音。同步调整 A 的淡出区间和 B 的音频起点。试听切点前后，检查 B 的对白或明显的声音标记是否仍与对应动作一致。

## 4. 反向分镜层

前一镜给关着的门，后一镜给走廊里的脚步。先在门的画面里听到脚步，然后切到走廊，保留脚落地和声音的同步。若前一镜末尾还有一句重要对白，可以缩短重叠区间，给台词留出空间。
