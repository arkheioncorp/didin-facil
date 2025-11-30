#!/bin/bash

# Create archive directory
mkdir -p _archive

# Move log files
mv *.log _archive/ 2>/dev/null
mv api_logs.txt _archive/ 2>/dev/null
mv output.txt _archive/ 2>/dev/null
mv test_output.txt _archive/ 2>/dev/null
mv test_results_full.txt _archive/ 2>/dev/null
mv coverage_output.txt _archive/ 2>/dev/null

# Move debug HTML and PNG files
mv debug_*.html _archive/ 2>/dev/null
mv debug_*.png _archive/ 2>/dev/null
mv error_page.html _archive/ 2>/dev/null
mv error_screenshot.png _archive/ 2>/dev/null
mv stats.html _archive/ 2>/dev/null

# Move other temporary files
mv worker.pid _archive/ 2>/dev/null
mv TEST_SCRAPER_CONSOLE.js _archive/ 2>/dev/null
mv test_tiktok_urls.py _archive/ 2>/dev/null
mv mock_products.sql _archive/ 2>/dev/null

# Move coverage reports from root if they exist (keep the folder if it has useful history, but usually it's generated)
# mv coverage/ _archive/ 2>/dev/null
# mv htmlcov/ _archive/ 2>/dev/null
# mv playwright-report/ _archive/ 2>/dev/null
# mv test-results/ _archive/ 2>/dev/null
# mv test-reports/ _archive/ 2>/dev/null

echo "Cleanup complete. Files moved to _archive/"
