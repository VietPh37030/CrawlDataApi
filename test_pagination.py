#!/usr/bin/env python
"""Check actual chapter list pagination on website"""
import sys
sys.path.append('.')

import requests
from bs4 import BeautifulSoup

url = 'https://truyenfull.vision/tam-quoc-dien-nghia/'
html = requests.get(url).text
soup = BeautifulSoup(html, 'lxml')

# Find chapter list section
chapter_section = soup.select_one("#list-chapter, .list-chapter")
if chapter_section:
    print("Found chapter section")
    
    # Count chapters on page 1
    chapters = chapter_section.select("a, li a")
    print(f"Chapters on page 1: {len(chapters)}")
    
    # Find pagination
    pagination = chapter_section.select(".pagination a, ul.pagination a")
    print(f"\nPagination links found: {len(pagination)}")
    
    for i, link in enumerate(pagination[:5]):
        print(f"  {i+1}. {link.get_text(strip=True)} -> {link.get('href', 'NO HREF')}")
else:
    print("Chapter section not found!")
