# 🐛 Debug Checklist - Live Test

## Pre-Test Validation

### Environment
- [ ] Chrome installed
- [ ] Cargo build passing
- [ ] Logging enabled (RUST_LOG=debug)
- [ ] Database initialized

### Code Review Points
- [ ] BrowserManager: lifecycle ok?
- [ ] AntiDetection: scripts inject?
- [ ] Parser: selectors current?
- [ ] Commands: error handling?

## Test Execution

### Phase 1: App Start
- [ ] Tauri dev starts
- [ ] Database creates
- [ ] No startup errors

### Phase 2: Scraper Trigger
- [ ] Call scrape_tiktok_shop
- [ ] Browser launches
- [ ] Navigation works

### Phase 3: Scraping
- [ ] Page loads
- [ ] Scripts inject
- [ ] Products parse
- [ ] Data saves

## Known Issues to Watch

1. **chromiumoxide**: May need Chrome path config
2. **Selectors**: TikTok changes DOM frequently
3. **Timeouts**: Might need adjustment
4. **Memory**: Watch for leaks

## Debug Commands

```bash
# Full logging
RUST_LOG=debug cargo tauri dev

# Check logs
tail -f ~/.local/share/tiktrend-finder/logs/*.log

# Monitor resources
htop | grep tiktrend
```

## Issues Found
(Track problems here as they appear)

---

**Status:** Ready for live test
