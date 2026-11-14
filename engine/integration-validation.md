# J-cut / LUT integration validation — 2026-11-14

Base: `7a3ef0ee1dc71c267a1d03465d36b1e66c4ed566` (`main`).

## Attribution and scope

- [PR #4](https://github.com/simonwar119-wq/open-edit/pull/4),
  `aa11a2882ea6cf80c0dd9b471e5b0d862829e30a`, by SeedanceCheap / @pesoszpesosz:
  J-cut recipe preserving B's source audio handle. The recipe is retained and
  supplemented with schema metadata and the application entry point.
- [PR #5](https://github.com/simonwar119-wq/open-edit/pull/5),
  `d863578a469e4b83446bfb66084bea25888d3bac`, by the same contributor:
  identified the two FFmpeg parsing layers affecting Windows LUT paths.
  The integrated helper escapes each layer explicitly, including literal POSIX
  backslashes. Both LUT branches share it.
- The application J-cut path, EDL validation, CLI selection and expanded tests
  were implemented independently on the existing project. Contributor scripts,
  tests and installers were not executed. Original commits remain in history.

## Executed validation

macOS arm64, Python 3.11.18, existing FFmpeg **4.4** and **7.1**; ffprobe **9.0.2**.
No package installation, paid generation, deployment or installed-app replacement.

`python -m unittest engine.test_render -v`: **14 tests pass on each FFmpeg version**,
including an actual `oe.py render ... --j-cut c2:0.5` subprocess with httpx available.
Every FFmpeg test invocation is bounded by a timeout; complete outputs are decoded.

- J-cut output: **4.000 s, 96 frames, 24 fps**, H.264 video + AAC audio.
- Frame 47 remains A; frame 48 is B's source time 0.5 s. A second source
  picture change lands at output frame 72 / 3.0 s.
- B's 880 Hz preroll is absent at 1.3 s, present with A's 440 Hz at 1.75 s;
  the tone changes to 1320 Hz at the 2.0 s picture cut and 1760 Hz at 3.0 s.
  25 ms windows before/after the boundaries verify continued source sync.
- Consecutive J-cuts; J-cut before and after dissolve; mixed ordinary cut;
  one-clip export; legacy cut/dissolve exports; silent outgoing source;
  short outgoing audio; absent incoming audio; video shorter than its audio.
- Invalid lead (zero, negative, NaN, infinity, string, boolean, oversized,
  non-frame-aligned), absent source handle, first-clip J-cut, source overrun
  and CLI id/format errors are rejected.
- Independently constructed standalone recipe: 1280 × 720, 4.000 s, 96 frames.
- LUT strengths **1.0 and 0.7**: three decoded RGB frames match the plain-path
  reference byte for byte for paths with spaces, apostrophes, brackets, comma,
  semicolon, Unicode, colon and a literal POSIX backslash. Both strengths change
  pixels relative to intensity zero, so the test cannot pass by silently skipping LUTs.
- The same independently authored LUT test against the original `main` renderer
  reproduces four failing punctuation/intensity cases.
- Project-required mock workflow: `oe.py plan` then `oe.py make --provider mock
  --style fincher-inspired --prompt "A red desk lamp flickers in an empty workshop."
  --duration 5`, with `OPENEDIT_LLM_PROVIDER=mock`, succeeds on FFmpeg 4.4.
  Result: 720 × 1280, H.264/AAC, three generated clips, zero cost, 4.54 s.
  Ordinary transition overlaps still reduce output duration, as before this change.

The second-version check found that FFmpeg 7.1 requires explicit CFR metadata
before xfade. Mixed paths now declare fps after resetting timestamps. Per-join
frame bounds also prevent FFmpeg 4.4's extra boundary frame from accumulating.

## Limits and existing failures

- **Windows and Linux were not executed locally.** Windows drive-letter parsing is
  covered indirectly by real colon-bearing POSIX paths; that is not a Windows
  filesystem or full application result. The contributor's Windows 8.1.2 result
  remains contributor-reported, not independently verified here.
- No cloud provider, production web service or installed application was deployed.
- The automatic director still plans cut/dissolve. J-cut is available explicitly
  through EDL and the render CLI. Lead and audio crossfade duration are coupled.
- `scripts/validate-frontmatter.py` has one pre-existing failure on
  `taxonomy/PROMPT-DISCIPLINE.md` (missing YAML frontmatter). The new J-cut recipe
  is separately validated and introduces no additional failure.
