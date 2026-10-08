"""Inspect saved IMDb page source to find correct CSS selectors."""
import re

with open("data/page_source.html", "r", encoding="utf-8") as f:
    src = f.read()

# Find the first list item block
start = src.find('ipc-metadata-list-summary-item__tc')
if start == -1:
    print("Could not find list item!")
else:
    chunk = src[start - 100 : start + 5000]
    print(chunk)
