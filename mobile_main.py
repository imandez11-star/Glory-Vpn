import flet as ft
import socket, time, json, base64, urllib.parse, requests

FLAGS = {"DE":"🇩🇪","US":"🇺🇸","GB":"🇬🇧","FR":"🇫🇷","NL":"🇳🇱","TR":"🇹🇷","FI":"🇫🇮","SE":"🇸🇪","CA":"🇨🇦","SG":"🇸🇬","CH":"🇨🇭","IT":"🇮🇹","ES":"🇪🇸","PL":"🇵🇱","XX":"🌐"}
EN_NAMES = {"DE":"Germany","US":"United States","GB":"United Kingdom","FR":"France","NL":"Netherlands","TR":"Turkey","FI":"Finland","SE":"Sweden","CA":"Canada","SG":"Singapore","CH":"Switzerland","IT":"Italy","ES":"Spain","PL":"Poland","XX":"Unknown"}
KW = {"germany":"DE","de":"DE","germ":"DE","usa":"US","us":"US","america":"US","usai":"US","uk":"GB","england":"GB","ukvman":"GB","france":"FR","french":"FR","netherlands":"NL","nl":"NL","netheri":"NL","finland":"FI","switzerland":"CH","swiss":"CH","canada":"CA","singapore":"SG","spain":"ES","sweden":"SE","italy":"IT","poland":"PL","turkey":"TR"}

def ping_tcp(host, port):
    if not host: return -1
    t0 = time.time()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((host, int(port)))
        s.close()
        return max(int((time.time() - t0)*1000), 1)
    except: return -1

def get_host_port(line):
    try:
        if line.startswith("vmess://"):
            raw = line[8:] + "=" * ((4 - len(line[8:]) % 4) % 4)
            d = json.loads(base64.b64decode(raw).decode('utf-8','ignore'))
            return d.get("add"), d.get("port", 443)
        u = urllib.parse.urlparse(line.split("#")[0])
        return u.hostname, u.port or 443
    except: return None, 443

def detect_cc(line):
    t = urllib.parse.unquote(line).lower()
    for k, v in KW.items():
        if k in t: return v
    return "XX"

def rename_cfg(line, name):
    try:
        if line.startswith("vmess://"):
            raw = line[8:] + "=" * ((4 - len(line[8:]) % 4) % 4)
            d = json.loads(base64.b64decode(raw).decode('utf-8','ignore'))
            d["ps"] = name
            return "vmess://" + base64.b64encode(json.dumps(d).encode()).decode()
        return line.split("#")[0] + "#" + urllib.parse.quote(name)
    except: return line

def main(page: ft.Page):
    page.title = "GloryRaft Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0b0c10"
    page.scroll = ft.ScrollMode.AUTO

    txt_subs = ft.TextField(label="Subscription Links", multiline=True, min_lines=2, max_lines=3, bgcolor="#13151c")
    txt_tpl = ft.TextField(label="Template", value="{flag} | {country_en}", bgcolor="#13151c")
    txt_in = ft.TextField(label="Input Configs", multiline=True, min_lines=4, max_lines=6, bgcolor="#13151c")
    txt_out = ft.TextField(label="Alive & Renamed Configs", multiline=True, min_lines=4, max_lines=6, bgcolor="#13151c", color="#fbbf24")
    lbl_status = ft.Text("Ready", color="#0ea5e9")

    def fetch_subs(e):
        lbl_status.value = "Fetching subs..."
        page.update()
        out = []
        for u in txt_subs.value.splitlines():
            if not u.strip(): continue
            try:
                r = requests.get(u.strip(), timeout=8).text.strip()
                if "://" not in r:
                    r = base64.b64decode(r + "===").decode('utf-8','ignore')
                for l in r.splitlines():
                    if "://" in l: out.append(l.strip())
            except: pass
        txt_in.value = "\n".join(list(dict.fromkeys(out)))
        lbl_status.value = f"Fetched {len(out)} configs"
        page.update()

    def test_and_rename(e):
        lines = [l.strip() for l in txt_in.value.splitlines() if l.strip()]
        lbl_status.value = f"Pinging {len(lines)} configs..."
        page.update()
        alive = []
        idx = 1
        for l in lines:
            h, p = get_host_port(l)
            ms = ping_tcp(h, p)
            if ms > 0:
                cc = detect_cc(l)
                name = txt_tpl.value.replace("{flag}", FLAGS.get(cc,"🌐")).replace("{country_en}", EN_NAMES.get(cc,"Unknown")).replace("{ping}", f"{ms}ms").replace("{num}", f"{idx:02d}")
                alive.append(rename_cfg(l, name))
                idx += 1
        txt_out.value = "\n".join(alive)
        lbl_status.value = f"Done! {len(alive)} Alive configs."
        page.update()

    def push_gh(e):
        if not txt_out.value.strip(): return
        lbl_status.value = "Uploading to GitHub..."
        page.update()
        url = f"https://api.github.com/{USER}/{REPO}/contents/sub.txt"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        r_get = requests.get(f"https://api.github.com/repos/{USER}/{REPO}/contents/sub.txt", headers=headers)
        sha = r_get.json().get("sha") if r_get.status_code == 200 else None
        b64 = base64.b64encode(txt_out.value.encode()).decode()
        payload = {"message":"Mobile Update","content":b64}
        if sha: payload["sha"] = sha
        r = requests.put(f"https://api.github.com/repos/{USER}/{REPO}/contents/sub.txt", headers=headers, json=payload)
        lbl_status.value = "🚀 Uploaded to GitHub!" if r.status_code in [200,201] else "❌ Error uploading"
        page.update()

    page.add(
        ft.Text("⚡ GloryRaft Android", size=22, weight="bold", color="#0ea5e9"),
        txt_subs,
        ft.ElevatedButton("📥 Fetch Subs", on_click=fetch_subs, bgcolor="#0c5a8a", color="white"),
        txt_tpl, txt_in,
        ft.Row([
            ft.ElevatedButton("⚡ Real Ping & Rename", on_click=test_and_rename, bgcolor="#0c5a8a", color="white", expand=True),
            ft.ElevatedButton("🚀 Push GitHub", on_click=push_gh, bgcolor="#0f766e", color="white", expand=True),
        ]),
        txt_out, lbl_status
    )

ft.app(target=main)
