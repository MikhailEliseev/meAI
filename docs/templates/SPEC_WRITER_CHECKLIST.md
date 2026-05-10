# Spec Writer Workflow Checklist

**Version:** 2.0  
**Last Updated:** 2026-05-11

## 📋 Pre-Work Checklist

- [ ] Read SESSION.md for context
- [ ] Read MEMO-NEXT-SESSION.md for plan
- [ ] Create main task via TaskCreate
- [ ] Create subtasks for each stage
- [ ] Check AIM/Old for existing implementations
- [ ] Update task status to "in_progress"

## 📋 Stage 1: Brief (5-10 min)

- [ ] **MANDATORY:** Conduct user interview (NEVER skip!)
- [ ] Ask about agent name and purpose
- [ ] Ask about context and specifics
- [ ] Ask about integrations and dependencies
- [ ] Ask about research priorities (CRITICAL, IMPORTANT, OPTIONAL)
- [ ] Save brief to `docs/briefs/[AGENT_NAME]_BRIEF.md`
- [ ] Update SESSION.md: `./scripts/update_session.sh "[Agent Name]" "Brief" "COMPLETED"`
- [ ] Update task status: TaskUpdate(taskId="X", status="completed")
- [ ] **Commit:** `git add docs/briefs/ && git commit -m "docs: add [Agent Name] brief"`

## 📋 Stage 2: Research (10-20 min)

- [ ] Check vault for similar research: `grep -r "[keywords]" obsidian/deep-research/wiki/topics/`
- [ ] If found (>70% match): reuse existing research
- [ ] If not found: launch deep-research in background
- [ ] **While research runs:** Study existing code in AIM/Old
- [ ] Wait for research completion
- [ ] Read research report
- [ ] Verify research quality (sources, metrics, examples)
- [ ] Update SESSION.md: `./scripts/update_session.sh "[Agent Name]" "Research" "COMPLETED"`
- [ ] Update task status: TaskUpdate(taskId="X", status="completed")
- [ ] **Commit:** `git add obsidian/deep-research/ && git commit -m "docs: archive [Agent Name] research"`

## 📋 Stage 3: Write Specification (30-40 min)

- [ ] Read template: `docs/templates/SUBAGENT_SPEC_TEMPLATE.md`
- [ ] Read patterns: `docs/ARCHITECTURE-COMMUNICATION.md`
- [ ] Prepare content (all sections)
- [ ] **Use Large File Write Rule:**
  - [ ] First 150-200 lines via Write tool
  - [ ] Remaining lines via Bash append
  - [ ] Verify: `wc -l spec.md && ls -lh spec.md`
- [ ] Check quality:
  - [ ] Size >30 KB
  - [ ] All sections filled
  - [ ] Examples with code
  - [ ] Statistics with sources
  - [ ] API with prices
  - [ ] Metrics defined
- [ ] Update SESSION.md: `./scripts/update_session.sh "[Agent Name]" "Specification" "COMPLETED"`
- [ ] Update task status: TaskUpdate(taskId="X", status="completed")
- [ ] **Commit:** `git add docs/subagents-specs/ && git commit -m "docs: create [Agent Name] specification"`

## 📋 Stage 4: Archive (5 min)

- [ ] Run ingest script: `python3 scripts/ingest_research.py ~/Documents/[Topic]_Research_[YYYYMMDD]/`
- [ ] Verify vault updated:
  - [ ] Research in `obsidian/deep-research/raw/`
  - [ ] Entry in `wiki/log.md`
  - [ ] Statistics in `wiki/statistics/usage.md`
- [ ] Update SESSION.md: `./scripts/update_session.sh "[Agent Name]" "Archive" "COMPLETED"`
- [ ] Update task status: TaskUpdate(taskId="X", status="completed")

## 📋 Stage 5: Final Commit & Push (5 min)

- [ ] Update SESSION.md with final summary
- [ ] Update MEMO-NEXT-SESSION.md for next agent
- [ ] Generate commit message: `./scripts/generate_commit_message.sh "[Agent Name]" "[brief]" "[research]" "[features]" "[lines]" "[KB]" "[mode]" "[cost]"`
- [ ] Create final commit:
  ```bash
  git add SESSION.md docs/MEMO-NEXT-SESSION.md
  git commit -m "$(./scripts/generate_commit_message.sh ...)"
  ```
- [ ] Push to GitHub: `git push origin main`
- [ ] Update main task status: TaskUpdate(taskId="1", status="completed")
- [ ] Verify push successful

## 🚫 Common Mistakes to Avoid

- [ ] ❌ Skipping user interview
- [ ] ❌ Creating HTML files without request
- [ ] ❌ Calling Bash() without command parameter
- [ ] ❌ Making one big commit at the end
- [ ] ❌ Forgetting to update SESSION.md
- [ ] ❌ Not using TaskCreate/TaskUpdate
- [ ] ❌ Not running research in background
- [ ] ❌ Not studying existing code first

## 📊 Target Metrics

**Time:**
- Brief: 5-10 min
- Research: 10-20 min (background!)
- Write: 30-40 min
- Archive: 5 min
- Commit: 5 min
- **Total:** 1-1.5 hours

**Quality:**
- Size: >30 KB
- Sections: 100% filled
- Metrics: Concrete numbers
- Code: From existing implementations

## 🎓 Lessons Learned

1. **Mandatory interview** — ALWAYS interview before writing
2. **Large file write** — Write + Bash append for big files
3. **Study existing code** — Check AIM/Old first
4. **No HTML by default** — Only Markdown
5. **Use TaskCreate** — Track progress
6. **Frequent commits** — After each stage
7. **Parallel work** — Research in background
8. **Session checkpoints** — Update SESSION.md

---

**Next Agent:** Budget Optimizer Agent (P1, Ads Magister)  
**Estimated Time:** 1-1.5 hours with improvements
