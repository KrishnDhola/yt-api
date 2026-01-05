import asyncio
import aiohttp
import re
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from duckduckgo_search import DDGS  # <--- NEW ENGINE
from bs4 import BeautifulSoup
from user_agent import generate_user_agent

app = FastAPI(title="The Harvester")

# --- CORE LOGIC: THE HARVESTER ---

async def scrape_site(session, url):
    """Visits a site and hunts for emails/phones."""
    try:
        # 4 second timeout per site
        async with session.get(url, timeout=4, allow_redirects=True) as response:
            if response.status != 200: return None
            
            # Decode with error handling
            html = await response.text(errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(" ", strip=True)

            # REGEX HUNTERS
            # Email: Standard loose regex
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
            
            # Phone: Matches (123) 456-7890 or +1 234... or 123-456-7890
            phones = set(re.findall(r'(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}', text))

            # Cleanup: Remove unlikely "phones" (like years 2023, 2024)
            valid_phones = [p for p in phones if len(p) > 9 and "202" not in p]

            if not emails and not valid_phones:
                return None

            return {
                "url": url,
                "title": soup.title.string[:50] if soup.title else "No Title",
                "emails": list(emails),
                "phones": list(valid_phones)
            }
    except:
        return None

async def run_harvest(keyword, limit):
    results = []
    
    # 1. SEARCH PHASE (DuckDuckGo)
    print(f"[*] Searching DDG for: {keyword}...")
    urls = []
    try:
        with DDGS() as ddgs:
            # Fetch results
            ddg_gen = ddgs.text(keyword, max_results=int(limit))
            for r in ddg_gen:
                urls.append(r['href'])
    except Exception as e:
        print(f"Search Error: {e}")
        return [{"url": "Error", "title": "Search Failed (Try again)", "emails": [], "phones": []}]

    if not urls:
        return [{"url": "Zero Results", "title": "Try a broader keyword", "emails": [], "phones": []}]

    # 2. RAID PHASE (Async Fetch)
    print(f"[*] Raiding {len(urls)} sites...")
    headers = {'User-Agent': generate_user_agent()}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [scrape_site(session, url) for url in urls]
        scraped_data = await asyncio.gather(*tasks)

    # Filter empty results
    clean_data = [d for d in scraped_data if d is not None]
    return clean_data

# --- THE UI (HTML/CSS/JS) ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>THE HARVESTER // GOD MODE</title>
    <style>
        :root { --neon: #00ff41; --dark: #0d0d0d; --panel: #1a1a1a; }
        body { background-color: var(--dark); color: #fff; font-family: 'Courier New', monospace; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: var(--neon); text-shadow: 0 0 10px var(--neon); border-bottom: 2px solid var(--neon); padding-bottom: 10px; }
        .control-panel { background: var(--panel); padding: 20px; border: 1px solid #333; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;}
        input { background: #000; border: 1px solid #333; color: var(--neon); padding: 10px; font-family: inherit; width: 300px; }
        select { background: #000; border: 1px solid #333; color: var(--neon); padding: 10px; font-family: inherit; }
        button { background: var(--neon); color: #000; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { box-shadow: 0 0 15px var(--neon); }
        #loader { display: none; color: var(--neon); margin-top: 20px; font-size: 1.2rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 30px; border: 1px solid #333; }
        th { background: #222; color: var(--neon); padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        td { padding: 8px; border-bottom: 1px solid #333; font-size: 0.9rem; vertical-align: top; }
        tr:hover { background: #111; }
        .tag { display: inline-block; background: #222; padding: 2px 6px; border-radius: 4px; margin: 2px; font-size: 0.8rem; border: 1px solid #444; }
        .copy-btn { float: right; background: #333; color: #fff; border: 1px solid #555; }
    </style>
</head>
<body>
    <div class="container">
        <h1>/// THE HARVESTER V2 (DDG) ///</h1>
        <form class="control-panel" action="/harvest" method="post" onsubmit="document.getElementById('loader').style.display='block'">
            <label>TARGET:</label>
            <input type="text" name="keyword" placeholder="e.g. 'Gym owner email New York'" required>
            <label>LIMIT:</label>
            <select name="limit">
                <option value="20">20 Sites</option>
                <option value="50">50 Sites</option>
                <option value="100">100 Sites</option>
            </select>
            <button type="submit">INITIATE SCAN</button>
        </form>
        <div id="loader">
            > BYPASSING GOOGLE IP BLOCKS... <br>
            > DEPLOYING DRONES TO DDG... <br>
            > SCANNING TARGETS...
        </div>
        {% if results %}
        <div style="margin-top: 20px;">
            <h2 style="display:inline;">> INTELLIGENCE REPORT [{{ results|length }} HITS]</h2>
            <button class="copy-btn" onclick="copyTable()">COPY FOR SHEETS</button>
        </div>
        <table id="dataTable">
            <thead>
                <tr>
                    <th>URL</th>
                    <th>EMAILS</th>
                    <th>PHONES</th>
                </tr>
            </thead>
            <tbody>
                {% for row in results %}
                <tr>
                    <td><a href="{{ row.url }}" style="color: #fff; text-decoration: none;" target="_blank">{{ row.url }}</a></td>
                    <td>{% for email in row.emails %}<span class="tag" style="color: #00ff41;">{{ email }}</span><br>{% endfor %}</td>
                    <td>{% for phone in row.phones %}<span class="tag" style="color: #00bfff;">{{ phone }}</span><br>{% endfor %}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
    <script>
        function copyTable() {
            var range = document.createRange();
            range.selectNode(document.getElementById("dataTable"));
            window.getSelection().removeAllRanges(); 
            window.getSelection().addRange(range); 
            document.execCommand("copy");
            window.getSelection().removeAllRanges();
            alert("COPIED!");
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home():
    from jinja2 import Template
    return Template(HTML_TEMPLATE).render(results=None)

@app.post("/harvest", response_class=HTMLResponse)
async def start_harvest(keyword: str = Form(...), limit: int = Form(...)):
    data = await run_harvest(keyword, limit)
    from jinja2 import Template
    return Template(HTML_TEMPLATE).render(results=data)
