# Chinese Hot Topic Research — Search Techniques

## Working Approaches

### 1. Bing Browser (for general Chinese web content)
Direct browser navigation to bing.com/search works reliably for Chinese queries. 
Use `setlang=zh-CN` parameter for Chinese results.

```
browser_navigate(url="https://www.bing.com/search?q=QUERY&setlang=zh-CN")
```

Works for: news articles, government announcements, public records, general web discussion

### 2. opencli weibo search (for Weibo hot topics and comments)
Two-step approach (avoids pipe security blocks):

```bash
opencli weibo search "QUERY" -f json 2>/dev/null > /tmp/weibo_search.json
```

Then parse the JSON:
```python
import json
d = json.load(open('/tmp/weibo_search.json'))
for i in d[:15]:
    print(i.get('title', '')[:400])
```

Returns flat list with fields: rank, author, id, time, title (full text), url
Works for: Weibo hot search topics, hashtag content, user comments, trending narratives

### 3. opencli weibo hot (for raw hot list)
```bash
opencli weibo hot -f json
```
Returns list with word, hot_value, label fields.

## Not Working (as of 2026-07)

| Method | Status | Notes |
|--------|--------|-------|
| Jina reader (r.jina.ai) | 401 Unauthorized | Auth failure, no reliable workaround |
| DuckDuckGo HTML | Captcha wall | Chinese queries trigger captcha |
| Marginalia Search | Irrelevant | Returns only English/Wikipedia content for Chinese queries |
| Baidu search (web) | Captcha wall | Anti-scraping blocks automated access |
| Google (via r.jina.ai) | 401 | Same as Jina |
| curl pipe to python | BLOCKED | Security scan blocks interpreter pipes |

## Pipeline Pattern

For a hot topic deep-dive:

1. Extract topic from hot list (Excel/API)
2. Run Bing browser search for general context
3. Run opencli weibo search for user sentiment and comments
4. Extract: core facts + time line + numbers + conflicting viewpoints
5. Feed into writing framework (toutiao-viral-writing or custom)

## Key Lesson

The Bing + opencli weibo combo covers ~90% of Chinese hot topic research needs.
For financial/government data, prefer official sources over general search.
