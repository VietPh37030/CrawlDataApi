import httpx
from bs4 import BeautifulSoup

# Test 2 different chapter URLs
urls = [
    ('Cam De', 'https://truyenfull.vision/cam-de/chuong-1/'),
    ('Gioi Tu Tien', 'https://truyenfull.vision/gioi-tu-tien-xem-ta-la-an-trong-nhu-nui/chuong-1/')
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9',
}

for name, url in urls:
    print(f"\n=== {name} ===")
    r = httpx.get(url, follow_redirects=True, headers=headers, timeout=30)
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
    
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.select_one('#chapter-c, .chapter-c, .chapter-content')
    
    if content:
        text = content.get_text(strip=True)
        print(f"Content found! Length: {len(text)}")
        print(f"Preview: {text[:200]}...")
    else:
        print("NO CONTENT FOUND!")
        # Look for alternative selectors
        divs = soup.select('div[id], div[class]')
        for d in divs[:10]:
            print(f"  - {d.get('id', '')} / {d.get('class', '')}")
