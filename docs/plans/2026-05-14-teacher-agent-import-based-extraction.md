# Teacher Agent: Import-Based Pattern Extraction

**Дата:** 2026-05-14 10:52 GMT+3  
**Статус:** PLANNING  
**Приоритет:** P0 (блокирует Phase 2)

---

## Проблема

Keyword-based pattern extraction извлекает example usage код вместо реализации.

**Текущее поведение:**
- Domain signatures ищут keywords: "extract", "parse", "trafilatura", "beautifulsoup"
- Находят и примеры (в docstrings, examples/), и реальную реализацию
- Невозможно отличить example от implementation по keywords
- Результат: извлекается `async def request_handler(context)` вместо `trafilatura.extract()`

**Ожидаемое поведение:**
- Найти импорты библиотек: `import trafilatura`, `from bs4 import BeautifulSoup`
- Извлечь функции, которые **используют** эти импорты
- Это будет реальная реализация, а не примеры

---

## Корневая причина

**Keyword-based подход:**
```python
# Ищет keywords в коде
signatures = ["extract", "parse", "trafilatura"]
if any(sig in content for sig in signatures):
    # Находит ВСЁ: и примеры, и реализацию
```

**Проблема:**
- Docstring: `"Use trafilatura to extract content"` → match ✅
- Example: `extracted = extract_crawlee_context(context)` → match ✅
- Real code: `content = trafilatura.extract(raw_html)` → match ✅
- Невозможно отличить!

---

## Решение: Import-Based Extraction

### Подход

1. **Найти импорты библиотек** (AST-based)
   ```python
   import trafilatura
   from bs4 import BeautifulSoup
   import lxml.html as lh
   ```

2. **Найти функции, использующие эти импорты**
   ```python
   def analyze(self, raw_html):
       metadata = trafilatura.extract_metadata(...)  # Uses trafilatura!
       content = trafilatura.extract(...)            # Uses trafilatura!
   ```

3. **Извлечь эти функции целиком**
   - Это реальная реализация
   - Не примеры из docstrings
   - Не example handlers

### Алгоритм

```python
def _extract_functions_using_imports(
    self, 
    content: str, 
    target_imports: list[str]
) -> list[dict]:
    """
    Extract functions that use specific imports.
    
    Args:
        content: File content
        target_imports: List of import names to look for
                       (e.g., ["trafilatura", "BeautifulSoup"])
    
    Returns:
        List of functions using these imports
    """
    tree = ast.parse(content)
    
    # Step 1: Find all imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.add(alias.name)
    
    # Step 2: Check if any target imports present
    if not any(imp in imports for imp in target_imports):
        return []
    
    # Step 3: Find functions using these imports
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_code = ast.get_source_segment(content, node)
            
            # Check if function uses target imports
            uses_import = any(imp in func_code for imp in target_imports)
            
            if uses_import:
                functions.append({
                    "name": node.name,
                    "code": func_code,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "docstring": ast.get_docstring(node),
                })
    
    return functions
```

### Domain Import Signatures

```python
self.domain_import_signatures = {
    "ci-content": [
        "trafilatura",
        "BeautifulSoup",
        "lxml",
        "scrapy",
        "crawlee",
    ],
    "ci-tech": [
        "lighthouse",
        "playwright",
        "selenium",
        "sitemap",
    ],
    "keyword-research": [
        "semrush",
        "ahrefs",
        "serpapi",
    ],
    # ... other subagents
}
```

---

## Implementation Plan

### Step 1: Add domain_import_signatures

```python
# In SkillSelector.__init__()
self.domain_import_signatures = {
    "ci-content": ["trafilatura", "BeautifulSoup", "lxml", "scrapy"],
    "ci-tech": ["lighthouse", "playwright", "selenium"],
    "keyword-research": ["semrush", "ahrefs", "serpapi"],
    "seo": ["pandas", "requests", "httpx"],
    "content": ["openai", "anthropic", "langchain"],
    "ads": ["yandex", "google.ads", "facebook"],
}
```

### Step 2: Implement _extract_functions_using_imports()

```python
def _extract_functions_using_imports(
    self, 
    content: str, 
    target_imports: list[str]
) -> list[dict]:
    # Implementation above
```

### Step 3: Update _detect_patterns()

```python
def _detect_patterns(self, content: str, tree: ast.AST, subagent_type: str = None) -> dict:
    patterns = {}
    
    # Skip generic patterns (already in base.py)
    
    # Extract domain-specific functions by imports
    if subagent_type and subagent_type in self.domain_import_signatures:
        target_imports = self.domain_import_signatures[subagent_type]
        functions = self._extract_functions_using_imports(content, target_imports)
        
        for func in functions:
            pattern_key = f"{subagent_type}_{func['name']}"
            patterns[pattern_key] = {
                "name": f"{subagent_type.title()} - {func['name'].replace('_', ' ').title()}",
                "description": func['docstring'] or f"Function using {', '.join(target_imports)}",
                "code": func['code'],
                "quality_score": self._score_pattern(func['code'], func['name']),
            }
    
    return patterns
```

### Step 4: Test on ci-content

Expected result:
```python
# From python-seo-analyzer/pyseoanalyzer/page.py
def analyze(self, raw_html=None):
    # Use trafilatura to extract metadata
    metadata = trafilatura.extract_metadata(
        filecontent=raw_html,
        default_url=self.url,
        extensive=True,
    )
    
    # use trafulatura to extract the content
    content = trafilatura.extract(
        raw_html,
        include_links=True,
        include_formatting=False,
        include_tables=True,
        include_images=True,
        output_format="json",
    )
```

---

## Expected Result

**До (keyword-based):**
```
Skills extracted: 1,625
Best skill: "Ci-Content - Seo Analysis"
Code: async def request_handler(context: BeautifulSoupCrawlingContext) ❌
      (example handler, not library usage)
```

**После (import-based):**
```
Skills extracted: ~50-100 (only real implementations)
Best skill: "Ci-Content - Analyze"
Code: def analyze(self, raw_html):
          metadata = trafilatura.extract_metadata(...)
          content = trafilatura.extract(...) ✅
      (real library usage!)
```

---

## Validation

**Success criteria:**
- ✅ Извлекаются функции, использующие trafilatura/BeautifulSoup
- ✅ НЕ извлекаются example handlers из docstrings
- ✅ Код содержит реальные вызовы библиотек
- ✅ Применённый код компилируется без SyntaxError
- ✅ Тесты проходят

**Test case:**
```python
# Должна извлечься функция Page.analyze() из python-seo-analyzer
# Содержит: trafilatura.extract_metadata(), trafilatura.extract()
# НЕ должен извлечься: request_handler() из examples/
```

---

## Estimated Time

- Domain import signatures: 15 минут
- _extract_functions_using_imports(): 30 минут
- Update _detect_patterns(): 15 минут
- Testing: 20 минут
- **Total:** 1-1.5 часа

---

## Advantages

**Import-based подход:**
- ✅ Точное определение реальной реализации
- ✅ Не путает examples с implementation
- ✅ Извлекает полные функции (не фрагменты)
- ✅ Меньше шума (только функции с библиотеками)

**Keyword-based подход:**
- ❌ Находит всё подряд (examples, docstrings, real code)
- ❌ Невозможно отличить example от implementation
- ❌ Много ложных срабатываний

---

## Notes

**Почему это важно:**
- Это единственный способ извлечь реальную реализацию
- Keyword-based подход фундаментально не может отличить example от code
- Import-based подход гарантирует, что функция **использует** библиотеку

**Альтернатива:**
- Если import-based не работает → ручная кураци я лучших репо
- Но сначала попробовать import-based (проще и автоматизируемо)

---

**Автор:** Claude Sonnet 4  
**Дата:** 2026-05-14 10:52 GMT+3  
**Статус:** READY TO IMPLEMENT (NEXT SESSION)
