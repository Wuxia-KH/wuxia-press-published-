#!/usr/bin/env python3
"""Builds deploy.html (the web version of DEPLOY.md), llms.txt and
llms-full.txt (the guide for AI assistants), and the shared site menu and
footer in index.html and deploy.html.

Every command on the page is DEPLOY.md's own code block, found by its first
words, so the page never drifts from the guide that was tested. After editing
DEPLOY.md or the server files:

    python3 build-deploy.py && ./bump-assets.sh
"""
import html
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).parent
REPO = "https://github.com/Wuxia-KH/wuxia-press-published-"
CONF = f"{REPO}/blob/main/server/nginx-wuxia-media.conf"
CORE = f"{REPO}/releases/latest/download/wuxia-core.zip"
THEME = f"{REPO}/releases/latest/download/wuxia-theme.zip"

SITE = "https://wuxia-kh.github.io/wuxia-press-published-"
GUIDE = (ROOT / "DEPLOY.md").read_text()
blocks = [
    (m.group(1) or "text", textwrap.dedent(m.group(2)).strip("\n"))
    for m in re.finditer(r"```(\w*)\n(.*?)\n\s*```", GUIDE, re.S)
]


def block(start: str) -> tuple[str, str]:
    """The one DEPLOY.md code block that begins with `start`."""
    found = [b for b in blocks if b[1].lstrip().startswith(start)]
    assert len(found) == 1, f"{len(found)} code blocks in DEPLOY.md start with {start!r}"
    return found[0]


def code(start: str, label: str) -> str:
    lang, body = block(start)
    return (
        f'<div class="code"><div class="code-bar"><span>{html.escape(label)}</span>'
        f'<button type="button" class="copy" aria-label="Copy {html.escape(label)}">Copy</button></div>'
        f'<pre><code class="lang-{lang}">{html.escape(body)}</code></pre></div>'
    )


def yes(ok: bool) -> str:
    return '<span class="pill ok">Yes</span>' if ok else '<span class="pill no">No</span>'


TOC = [
    ("hosting", "Pick your hosting"),
    ("path-a", "Path A · new Ubuntu server"),
    ("path-b", "Path B · hosting panel"),
    ("path-c", "Path C · existing nginx"),
    ("path-d", "Path D · Nginx Proxy Manager"),
    ("ai", "Deploy with an AI assistant"),
    ("cloudflare", "Cloudflare"),
    ("install", "Theme and plugin"),
    ("check", "Check video plays"),
    ("troubleshooting", "Troubleshooting"),
    ("updates", "Updates and backups"),
]

TROUBLE = [
    ("<code>501</code> “Media is served through nginx”", "The request reached WordPress without the media rules.",
     "Add part 2 to the site’s <code>server { }</code> and reload nginx. On Apache or LiteSpeed hosting this cannot be fixed; move to nginx."),
    ("<code>nginx -t</code>: <em>“proxy_cache” zone “wuxia_media” is unknown</em>", "Part 1 is missing.", "Add part 1 inside <code>http { }</code>."),
    ("<code>nginx -t</code>: <em>“limit_req_zone” directive is not allowed here</em>", "Part 1 was put inside <code>server { }</code>.", "Move it to <code>http { }</code>."),
    ("Episodes fail; the error log says <em>Permission denied</em> under <code>/var/cache/nginx/wuxia</code>", "nginx’s workers can’t write the cache folder.",
     "<code>sudo chown -R www-data /var/cache/nginx/wuxia</code> (<code>nginx</code> on RHEL-family systems), then reload nginx."),
    ("<code>502</code> on every media request; the error log says <em>connect() to unix:… failed</em>", "<code>fastcgi_pass</code> in part 2 doesn’t match your PHP.",
     "Copy the value from your <code>location ~ \\.php$</code> block. <code>ls /run/php/</code> lists the sockets."),
    ("<code>502</code> “Storage did not answer”", "nginx couldn’t reach your storage.",
     "Check the provider in <b>Storage Providers</b>. The error log may say <em>could not be resolved</em> (the <code>resolver</code> line) or <em>certificate verify failed</em> (the CA-bundle line)."),
    ("<code>503</code> “Storage is busy”", "Telegram asked to slow down.", "It retries by itself."),
    ("<code>403</code> “This link has expired”", "Media links last six hours.", "Reload the page."),
    ("<code>404</code>", "That episode or file doesn’t exist.", "Check the episode’s link and provider."),
    ("<code>429</code>", "Too many requests from one IP.", 'Behind Cloudflare, do <a href="#a5">step A5</a> so viewers aren’t counted as one.'),
    ("wp-admin loops “too many redirects”", "Cloudflare SSL is <em>Flexible</em>.", "Set <b>Full (strict)</b> with the origin certificate."),
    ("Episode pages or <code>/shorts/</code> answer 404", "Permalinks are “Plain”.", "<b>Settings → Permalinks → Post name → Save</b>."),
    ("Path D: Nginx Proxy Manager shows <em>502 Bad Gateway</em>", "It can’t reach the <code>web</code> container.",
     "<code>sudo docker compose ps</code>: all four services must be up. The proxy host forwards to <code>web</code>, port <code>80</code>, scheme <code>http</code>."),
    ("Path D: the certificate request fails", "Let’s Encrypt couldn’t check the domain.",
     "The domain must already point at the server. Behind Cloudflare’s orange cloud, use <b>Use a DNS Challenge</b> with a Cloudflare API token."),
    ("Path D: <code>501</code> although everything runs", "<code>site.conf</code> or the split media files are missing.",
     "In <code>~/wuxia</code>, <code>ls nginx</code> must list the five files from step D2; then <code>sudo docker compose restart web</code>."),
]

# One menu and one footer for every page of the site (index.html gets the same).
MENU = [
    ("wide", "./#features", "#features", "Features"),
    ("", "./#install", "#install", "Install"),
    ("", "deploy.html", "deploy.html", "Deploy"),
    ("wide", "./#faq", "#faq", "FAQ"),
    ("", f"{REPO}/releases", f"{REPO}/releases", "Releases"),
]
CONTACT = f"{REPO}/issues/new?template=use-wuxia.yml"
FOOTER = [
    ("deploy.html", "Deployment guide"),
    (f"{REPO}/releases", "All releases"),
    (f"{REPO}/releases/latest", "Changelog &amp; checksums"),
    (REPO, "GitHub"),
    (CONTACT, "Contact us"),
]


def menu(page: str) -> str:
    links = []
    for cls, away, home, label in MENU:
        href = home if page == "index" else away
        attrs = f' class="{cls}"' if cls else ""
        if page == "deploy" and label == "Deploy":
            attrs += ' aria-current="page"'
        links.append(f'        <a{attrs} href="{href}">{label}</a>')
    return '      <nav class="menu" aria-label="Site">\n' + "\n".join(links) + "\n      </nav>"


def footer() -> str:
    links = "\n".join(f'        <a href="{h}">{t}</a>' for h, t in FOOTER)
    return f'      <nav aria-label="Footer">\n{links}\n      </nav>'


toc = "\n".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in TOC)
trouble = "\n".join(
    f'<tr><th scope="row">{a}</th><td>{b}</td><td>{c}</td></tr>' for a, b, c in TROUBLE
)

page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Deploy Wuxia for WordPress: nginx, Cloudflare and video playback</title>
  <meta name="description" content="Step by step: a server whose Wuxia pages load and whose episodes play. A new Ubuntu server, a hosting panel or an existing nginx server, with Cloudflare, checks and troubleshooting.">
  <link rel="canonical" href="https://wuxia-kh.github.io/wuxia-press-published-/deploy.html">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <meta name="theme-color" content="#000000">
  <meta property="og:type" content="article">
  <meta property="og:title" content="Deploy Wuxia for WordPress">
  <meta property="og:description" content="A server whose pages load and whose episodes play, step by step.">
  <meta property="og:url" content="https://wuxia-kh.github.io/wuxia-press-published-/deploy.html">
  <meta property="og:image" content="https://wuxia-kh.github.io/wuxia-press-published-/assets/img/og.png">
  <link rel="preload" href="assets/fonts/KantumruyPro-Variable.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="stylesheet" href="assets/site.css?v=0">
  <script src="assets/deploy.js?v=0" defer></script>
</head>
<body>
  <header class="top">
    <div class="wrap">
      <a class="brand" href="./"><img src="assets/img/mark.svg" alt="" width="34" height="26"><span>WUXIA <small>for WordPress</small></span></a>
{menu("deploy")}
    </div>
  </header>

  <main>
    <section class="doc-hero">
      <div class="wrap">
        <p class="eyebrow">Deployment guide</p>
        <h1>Deploy Wuxia so every episode plays.</h1>
        <p class="lede">Follow the guide from top to bottom. Copy each command as it is; change only the values in <code>ALL_CAPS</code>, such as <code>YOUR_DOMAIN</code>. Or let an <a href="#ai">AI assistant</a> walk you through it.</p>
        <ul class="facts">
          <li>About 30 minutes</li>
          <li>Ubuntu 24.04</li>
          <li>nginx · PHP 8.3 · MariaDB</li>
          <li>Cloudflare</li>
        </ul>
      </div>
    </section>

    <div class="wrap doc">
      <nav class="toc" aria-label="On this page">
        <p>On this page</p>
        <ol>
{toc}
        </ol>
      </nav>

      <article class="doc-body">
        <section class="doc-sec" aria-labelledby="how">
          <h2 id="how">How video reaches a viewer</h2>
          <ol class="flow" aria-label="The path of a video request">
            <li><b>Viewer</b><span>presses play</span></li>
            <li><b>Cloudflare</b><span>caches segments</span></li>
            <li><b>nginx</b><span>the two media rules</span></li>
            <li><b>WordPress</b><span>checks the signed link, names the file</span></li>
            <li class="accent"><b>nginx</b><span>fetches from your storage and streams it</span></li>
          </ol>
          <p>WordPress never streams video itself, and viewers never see your storage address. That takes <strong>two nginx rules</strong>, in <a href="{CONF}"><code>nginx-wuxia-media.conf</code></a>.</p>
          <div class="callout warn"><b>Without the rules</b><p>The site works, but every episode answers <code>501 Media is served through nginx</code>.</p></div>
        </section>

        <section class="doc-sec" aria-labelledby="hosting">
          <h2 id="hosting"><span class="num">1</span>Pick your hosting</h2>
          <div class="table-wrap"><table class="grid-table">
            <thead><tr><th scope="col">Your hosting</th><th scope="col">Pages</th><th scope="col">Video</th><th scope="col">Follow</th></tr></thead>
            <tbody>
              <tr><th scope="row">A VPS or dedicated server you can <code>ssh</code> into (Ubuntu 24.04)</th><td>{yes(True)}</td><td>{yes(True)}</td><td><a href="#path-a">Path A</a></td></tr>
              <tr><th scope="row">A panel that runs nginx and accepts custom nginx config (CloudPanel, RunCloud, SpinupWP, GridPane, Plesk with nginx)</th><td>{yes(True)}</td><td>{yes(True)}</td><td><a href="#path-b">Path B</a></td></tr>
              <tr><th scope="row">A server where you already run WordPress on nginx</th><td>{yes(True)}</td><td>{yes(True)}</td><td><a href="#path-c">Path C</a></td></tr>
              <tr><th scope="row">A server with Docker, where you want <a href="https://nginxproxymanager.com">Nginx Proxy Manager</a> to handle domains and HTTPS certificates</th><td>{yes(True)}</td><td>{yes(True)}</td><td><a href="#path-d">Path D</a></td></tr>
              <tr><th scope="row">Shared hosting, cPanel, Apache or LiteSpeed</th><td>{yes(True)}</td><td>{yes(False)}</td><td>Move to one of the rows above</td></tr>
            </tbody>
          </table></div>
          <p>Not sure what an existing site runs? Behind Cloudflare every answer says <code>server: cloudflare</code>, so ask your host, or look in its control panel for “nginx” or “Apache/LiteSpeed”.</p>
          <p class="muted">A server with 2 vCPU, 4 GB of RAM and 40 GB of disk is plenty to start; the disk also holds the video cache (20 GB by default).</p>
        </section>

        <section class="doc-sec" aria-labelledby="path-a">
          <h2 id="path-a"><span class="num">2</span>Path A · a new Ubuntu server <span class="tag">Recommended</span></h2>
          <p>Log in as a user with <code>sudo</code> on a fresh <strong>Ubuntu 24.04</strong>.</p>

          <h3 id="a1"><span class="step">A1</span>Firewall and packages</h3>
          {code("sudo apt update", "Terminal")}

          <h3 id="a2"><span class="step">A2</span>Database</h3>
          <p>Replace <code>A_STRONG_DB_PASSWORD</code>; you need it again in the WordPress installer.</p>
          {code("sudo mysql_secure_installation", "Terminal")}

          <h3 id="a3"><span class="step">A3</span>WordPress files</h3>
          {code("sudo mkdir -p /var/www/wuxia", "Terminal")}

          <h3 id="a4"><span class="step">A4</span>The Cloudflare origin certificate</h3>
          <p>Cloudflare talks to your server over HTTPS with a free certificate that lasts 15 years.</p>
          <ol class="plain">
            <li>In Cloudflare: <span class="path">SSL/TLS → Origin Server → Create Certificate</span>, keep the defaults, <b>Create</b>.</li>
            <li>On the server, paste the two blocks it shows:</li>
          </ol>
          {code("sudo mkdir -p /etc/nginx/certs", "Terminal")}

          <h3 id="a5"><span class="step">A5</span>Visitor IPs behind Cloudflare</h3>
          <p>Without this every visitor looks like a Cloudflare address, and the media rate limit would slow everyone down together.</p>
          {code("{ for ip in", "Terminal")}

          <h3 id="a6"><span class="step">A6</span>The media rules</h3>
          {code("sudo curl -sL -o /etc/nginx/wuxia-media.conf", "Terminal")}
          <p>Part 1 of that file belongs inside <code>http {{ }}</code> and part 2 inside <code>server {{ }}</code>. Split it into two files:</p>
          {code("sudo sed -n '/PART 1", "Terminal")}
          <p class="muted">The file already points at Ubuntu 24.04’s PHP (<code>unix:/run/php/php8.3-fpm.sock</code>) and CA bundle, so nothing needs changing on this path.</p>

          <h3 id="a7"><span class="step">A7</span>The site</h3>
          <p>Change <code>example.com</code> in the <code>sed</code> line near the end to your domain before running it.</p>
          {code("sudo tee /etc/nginx/sites-available/wuxia", "Terminal")}
          <div class="callout ok"><b>Expected</b><p><code>nginx -t</code> prints <code>syntax is ok</code> and <code>test is successful</code>. Anything else: see <a href="#troubleshooting">Troubleshooting</a>.</p></div>
          <p>Now set up <a href="#cloudflare">Cloudflare</a>, then open <code>https://YOUR_DOMAIN</code> and run the WordPress installer: database <code>wuxia</code>, user <code>wuxia</code>, the password from A2.</p>
        </section>

        <section class="doc-sec" aria-labelledby="path-b">
          <h2 id="path-b"><span class="num">3</span>Path B · a hosting panel that runs nginx</h2>
          <p>Create the WordPress site in the panel as usual, then add the rules as <strong>custom nginx configuration</strong>:</p>
          <div class="table-wrap"><table class="grid-table">
            <thead><tr><th scope="col">Panel</th><th scope="col">Where</th></tr></thead>
            <tbody>
              <tr><th scope="row">CloudPanel</th><td>Site → <b>Vhost</b> (edit the file directly)</td></tr>
              <tr><th scope="row">RunCloud</th><td>Web Application → <b>NGINX Config</b> → a config of type <code>location.main-before</code>, and one of type <code>http</code></td></tr>
              <tr><th scope="row">SpinupWP</th><td>Site → <b>Custom Nginx Config</b> (or <code>/etc/nginx/sites-available/&lt;site&gt;/server/</code> over SSH)</td></tr>
              <tr><th scope="row">GridPane</th><td><code>/var/www/&lt;site&gt;/nginx/</code> includes, over SSH</td></tr>
              <tr><th scope="row">Plesk</th><td>Domain → <b>Apache &amp; nginx Settings</b> → <em>Additional nginx directives</em>, with “Proxy mode” <b>off</b></td></tr>
            </tbody>
          </table></div>
          <ol class="steps">
            <li><b>Part 1 at http level</b><p>From <a href="{CONF}"><code>nginx-wuxia-media.conf</code></a>, put part 1 where the panel accepts <code>http</code>-level config. If it has none, ask your host to add those two lines (<code>limit_req_zone …</code> and <code>proxy_cache_path …</code>); both are harmless to other sites.</p></li>
            <li><b>Part 2 in the site</b><p>Put part 2 in the site’s server block.</p></li>
            <li><b>Point it at PHP</b><p>Find <code>fastcgi_pass</code> in the site’s vhost and copy that value exactly into part 2.</p></li>
            <li><b>Cache folder</b><p><code>mkdir -p /var/cache/nginx/wuxia</code>, owned by nginx’s user (or ask your host).</p></li>
            <li><b>Save</b><p>The panel reloads nginx. If it reports an error, the message names the line.</p></li>
          </ol>
        </section>

        <section class="doc-sec" aria-labelledby="path-c">
          <h2 id="path-c"><span class="num">4</span>Path C · a server that already runs nginx</h2>
          <ol class="steps">
            <li><b>Download</b><p><a href="{CONF}"><code>nginx-wuxia-media.conf</code></a>.</p></li>
            <li><b>Part 1</b><p>Inside <code>http {{ }}</code>, usually as a new file in <code>/etc/nginx/conf.d/</code>.</p></li>
            <li><b>Part 2</b><p>Inside the site’s <code>server {{ }}</code>, next to its other <code>location</code> blocks.</p></li>
            <li><b>Lines marked CHANGE</b><p><code>fastcgi_pass</code>: the same value as your <code>location ~ \\.php$</code> block. On RHEL, Alma or Rocky the CA bundle is <code>/etc/pki/tls/certs/ca-bundle.crt</code>.</p></li>
            <li><b>Cache folder</b><p><code>sudo mkdir -p /var/cache/nginx/wuxia &amp;&amp; sudo chown -R www-data /var/cache/nginx/wuxia</code> (the user is <code>nginx</code> on RHEL-family systems).</p></li>
            <li><b>Behind Cloudflare?</b><p>Add the visitor-IP file from <a href="#a5">step A5</a>.</p></li>
            <li><b>Reload</b><p><code>sudo nginx -t &amp;&amp; sudo systemctl reload nginx</code></p></li>
          </ol>
        </section>

        <section class="doc-sec" aria-labelledby="path-d">
          <h2 id="path-d"><span class="num">5</span>Path D · Docker with Nginx Proxy Manager</h2>
          <p><a href="https://nginxproxymanager.com">Nginx Proxy Manager</a> gives you a web panel for domains and free HTTPS certificates. It only forwards traffic, so the Wuxia media rules live in a small nginx container behind it. Everything runs in Docker from one folder.</p>
          <ol class="flow" aria-label="The path of a request on Path D">
            <li><b>Cloudflare</b><span>optional</span></li>
            <li><b>Nginx Proxy Manager</b><span>domains and HTTPS</span></li>
            <li><b>nginx</b><span>the two media rules</span></li>
            <li><b>WordPress</b><span>PHP-FPM</span></li>
            <li class="accent"><b>MariaDB</b><span>your catalogue</span></li>
          </ol>
          <div class="callout ok"><b>Tested end to end</b><p>An episode’s playlist and video segments played through Nginx Proxy Manager, the second time from nginx’s cache.</p></div>

          <h3 id="d1"><span class="step">D1</span>Docker and the firewall</h3>
          <p>On a fresh Ubuntu 24.04 (Debian works too):</p>
          {code("curl -fsSL https://get.docker.com", "Terminal")}

          <h3 id="d2"><span class="step">D2</span>The files</h3>
          {code("mkdir -p ~/wuxia/nginx", "Terminal")}
          <p class="muted"><code>ls</code> lists <code>cloudflare.conf</code>, <code>nginx-wuxia-media.conf</code>, <code>site.conf</code>, <code>wuxia-media-http.conf</code> and <code>wuxia-media-server.conf</code>. The Cloudflare file lets nginx see visitors’ real addresses behind Cloudflare; without Cloudflare it does nothing. The files: <a href="{REPO}/blob/main/server/nginx-proxy-manager/docker-compose.yml"><code>docker-compose.yml</code></a>, <a href="{REPO}/blob/main/server/nginx-proxy-manager/nginx/site.conf"><code>site.conf</code></a>.</p>

          <h3 id="d3"><span class="step">D3</span>Passwords, then start</h3>
          <p>This puts random database passwords into <code>docker-compose.yml</code>; you never need to type them.</p>
          {code("sed -i \"s/A_STRONG_DB_PASSWORD", "Terminal")}
          <div class="callout ok"><b>Expected</b><p>All four services (<code>npm</code>, <code>db</code>, <code>wordpress</code>, <code>web</code>) show <code>Up</code>.</p></div>

          <h3 id="d4"><span class="step">D4</span>Open the Nginx Proxy Manager panel</h3>
          <p>The panel (port 81) listens only on the server itself, so it is never exposed to the internet. From <strong>your own computer</strong>, open a tunnel:</p>
          {code("ssh -L 8181:127.0.0.1:81", "Your computer")}
          <p>Keep that window open and browse to <code>http://localhost:8181</code>. On the first visit, create the admin account (name, email, password). Older versions show a login instead: <code>admin@example.com</code> / <code>changeme</code>, then ask you to change both.</p>

          <h3 id="d5"><span class="step">D5</span>The proxy host</h3>
          <p>Point <code>YOUR_DOMAIN</code> and <code>www</code> at the server’s IP first (see <a href="#cloudflare">Cloudflare</a>). Then <span class="path">Hosts → Proxy Hosts → Add Proxy Host</span>, <b>Details</b> tab:</p>
          <div class="table-wrap"><table class="grid-table">
            <thead><tr><th scope="col">Field</th><th scope="col">Value</th></tr></thead>
            <tbody>
              <tr><th scope="row">Domain Names</th><td><code>YOUR_DOMAIN</code> and <code>www.YOUR_DOMAIN</code></td></tr>
              <tr><th scope="row">Scheme</th><td><code>http</code></td></tr>
              <tr><th scope="row">Forward Hostname / IP</th><td><code>web</code></td></tr>
              <tr><th scope="row">Forward Port</th><td><code>80</code></td></tr>
              <tr><th scope="row">Cache Assets</th><td>off</td></tr>
              <tr><th scope="row">Block Common Exploits</th><td>off (not needed: WordPress and nginx check every media link themselves)</td></tr>
              <tr><th scope="row">Websockets Support</th><td>off</td></tr>
            </tbody>
          </table></div>
          <p><b>SSL</b> tab: <b>Request a new SSL Certificate</b>, turn on <b>Force SSL</b> and <b>HTTP/2 Support</b>, agree to the terms, <b>Save</b>.</p>
          <ul class="plain">
            <li>With Cloudflare’s orange cloud on, tick <b>Use a DNS Challenge</b>, choose <b>Cloudflare</b>, and paste an API token that can edit the zone’s DNS (Cloudflare → My Profile → API Tokens → <em>Edit zone DNS</em> template).</li>
            <li>Or use a Cloudflare Origin Certificate: <span class="path">SSL Certificates → Add SSL Certificate → Custom</span>, upload the certificate and key from Cloudflare’s <span class="path">SSL/TLS → Origin Server</span>, then pick it on the proxy host’s SSL tab.</li>
          </ul>

          <h3 id="d6"><span class="step">D6</span>WordPress</h3>
          <p>Open <code>https://YOUR_DOMAIN</code>: the installer asks only for a site title and your admin account (the database is already connected). Then continue with <a href="#install">Install the theme and plugin</a>.</p>
          <p class="muted">On this path, <code>wp-config.php</code> settings go in <code>docker-compose.yml</code>, under the <code>wordpress</code> service’s <code>WORDPRESS_CONFIG_EXTRA</code>, one <code>define</code> per line after the one already there; then <code>sudo docker compose up -d</code>.</p>
        </section>

        <section class="doc-sec" aria-labelledby="ai">
          <h2 id="ai"><span class="num">6</span>Deploy with an AI assistant</h2>
          <p>AI assistants such as ChatGPT, Claude, Gemini and Copilot can read this guide and walk you through it, one step at a time. It is published for them as plain text at <a href="llms-full.txt"><code>llms-full.txt</code></a>, with an index at <a href="llms.txt"><code>llms.txt</code></a>.</p>
          <p>Copy this into the assistant and fill in the brackets:</p>
          {code("Help me deploy", "Prompt")}
          <ul class="plain">
            <li><b>Assistants that can run commands</b> on your server (Claude Code, Codex CLI, Gemini CLI and similar) can follow the guide directly. Read each command before you approve it.</li>
            <li><b>Keep secrets out of the chat.</b> The guide generates passwords on the server; an assistant never needs to see them.</li>
            <li><b>The guide is the reference.</b> If an assistant’s advice disagrees with it, trust the guide, especially the nginx rules.</li>
          </ul>
        </section>

        <section class="doc-sec" aria-labelledby="cloudflare">
          <h2 id="cloudflare"><span class="num">7</span>Cloudflare</h2>
          <ol class="steps">
            <li><b>DNS</b><p><code>A</code> records for <code>@</code> and <code>www</code> pointing at the server, <b>Proxied</b> (orange cloud).</p></li>
            <li><b>SSL</b><p><span class="path">SSL/TLS → Overview</span> → <b>Full (strict)</b>. Never <em>Flexible</em>: it loops wp-admin redirects.</p></li>
            <li><b>Cache video</b><p><span class="path">Caching → Cache Rules → Create rule</span> “Wuxia media”: <em>URI Path starts with</em> <code>/media/</code> → <b>Eligible for cache</b>, Edge TTL <b>Use cache-control header if present</b>. Segments then come from Cloudflare instead of your server.</p></li>
            <li><b>Never cache admin</b><p>Another cache rule: bypass cache for <code>/wp-admin</code>, <code>/wp-login.php</code> and <code>/wp-json/</code>.</p></li>
            <li><b>Leave these alone</b><p>Never cache episode pages (<code>/episode/…</code>) and never put <code>/media/</code> behind a Worker: the first sets each viewer’s session, the second skips WordPress’s checks.</p></li>
            <li><b>Optional</b><p><span class="path">Security → WAF → Rate limiting rules</span>: <code>/media/</code> at about 600 requests per minute per IP.</p></li>
          </ol>
        </section>

        <section class="doc-sec" aria-labelledby="install">
          <h2 id="install"><span class="num">8</span>Install the theme and plugin</h2>
          <div class="downloads">
            <a class="btn btn-red" href="{CORE}">Plugin <small>wuxia-core.zip</small></a>
            <a class="btn btn-ghost" href="{THEME}">Theme <small>wuxia-theme.zip</small></a>
          </div>
          <ol class="steps">
            <li><b>Plugin</b><p><span class="path">Plugins → Add New Plugin → Upload Plugin</span> → <code>wuxia-core.zip</code> → <b>Activate</b>.</p></li>
            <li><b>Theme</b><p><span class="path">Appearance → Themes → Add New Theme → Upload Theme</span> → <code>wuxia-theme.zip</code> → <b>Activate</b>.</p></li>
            <li><b>Readable links</b><p><span class="path">Settings → Permalinks</span> → <b>Post name</b> → <b>Save</b>.</p></li>
            <li><b>A media key, before adding storage</b><p>Recommended. Add to <code>wp-config.php</code>, above <code>/* That's all, stop editing! */</code>, a value from <code>openssl rand -hex 32</code>:</p></li>
          </ol>
          {code("define( 'WUXIA_MEDIA_KEY'", "wp-config.php")}
          <div class="callout warn"><b>Back it up with the database</b><p>If the key is lost or changed, storage credentials must be entered again. Without it, the site’s WordPress salts are used.</p></div>
          <p><b>Optional:</b> password-reset and notification mail through an SMTP relay (Brevo, Mailgun, …), also in <code>wp-config.php</code>:</p>
          {code("define( 'WUXIA_SMTP_HOST'", "wp-config.php")}
          <p>Then: <span class="path">Drama Manager → Storage Providers</span> to connect storage, <span class="path">Drama Manager → Import</span> for iVault JSON (or <b>Add drama</b>), and <span class="path">Drama Manager → Settings</span> for Khmer or English.</p>
        </section>

        <section class="doc-sec" aria-labelledby="check">
          <h2 id="check"><span class="num">9</span>Check that video plays</h2>
          <ol class="steps">
            <li><b>Play</b><p>Open any episode and press play.</p></li>
            <li><b>Network tab</b><p>Open the browser’s developer tools → <b>Network</b>, filter <code>media</code>.</p></li>
            <li><b>200</b><p><code>master.m3u8</code> and the segments (<code>.ts</code>, <code>.m4s</code>, <code>.single</code>, <code>.married</code>) answer <b>200</b>.</p></li>
            <li><b>Cache</b><p>A segment’s response headers show <code>x-wuxia-origin-cache: MISS</code> the first time and <code>HIT</code> after.</p></li>
          </ol>
          <p>Or, from a terminal (a deliberately bad link):</p>
          {code("curl -s -o /dev/null -w", "Terminal")}
          <div class="verdicts">
            <div class="callout ok"><b><code>403</code> or <code>404</code></b><p>The rules are working.</p></div>
            <div class="callout warn"><b><code>501</code></b><p>The rules are missing. See the first row below.</p></div>
          </div>
        </section>

        <section class="doc-sec" aria-labelledby="troubleshooting">
          <h2 id="troubleshooting"><span class="num">10</span>Troubleshooting</h2>
          <div class="table-wrap"><table class="grid-table trouble">
            <thead><tr><th scope="col">You see</th><th scope="col">Meaning</th><th scope="col">Fix</th></tr></thead>
            <tbody>
{trouble}
            </tbody>
          </table></div>
          <p class="muted">nginx’s error log is <code>/var/log/nginx/error.log</code>; media requests are also in the access log. On Path D: <code>sudo docker compose logs web</code> (and <code>logs npm</code> for the proxy).</p>
        </section>

        <section class="doc-sec" aria-labelledby="updates">
          <h2 id="updates"><span class="num">11</span>Updates and backups</h2>
          <ul class="plain">
            <li><b>Update:</b> download the new zips and upload them the same way; WordPress asks to replace the installed version. Every release lists <code>SHA256SUMS</code>. Check each release’s notes for a new <code>nginx-wuxia-media.conf</code>.</li>
            <li><b>Replaced a video at the same address?</b> Empty nginx’s cache, or it keeps the old copy for up to 7 days: <code>sudo rm -rf /var/cache/nginx/wuxia/*</code> (Path D: <code>sudo docker compose exec web sh -c 'rm -rf /var/cache/nginx/wuxia/*'</code>)</li>
            <li><b>Path D, updating the containers:</b> <code>cd ~/wuxia &amp;&amp; sudo docker compose pull &amp;&amp; sudo docker compose up -d</code></li>
            <li><b>Back up</b> the database and <code>wp-config.php</code> (it holds <code>WUXIA_MEDIA_KEY</code>; on Path D, <code>docker-compose.yml</code>) every day, and keep a copy off the server. Path D: <code>sudo docker compose exec -T db sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" wuxia' | gzip &gt; ~/wuxia-$(date +%F).sql.gz</code>. Paths A to C:</li>
          </ul>
          {code("sudo mysqldump", "Terminal")}
        </section>
      </article>
    </div>
  </main>

  <footer>
    <div class="wrap">
      <span>Wuxia for WordPress · GPL-2.0-or-later</span>
{footer()}
    </div>
  </footer>
</body>
</html>
"""

(ROOT / "deploy.html").write_text(page)

# The home page shares the menu and footer.
index = (ROOT / "index.html").read_text()
index, n1 = re.subn(r'      <nav class="menu" aria-label="[^"]*">.*?</nav>', lambda _: menu("index"), index, count=1, flags=re.S)
index, n2 = re.subn(r'      <nav aria-label="Footer">.*?</nav>', lambda _: footer(), index, count=1, flags=re.S)
assert n1 == n2 == 1, "index.html: menu or footer not found"
(ROOT / "index.html").write_text(index)

# For AI assistants (llmstxt.org): an index, and the whole guide as text.
server = ROOT / "server"
extras = [
    ("server/nginx-wuxia-media.conf", server / "nginx-wuxia-media.conf"),
    ("server/nginx-proxy-manager/docker-compose.yml", server / "nginx-proxy-manager/docker-compose.yml"),
    ("server/nginx-proxy-manager/nginx/site.conf", server / "nginx-proxy-manager/nginx/site.conf"),
]
full = GUIDE.rstrip() + "\n"
for name, path in extras:
    full += f"\n---\n\n## File: {name}\n\n```\n{path.read_text().rstrip()}\n```\n"
(ROOT / "llms-full.txt").write_text(full)
(ROOT / "llms.txt").write_text(f"""# Wuxia for WordPress

> A free (GPL) WordPress theme and plugin for a Netflix-style site of Chinese and Hong Kong series and films, in Khmer or English. Pages run on any WordPress host; video plays only when nginx serves the site with Wuxia's two media rules (WordPress checks each signed /media/ link, nginx streams the file). Without them every episode answers 501 "Media is served through nginx".

When helping someone deploy it, follow the deployment guide exactly and ask which hosting they have (a new Ubuntu server, a hosting panel running nginx, an existing nginx server, or Docker with Nginx Proxy Manager). Never ask them to paste passwords, API keys or tokens into the chat.

## Deployment

- [Deployment guide, full text]({SITE}/llms-full.txt): every step, command and config file, with troubleshooting
- [Deployment guide, web page]({SITE}/deploy.html)
- [nginx media rules]({REPO}/blob/main/server/nginx-wuxia-media.conf): part 1 in http {{ }}, part 2 in the site's server {{ }}
- [Nginx Proxy Manager stack]({REPO}/tree/main/server/nginx-proxy-manager): docker-compose.yml and nginx/site.conf

## Downloads

- [wuxia-core.zip]({CORE}): the plugin
- [wuxia-theme.zip]({THEME}): the theme
- [Releases]({REPO}/releases): changelog and SHA256SUMS

## Contact

- [Using Wuxia on your site]({CONTACT}): get listed, add your logo to the Site logo switch, or ask for setup help
""")
print("deploy.html, index.html menu and footer, llms.txt, llms-full.txt written")
