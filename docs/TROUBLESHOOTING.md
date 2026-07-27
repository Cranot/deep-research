# Troubleshooting Guide

This guide helps you diagnose and fix common issues with deep-research.

## Quick Diagnostics

Run the validate command to check your setup:

```bash
deep-research validate "Test question" -m opus
```

This will check:
- Question validity
- Model specification
- API key presence

---

## Common Errors

### API Key Errors

**Claude and Gemini do not use API keys.** They shell out to the local `claude`
and `gemini` CLIs and inherit whatever session those are logged into. If a
Claude-backed run fails, the problem is the CLI, not a key:

```bash
which claude          # must resolve
claude -p "hello"     # must answer without prompting you to log in
```

If it is missing: `npm install -g @anthropic-ai/claude-code`, then run `claude`
once to log in. `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` are never read for
authentication anywhere in this project.

**Error: `API key not found for provider 'openai'. Set the GPT5_MINI_API_KEY environment variable.`**

**Cause:** A key-based provider is selected but its key is not set.

**Solution:**
```bash
# Linux/macOS
export GPT5_MINI_API_KEY=your-key-here

# Windows PowerShell
$env:GPT5_MINI_API_KEY = "your-key-here"

# Windows CMD
set GPT5_MINI_API_KEY=your-key-here
```

**Required environment variables by provider:**

| Provider | Required variables |
|----------|-------------------|
| Claude | none — uses the local `claude` CLI |
| Gemini | none — uses the local `gemini` CLI |
| OpenAI (Azure) | `GPT5_MINI_API_KEY` + `GPT5_MINI_ENDPOINT` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Kimi | `KIMI_API_KEY` + `KIMI_ENDPOINT` |

The two Azure-backed providers have no default endpoint — you must point them at
your own resource, or construction fails with an explicit error.

---

### Question Validation Errors

**Error: `Question cannot be empty`**

**Cause:** Empty string or whitespace-only question provided.

**Solution:** Provide a non-empty question with at least 3 characters.

---

**Error: `Question too short (minimum 3 characters)`**

**Cause:** Question is too short to be meaningful.

**Solution:** Provide a more detailed question.

---

**Error: `Question too long (maximum 10000 characters)`**

**Cause:** Question exceeds the maximum allowed length.

**Solution:** Shorten your question or break it into multiple research runs.

---

**Error: `Question contains invalid control characters`**

**Cause:** The question contains non-printable characters (except newlines/tabs).

**Solution:** Remove control characters from your question. This often happens when copying from certain sources.

---

### Model Validation Errors

**Error: `Unknown provider 'xxx'`**

**Cause:** Invalid provider in model specification.

**Solution:** Use a valid provider. Valid options: `claude`, `gemini`, `openai`, `openrouter`, `kimi`.

**Examples:**
```bash
# Valid
deep-research research -m opus "Question"           # Claude (default)
deep-research research -m gemini:flash "Question"  # Gemini
deep-research research -m openai:gpt5-mini "Question"  # Azure OpenAI
```

---

**Warning: `Model 'xxx' not in known models for provider`**

**Cause:** The model name is not in our list of known models (but may still work).

**Note:** This is a warning, not an error. The request will still be attempted.

**Known models:**
- **Claude:** `opus`, `sonnet`, `haiku`
- **Gemini:** `flash`, `pro`
- **OpenAI:** `gpt5-mini`
- **OpenRouter:** `grok`, `grok-3`, `grok-4`
- **Kimi:** `kimi`, `kimi-k2-thinking`

---

### Configuration Errors

**Error: `Depth cannot be negative`**

**Cause:** Negative depth value provided.

**Solution:** Use depth >= 0. On the CLI, `0` means "use the configured default"
(`DEEP_RESEARCH_MAX_DEPTH`, normally 5) — it does not mean unlimited.

---

**Error: `Depth exceeds maximum (20)`**

**Cause:** Depth value too high.

**Solution:** Use depth <= 20. Higher depths are rarely useful and can cause very long runs.

---

**Error: `Parallel must be at least 1`**

**Cause:** Invalid parallel value.

**Solution:** Use parallel >= 1 (default is 10).

---

**Error: `Parallel exceeds maximum (100)`**

**Cause:** Too many parallel agents requested.

**Solution:** Use parallel <= 100. Higher values can overwhelm API rate limits.

---

### Runtime Errors

**Error: `API request timed out for claude after 300s`**

**Cause:** The API request took too long.

**Solutions:**
1. Try again (transient network issue)
2. Use a faster model (haiku instead of opus)
3. Reduce question complexity
4. Check your internet connection

---

**Error: `Rate limit exceeded for provider`**

**Cause:** Too many API requests in a short time.

**Solutions:**
1. Wait and try again
2. Reduce `--parallel` value
3. Use caching to avoid repeated requests
4. Check your API plan limits

---

**Error: `Empty response from provider`**

**Cause:** The API returned an empty response.

**Solutions:**
1. Try again (transient issue)
2. Check the question isn't too vague
3. Try a different model

---

**Error: `All child agents failed`**

**Cause:** Every child research thread failed.

**Solutions:**
1. Check individual agent files in `reports/*/agents/` for error details
2. Verify API keys are correct
3. Reduce parallel count
4. Check for rate limiting

---

## Debugging

### Enable Verbose Output

```bash
deep-research research -v "Your question"
```

### Check Agent Files

Each research run creates agent files in `reports/YYYY-MM-DD-slug/agents/`:

```
d0-001-opus.md    # Orchestrator
d1-002-haiku.md   # First child
d1-003-haiku.md   # Second child
...
```

Each file contains:
- Question
- Status (COMPLETE, FAILED, etc.)
- Exploration output
- Child results
- Synthesis
- Error messages (if failed)

### Check Log Files

Research runs create log files:
- `reports/*/research.log` - JSON lines log of all events
- `reports/*/metrics.json` - Summary metrics

### Cache Issues

If you suspect cached responses are causing problems:

```bash
# View cache stats
deep-research cache stats

# Clear the cache
deep-research cache clear
```

---

## Performance Issues

### Research Taking Too Long

1. **Reduce depth:** Use `-d 2` instead of unlimited
2. **Use faster models:** Use `haiku` for researchers, `opus` only for orchestrator
3. **Increase parallel:** Use `-p 20` for more concurrency (watch rate limits)
4. **Enable caching:** Caching is on by default; don't disable it

### Too Many API Calls

1. **Limit depth:** Use `-d 2` to limit recursion
2. **Enable caching:** Repeated questions hit cache
3. **Use ensemble wisely:** Ensemble mode multiplies API calls

### High Costs

1. **Use haiku for leaves:** `-r haiku` is 10-50x cheaper than opus
2. **Use kimi for merging:** `--merger kimi:kimi` is free
3. **Limit depth:** Shallower trees = fewer calls
4. **Use caching:** Avoid duplicate calls

---

## Getting Help

If you're still stuck:

1. Check the [README](../README.md) for examples
2. Check [CLAUDE.md](../CLAUDE.md) for detailed documentation
3. Open an issue at https://github.com/Cranot/deep-research/issues

When reporting issues, include:
- The command you ran
- The full error message
- Output from `deep-research validate "Your question"`
- Python version (`python --version`)
- Operating system
