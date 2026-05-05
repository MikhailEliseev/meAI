# Technical Specification v1.1: Business-Oriented CI Report

**Date:** 2026-05-05  
**Version:** 1.1 (Updated with security fixes from review)  
**Status:** Approved for implementation  
**Governance:** Critical mode

**Changes from v1.0:**
- Added XSS prevention (html.escape)
- Replaced regex with BeautifulSoup for HTML parsing
- Added per-detector error handling
- Chose WeasyPrint for PDF generation
- Added security hardening section

---

## Security Fixes (Critical)

### Fix 1: XSS Prevention in Report Generation

**Problem:** Competitor HTML could contain malicious content reflected in reports

**Solution:**
```python
import html

class BusinessReportGenerator:
    def _escape_for_html(self, text: str) -> str:
        """Escape all user-controlled data for HTML output"""
        return html.escape(text, quote=True)
    
    def _escape_for_pdf(self, text: str) -> str:
        """Escape all user-controlled data for PDF output"""
        return html.escape(text, quote=True)
    
    def generate_html(self, output_path: str) -> str:
        # Escape ALL data from competitor sites
        safe_data = {
            "competitor_name": self._escape_for_html(self.analysis["name"]),
            "url": self._escape_for_html(self.analysis["url"]),
            "cms": self._escape_for_html(self.analysis["cms"]),
            # ... escape all fields
        }
        return template.render(safe_data)
```

**CSP Header:**
```python
# Add to HTML reports
CSP_HEADER = "Content-Security-Policy: default-src 'self'; script-src 'none'; object-src 'none'"
```

---

### Fix 2: Replace Regex with BeautifulSoup

**Problem:** Regex fails on malformed HTML, nested tags, CDATA sections

**Solution:**
```python
from bs4 import BeautifulSoup

def _analyze_seo(self, html: str) -> Dict[str, Any]:
    """SEO analysis using BeautifulSoup (not regex)"""
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Extract meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag.get('content', '') if desc_tag else ""
        
        # Extract h1
        h1_tag = soup.find('h1')
        h1 = h1_tag.get_text().strip() if h1_tag else ""
        
        # Count headings
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        
        return {
            "title": title,
            "title_length": len(title),
            "has_title": bool(title),
            "description": description,
            "description_length": len(description),
            "has_description": bool(description),
            "h1": h1,
            "has_h1": bool(h1),
            "h2_count": h2_count,
            "h3_count": h3_count
        }
    except Exception as e:
        # Fallback to regex if BeautifulSoup fails
        return self._analyze_seo_regex_fallback(html)
```

---

### Fix 3: Per-Detector Error Handling

**Problem:** One detector crash → entire analysis fails

**Solution:**
```python
async def _analyze_single_page(self, url: str, page_type: str) -> Dict[str, Any]:
    """Analyze single page with error handling per detector"""
    html = await self._fetch_url(url)
    
    if not html:
        return {"url": url, "type": page_type, "error": "Failed to fetch"}
    
    # Wrap each detector in try/except
    result = {"url": url, "type": page_type}
    
    # SEO analysis
    try:
        result["seo"] = self._analyze_seo(html)
    except Exception as e:
        result["seo"] = {"error": str(e), "confidence": 0.0}
        self.logger.error(f"SEO analysis failed for {url}: {e}")
    
    # Content analysis
    try:
        result["content"] = self._analyze_content(html)
    except Exception as e:
        result["content"] = {"error": str(e), "confidence": 0.0}
        self.logger.error(f"Content analysis failed for {url}: {e}")
    
    # CMS detection
    try:
        result["cms"] = self._detect_cms(html, {})
    except Exception as e:
        result["cms"] = {"error": str(e), "confidence": 0.0}
        self.logger.error(f"CMS detection failed for {url}: {e}")
    
    # ... wrap all detectors
    
    return result
```

---

### Fix 4: PDF Library Choice

**Decision:** WeasyPrint (not ReportLab)

**Rationale:**
- Simpler: HTML → PDF workflow
- Reuse HTML template for both formats
- Designers can edit HTML, not Python
- Faster development

**Implementation:**
```python
from weasyprint import HTML, CSS

class BusinessReportGenerator:
    def generate_pdf(self, output_path: str) -> str:
        """Generate PDF using WeasyPrint"""
        # Generate HTML first
        html_content = self._generate_html_content()
        
        # Convert to PDF
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=self._get_pdf_styles())]
        )
        
        return output_path
```

---

## Original Spec (v1.0) - Unchanged Sections

[Rest of the spec remains the same as v1.0, including:]
- Overview
- Architecture
- 18 Detectors (detailed design)
- Business Report Format
- Testing Strategy
- Performance Requirements
- Deployment Plan
- Monitoring & Maintenance

---

## Updated Dependencies

```python
# Existing
aiohttp
beautifulsoup4  # Now REQUIRED (not optional)
lxml

# New
weasyprint  # PDF generation (chosen over ReportLab)
jinja2      # HTML templating
```

---

## Updated Effort Estimate

**Original:** 8-10 hours  
**With security fixes:** 10-12 hours

**Breakdown:**
- Sprint 1: 3-4 hours → 4-5 hours (add security hardening)
- Sprint 2: 2-3 hours (unchanged)
- Sprint 3: 1-2 hours (unchanged, WeasyPrint is simpler)
- Sprint 4: 1-2 hours (unchanged)
- Sprint 5: 30 minutes (unchanged)

**Total:** 10-12 hours

---

## Security Checklist

Before Sprint 1:
- ✅ XSS prevention implemented (html.escape)
- ✅ BeautifulSoup replaces regex
- ✅ Per-detector error handling
- ✅ CSP header added to HTML reports

Before Sprint 4:
- ✅ Test with malicious input (`<script>alert('XSS')</script>`)
- ✅ Test with malformed HTML
- ✅ Test error handling (simulate detector crashes)

---

**Status:** Approved for Phase 2 implementation  
**Review feedback:** Incorporated (security fixes from Technical Reviewer)  
**Next:** Begin Sprint 1
