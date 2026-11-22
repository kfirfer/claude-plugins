# Nano Banana

A Claude Code plugin for generating and editing images with Google Gemini **Nano Banana 2.1**.

```bash
claude plugin marketplace add kfirfer/claude-plugins
claude plugin install nano-banana@kfirfer
```

**Requires** [uv](https://docs.astral.sh/uv/) and a `GEMINI_API_KEY`. Get a key from [Google AI Studio](https://aistudio.google.com/apikey); billing must be enabled.

Then just ask Claude for an image. The `nano-banana` skill (`/nano-banana:nano-banana`) handles prompting, settings, checking the result and refining it. The same script is also available as the `nano-banana` shell command while the plugin is enabled; run `nano-banana --help` for all options.

See the [repository README](../../README.md) for features, examples and costs.
