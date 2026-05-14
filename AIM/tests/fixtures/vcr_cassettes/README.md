# VCR Cassettes for API Testing

This directory contains recorded HTTP interactions (VCR cassettes) for API client tests.

## What is VCR?

VCR (Video Cassette Recorder) records HTTP interactions and replays them during tests. This allows:
- **Fast tests** - No real API calls during testing
- **Deterministic tests** - Same responses every time
- **Offline testing** - No internet required
- **Cost savings** - No API charges during testing

## Recording Cassettes

### First Time Setup

1. **Set API keys in environment:**
```bash
export SEMRUSH_API_KEY="your_real_key"
export AHREFS_API_KEY="your_real_key"
export GA4_CREDENTIALS_PATH="/path/to/credentials.json"
export YANDEX_METRICA_API_KEY="your_real_key"
```

2. **Run tests in record mode:**
```bash
cd /Users/mikhaileliseev/Desktop/Dev/AIM
source venv/bin/activate

# Record all cassettes
python -m pytest tests/unit/test_api_clients.py -v --vcr-record=once

# Or record specific test
python -m pytest tests/unit/test_api_clients.py::TestSEMrushClient::test_expand_keywords_success -v --vcr-record=once
```

3. **Cassettes will be saved here:**
```
tests/fixtures/vcr_cassettes/
├── semrush_expand_keywords.yaml
├── ahrefs_expand_keywords.yaml
├── ga4_get_traffic_data.yaml
└── yandex_get_traffic_data.yaml
```

### Re-recording Cassettes

If API responses change or you need fresh data:

```bash
# Delete old cassettes
rm tests/fixtures/vcr_cassettes/*.yaml

# Re-record
python -m pytest tests/unit/test_api_clients.py -v --vcr-record=once
```

## VCR Modes

- `once` (default) - Record once, then replay. Best for CI/CD.
- `new_episodes` - Record new interactions, replay existing.
- `all` - Always record (overwrites cassettes).
- `none` - Never record, only replay (fails if cassette missing).

## Security

**IMPORTANT:** VCR automatically filters sensitive headers:
- `authorization`
- `x-api-key`

API keys are **NOT** stored in cassettes. Safe to commit to git.

## Cassette Format

Cassettes are YAML files containing:
```yaml
interactions:
- request:
    method: GET
    uri: https://api.semrush.com/...
    headers:
      # API keys filtered out
  response:
    status:
      code: 200
    body:
      string: '{"data": [...]}'
```

## Testing Without Real APIs

After recording, tests run offline:

```bash
# No API keys needed!
python -m pytest tests/unit/test_api_clients.py -v
```

VCR replays recorded responses. Fast and free.

## Troubleshooting

### Cassette not found
```
VCRError: Could not find cassette 'semrush_expand_keywords.yaml'
```
**Solution:** Record cassette first with `--vcr-record=once`

### API key in cassette
```
WARNING: API key found in cassette
```
**Solution:** Check `filter_headers` in test file. Should filter `authorization` and `x-api-key`.

### Stale cassette
```
Response doesn't match current API
```
**Solution:** Delete cassette and re-record with fresh API call.

## Best Practices

1. **Record with real data** - Use actual API keys for recording
2. **Commit cassettes** - Include in git for CI/CD
3. **Update regularly** - Re-record when API changes
4. **Test offline** - Verify tests work without API keys
5. **Filter secrets** - Always filter API keys and tokens

## CI/CD Integration

In CI/CD, tests use recorded cassettes (no API keys needed):

```yaml
# .github/workflows/test.yml
- name: Run API tests
  run: pytest tests/unit/test_api_clients.py -v
  # No API keys in environment!
```

Fast, free, and deterministic tests in CI/CD.
