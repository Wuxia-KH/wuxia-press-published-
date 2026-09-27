#!/usr/bin/env python3
"""Builds deploy.html, the web version of DEPLOY.md.

The commands and configuration come from DEPLOY.md's code blocks, in order, so
the page never drifts from the guide that was tested. After editing DEPLOY.md:

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

blocks = [
    (m.group(1) or "text", textwrap.dedent(m.group(2)).strip("\n"))
    for m in re.finditer(r"```(\w*)\n(.*?)\n\s*```", (ROOT / "DEPLOY.md").read_text(), re.S)
]
assert len(blocks) == 13, f"DEPLOY.md has {len(blocks)} code blocks; update build-deploy.py"


def code(i: int, label: str) -> str:
    lang, body = blocks[i]
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
]

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
      <nav class="menu" aria-label="Site">
        <a class="wide" href="./#features">Features</a>
        <a class="wide" href="./#install">Install</a>
        <a href="deploy.html" aria-current="page">Deploy</a>
        <a href="{REPO}/releases">Releases</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="doc-hero">
      <div class="wrap">
        <p class="eyebrow">Deployment guide</p>
        <h1>Deploy Wuxia so every episode plays.</h1>
        <p class="lede">Follow the guide from top to bottom. Copy each command as it is; change only the values in <code>ALL_CAPS</code>, such as <code>YOUR_DOMAIN</code>.</p>
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
          {code(1, "Terminal")}

          <h3 id="a2"><span class="step">A2</span>Database</h3>
          <p>Replace <code>A_STRONG_DB_PASSWORD</code>; you need it again in the WordPress installer.</p>
          {code(2, "Terminal")}

          <h3 id="a3"><span class="step">A3</span>WordPress files</h3>
          {code(3, "Terminal")}

          <h3 id="a4"><span class="step">A4</span>The Cloudflare origin certificate</h3>
          <p>Cloudflare talks to your server over HTTPS with a free certificate that lasts 15 years.</p>
          <ol class="plain">
            <li>In Cloudflare: <span class="path">SSL/TLS → Origin Server → Create Certificate</span>, keep the defaults, <b>Create</b>.</li>
            <li>On the server, paste the two blocks it shows:</li>
          </ol>
          {code(4, "Terminal")}

          <h3 id="a5"><span class="step">A5</span>Visitor IPs behind Cloudflare</h3>
          <p>Without this every visitor looks like a Cloudflare address, and the media rate limit would slow everyone down together.</p>
          {code(5, "Terminal")}

          <h3 id="a6"><span class="step">A6</span>The media rules</h3>
          {code(6, "Terminal")}
          <p>Part 1 of that file belongs inside <code>http {{ }}</code> and part 2 inside <code>server {{ }}</code>. Split it into two files:</p>
          {code(7, "Terminal")}
          <p class="muted">The file already points at Ubuntu 24.04’s PHP (<code>unix:/run/php/php8.3-fpm.sock</code>) and CA bundle, so nothing needs changing on this path.</p>

          <h3 id="a7"><span class="step">A7</span>The site</h3>
          <p>Change <code>example.com</code> in the <code>sed</code> line near the end to your domain before running it.</p>
          {code(8, "Terminal")}
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

        <section class="doc-sec" aria-labelledby="cloudflare">
          <h2 id="cloudflare"><span class="num">5</span>Cloudflare</h2>
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
          <h2 id="install"><span class="num">6</span>Install the theme and plugin</h2>
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
          {code(9, "wp-config.php")}
          <div class="callout warn"><b>Back it up with the database</b><p>If the key is lost or changed, storage credentials must be entered again. Without it, the site’s WordPress salts are used.</p></div>
          <p><b>Optional:</b> password-reset and notification mail through an SMTP relay (Brevo, Mailgun, …), also in <code>wp-config.php</code>:</p>
          {code(10, "wp-config.php")}
          <p>Then: <span class="path">Drama Manager → Storage Providers</span> to connect storage, <span class="path">Drama Manager → Import</span> for iVault JSON (or <b>Add drama</b>), and <span class="path">Drama Manager → Settings</span> for Khmer or English.</p>
        </section>

        <section class="doc-sec" aria-labelledby="check">
          <h2 id="check"><span class="num">7</span>Check that video plays</h2>
          <ol class="steps">
            <li><b>Play</b><p>Open any episode and press play.</p></li>
            <li><b>Network tab</b><p>Open the browser’s developer tools → <b>Network</b>, filter <code>media</code>.</p></li>
            <li><b>200</b><p><code>master.m3u8</code> and the segments (<code>.ts</code>, <code>.m4s</code>, <code>.single</code>, <code>.married</code>) answer <b>200</b>.</p></li>
            <li><b>Cache</b><p>A segment’s response headers show <code>x-wuxia-origin-cache: MISS</code> the first time and <code>HIT</code> after.</p></li>
          </ol>
          <p>Or, from a terminal (a deliberately bad link):</p>
          {code(11, "Terminal")}
          <div class="verdicts">
            <div class="callout ok"><b><code>403</code> or <code>404</code></b><p>The rules are working.</p></div>
            <div class="callout warn"><b><code>501</code></b><p>The rules are missing. See the first row below.</p></div>
          </div>
        </section>

        <section class="doc-sec" aria-labelledby="troubleshooting">
          <h2 id="troubleshooting"><span class="num">8</span>Troubleshooting</h2>
          <div class="table-wrap"><table class="grid-table trouble">
            <thead><tr><th scope="col">You see</th><th scope="col">Meaning</th><th scope="col">Fix</th></tr></thead>
            <tbody>
{trouble}
            </tbody>
          </table></div>
          <p class="muted">nginx’s error log is <code>/var/log/nginx/error.log</code>; media requests are also in the access log.</p>
        </section>

        <section class="doc-sec" aria-labelledby="updates">
          <h2 id="updates"><span class="num">9</span>Updates and backups</h2>
          <ul class="plain">
            <li><b>Update:</b> download the new zips and upload them the same way; WordPress asks to replace the installed version. Every release lists <code>SHA256SUMS</code>. Check each release’s notes for a new <code>nginx-wuxia-media.conf</code>.</li>
            <li><b>Replaced a video at the same address?</b> Empty nginx’s cache, or it keeps the old copy for up to 7 days: <code>sudo rm -rf /var/cache/nginx/wuxia/*</code></li>
            <li><b>Back up</b> the database and <code>wp-config.php</code> (it holds <code>WUXIA_MEDIA_KEY</code>) every day, and keep a copy off the server:</li>
          </ul>
          {code(12, "Terminal")}
        </section>
      </article>
    </div>
  </main>

  <footer>
    <div class="wrap">
      <span>Wuxia for WordPress · GPL-2.0-or-later</span>
      <nav aria-label="Footer">
        <a href="./">Home</a>
        <a href="{REPO}/blob/main/DEPLOY.md">This guide on GitHub</a>
        <a href="{REPO}/releases">Releases</a>
      </nav>
    </div>
  </footer>
</body>
</html>
"""

(ROOT / "deploy.html").write_text(page)
print("deploy.html written")
