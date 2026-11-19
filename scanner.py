import re
import requests
from rich.console import Console

console = Console()

def youtube_osint():
    console.print("\n[bold yellow][*] YouTube Channel OSINT Intelligence[/bold yellow]")
    yt_url = console.input("Enter YouTube Channel URL or @Handle (e.g., https://www.youtube.com/@vedanshsrivastava182): ").strip()
    
    if yt_url.startswith("@"):
        yt_url = f"https://www.youtube.com/{yt_url}"
    elif not yt_url.startswith("http"):
        yt_url = f"https://www.youtube.com/@{yt_url}"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        console.print(f"[cyan][*] Fetching metadata for: {yt_url}...[/cyan]")
        resp = requests.get(yt_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            console.print("[red][-] Channel not found or invalid URL.[/red]")
            return

        html = resp.text
        
        # Extract Channel ID
        cid_match = re.search(r'"channelId":"(UC[\w-]+)"', html)
        channel_id = cid_match.group(1) if cid_match else "Not Found"
        
        # Extract Title
        title_match = re.search(r'<title>(.*?) - YouTube</title>', html)
        title = title_match.group(1) if title_match else "Unknown"

        console.print(f"[green][+] Channel Name   :[/green] {title}")
        console.print(f"[green][+] Channel ID     :[/green] {channel_id}")
        console.print(f"[green][+] Channels Tab   :[/green] {yt_url}/channels (Check here if subscriptions are public)")
        
        # Google Dork suggestion for public mentions/comments
        handle = yt_url.split("/")[-1]
        dork_url = f"https://www.google.com/search?q=site:youtube.com+%22{handle}%22"
        console.print(f"[green][+] Public Mentions:[/green] {dork_url}")
        console.print("[dim]Note: YouTube hides comment history & private subscriptions by default due to privacy rules.[/dim]")

    except Exception as e:
        console.print(f"[red][-] Error fetching YouTube data: {e}[/red]")
