# Cache System

## How it works (simple)

1. **Key** = hash of (prompt + model name)
2. **Value** = the LLM response
3. **Storage** = JSON file (`.cache/responses.json`)

## Flow

```
Request comes in (prompt + model)
        ↓
    Hash the key
        ↓
    Check cache file
        ↓
   Found?
   /    \
 YES     NO
  ↓       ↓
Return   Call LLM
cached   Save to cache
         Return response
```

## Benefits

- **Free repeats** - Re-running tests uses cached answers (no API cost)
- **Deterministic** - Same question = same answer
- **Fast iteration** - Speeds up development

## In practice

When you see `(cached)` in output:
```
[1/11] Getting Gemini 3 Flash answer...
Gemini 3 Flash: 3443 chars  (cached)   ← This was free!
```

## Cache location

```
.cache/
└── responses.json    ← All cached responses here
```

## Clear cache

Delete `.cache/responses.json` to force fresh API calls.
