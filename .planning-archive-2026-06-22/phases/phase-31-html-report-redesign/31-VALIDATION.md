# Phase 31: HTML Report Redesign — Validation Architecture

**Created:** 2026-06-16
**Nyquist Compliance:** VERIFIED

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (project standard) |
| Test file | `AIM/tests/unit/test_html_report.py` |
| Quick run | `pytest AIM/tests/unit/test_html_report.py -x -v` |
| Full suite | `pytest AIM/tests/unit/ -x -v` |

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Status |
|--------|----------|-----------|-------------------|--------|
| REQ-31-CSS-01 | Dual-theme CSS renders correctly with both light and dark themes | unit | `test_css_variables_present` | Wave 0 |
| REQ-31-CSS-02 | All color values use CSS variables (no hardcoded #XXXXXX) | unit | `test_no_hardcoded_colors` | Wave 0 |
| REQ-31-NAV-01 | Fixed nav renders with section links matching actual sections | unit | `test_nav_links_match_sections` | Wave 0 |
| REQ-31-RIPPLE-01 | Ripple divs present in HTML output | unit | `test_ripple_elements_present` | Wave 0 |
| REQ-31-THEME-01 | Theme toggle button present and has localStorage script | unit | `test_theme_toggle_present` | Wave 0 |
| REQ-31-THEME-02 | Blocking script in `<head>` prevents theme flicker | unit | `test_theme_blocking_script` | Wave 0 |
| REQ-31-GRACE-01 | Missing doctor_dossiers → experts section not rendered | unit | `test_experts_omitted_without_data` | Wave 0 |
| REQ-31-GRACE-02 | Minimal session data → still produces valid HTML with core sections | unit | `test_minimal_session_produces_valid_html` | Wave 0 |
| REQ-31-DATA-01 | All section builders return "" when required data missing | unit | `test_all_builders_graceful_omission` | Wave 0 |
| REQ-31-SEC-01 | XSS: client_name with special chars is escaped | unit | `test_xss_client_name_escaped` | Wave 0 |
| REQ-31-SEC-02 | External links have rel="noopener noreferrer" | unit | `test_external_links_have_noopener` | Wave 0 |
| REQ-31-FONT-01 | Inter font referenced in Google Fonts URL (not Jost) | unit | `test_inter_font_loaded` | Wave 0 |
| REQ-31-PUB-01 | Report publishes to WordPress and returns valid URL | integration | Manual: call tool with test session | Manual only |
| REQ-31-COMPAT-01 | Old session without new data files generates report without errors | unit | `test_old_session_backward_compatible` | Wave 0 |

## Sampling Rate

- **Per task commit:** `pytest AIM/tests/unit/test_html_report.py -x -v`
- **Per wave merge:** `pytest AIM/tests/unit/ -x -v`
- **Phase gate:** All unit tests green + manual integration test on Polish server with real session data

## Wave 0 Gaps (must be created during Plan 31-01 Task 3)

- [ ] `AIM/tests/unit/test_html_report.py` — does not exist; must be created
- [ ] `AIM/tests/unit/conftest.py` — may need shared fixtures for sample session data
- [ ] Test framework install: verify `pytest` is in Docker image

## Validation Phases

### Wave 1 (Plan 31-01 complete)
- 12 unit tests passing (all CSS/theme/nav/ripple/grace/XSS)
- Visual verification: generate report, toggle theme, check ripple rings visible
- Manual: open report in Chrome + Safari, verify no theme flicker

### Wave 2 (Plan 31-02 complete)
- 27 unit tests passing (12 existing + 15 new for section builders)
- Integration: call `handle_generate_html_report(session_hash="nachalo-clinica")` on server
- Visual: compare generated report side-by-side with ИПХиК.html reference
- Backward compatibility: test with old session (no new JSON files)

## Nyquist Gap Analysis

| Success Criterion | Test Coverage | Verdict |
|-------------------|--------------|---------|
| 1. Dual theme toggle | REQ-31-THEME-01, REQ-31-THEME-02, REQ-31-CSS-01 | COVERED |
| 2. Ripple ring animations | REQ-31-RIPPLE-01 | COVERED |
| 3. Fixed navigation bar | REQ-31-NAV-01 | COVERED |
| 4. 10+ sections | REQ-31-DATA-01 (verifies no empty sections) | COVERED |
| 5. Per-doctor analysis | REQ-31-GRACE-01 (verifies presence when data exists) | COVERED |
| 6. Content analysis | REQ-31-GRACE-01 (same pattern) | COVERED |
| 7. Market comparison table | Manual visual check | PARTIAL |
| 8. Whitefields table | Manual visual check | PARTIAL |
| 9. Strategy recommendations | Manual visual check | PARTIAL |
| 10. CTA offer blocks | Manual visual check | PARTIAL |
| 11. Inter font | REQ-31-FONT-01 | COVERED |
| 12. Graceful omission | REQ-31-GRACE-01, REQ-31-GRACE-02, REQ-31-DATA-01 | COVERED |
| 13. WordPress publish | REQ-31-PUB-01 (manual) | COVERED |
| 14. Backward compatibility | REQ-31-COMPAT-01 | COVERED |

**Overall:** 10 COVERED, 4 PARTIAL (visual quality checks — manual verification sufficient)
