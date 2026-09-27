# Deploying Wuxia for WordPress

Follow this guide from top to bottom and you end with a site whose pages load **and whose episodes play**. Every command is meant to be copied as-is; replace only the values in `ALL_CAPS` (such as `YOUR_DOMAIN`).

- [Before you start: pick your hosting](#1-before-you-start-pick-your-hosting)
- [Path A: a new Ubuntu server](#2-path-a-a-new-ubuntu-server-recommended)
- [Path B: a hosting panel that runs nginx](#3-path-b-a-hosting-panel-that-runs-nginx)
- [Path C: a server that already runs nginx](#4-path-c-a-server-that-already-runs-nginx)
- [Cloudflare](#5-cloudflare)
- [Install the theme and plugin](#6-install-the-theme-and-plugin)
- [Check that video plays](#7-check-that-video-plays)
- [Troubleshooting](#8-troubleshooting)
- [Updates and backups](#9-updates-and-backups)

## How video reaches a viewer

```
viewer ──▶ Cloudflare ──▶ nginx ──▶ WordPress checks the signed /media/ link, names the file
                            │
                            └──▶ nginx fetches the file from your storage (R2, S3, Telegram, …) and streams it
```

WordPress never streams video itself, and viewers never see your storage address. This needs **two nginx rules** ([`server/nginx-wuxia-media.conf`](server/nginx-wuxia-media.conf)). Without them the site works but every episode answers `501 Media is served through nginx`.

## 1. Before you start: pick your hosting

| Your hosting | Pages | Video | Follow |
|---|---|---|---|
| A VPS or dedicated server you can `ssh` into (Ubuntu 24.04) | Yes | Yes | [Path A](#2-path-a-a-new-ubuntu-server-recommended) |
| A panel that runs nginx and accepts custom nginx config (CloudPanel, RunCloud, SpinupWP, GridPane, Plesk with nginx) | Yes | Yes | [Path B](#3-path-b-a-hosting-panel-that-runs-nginx) |
| A server where you already run WordPress on nginx | Yes | Yes | [Path C](#4-path-c-a-server-that-already-runs-nginx) |
| Shared hosting, cPanel, Apache or LiteSpeed | Yes | **No** | Move to one of the rows above |

How to tell what an existing site runs: in a terminal, `curl -sI https://YOUR_DOMAIN/xmlrpc.php`. Behind Cloudflare the `server:` header always says `cloudflare`, so ask your host, or look in its control panel for "nginx" or "Apache/LiteSpeed".

A server with 2 vCPU, 4 GB RAM and 40 GB of disk is plenty to start. The disk also holds the video cache (20 GB by default).

## 2. Path A: a new Ubuntu server (recommended)

Log in as a user with `sudo` on a fresh **Ubuntu 24.04**.

### 2.1 Firewall and packages

```bash
sudo apt update && sudo apt -y upgrade
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw --force enable

sudo apt -y install nginx mariadb-server \
  php8.3-fpm php8.3-mysql php8.3-curl php8.3-xml php8.3-mbstring \
  php8.3-zip php8.3-gd php8.3-intl unzip curl
```

### 2.2 Database

```bash
sudo mysql_secure_installation   # answer Y to every question
sudo mysql -e "CREATE DATABASE wuxia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wuxia'@'localhost' IDENTIFIED BY 'A_STRONG_DB_PASSWORD';
GRANT ALL ON wuxia.* TO 'wuxia'@'localhost'; FLUSH PRIVILEGES;"
```

### 2.3 WordPress files

```bash
sudo mkdir -p /var/www/wuxia
curl -sL https://wordpress.org/latest.tar.gz | sudo tar -xz -C /var/www/wuxia --strip-components=1
sudo chown -R www-data:www-data /var/www/wuxia
```

### 2.4 The Cloudflare origin certificate

Cloudflare talks to your server over HTTPS with a free certificate that lasts 15 years.

1. In Cloudflare: **SSL/TLS → Origin Server → Create Certificate** (keep the defaults) → **Create**.
2. On the server, paste the two blocks it shows:

```bash
sudo mkdir -p /etc/nginx/certs
sudo nano /etc/nginx/certs/origin.pem   # paste "Origin Certificate", save
sudo nano /etc/nginx/certs/origin.key   # paste "Private Key", save
sudo chmod 600 /etc/nginx/certs/origin.key
```

### 2.5 nginx: visitor IPs behind Cloudflare

Without this every visitor looks like a Cloudflare address, and the media rate limit would slow everyone together.

```bash
{ for ip in $(curl -s https://www.cloudflare.com/ips-v4) $(curl -s https://www.cloudflare.com/ips-v6); do
    echo "set_real_ip_from $ip;"; done
  echo "real_ip_header CF-Connecting-IP;"; } | sudo tee /etc/nginx/conf.d/cloudflare-realip.conf
```

### 2.6 nginx: the media rules

```bash
sudo curl -sL -o /etc/nginx/wuxia-media.conf \
  https://raw.githubusercontent.com/Wuxia-KH/wuxia-press-published-/main/server/nginx-wuxia-media.conf
sudo mkdir -p /var/cache/nginx/wuxia && sudo chown -R www-data /var/cache/nginx/wuxia
```

Part 1 of that file belongs inside `http { }` and part 2 inside `server { }`. Split it into two files:

```bash
sudo sed -n '/PART 1: http/,/PART 2: server/p' /etc/nginx/wuxia-media.conf | sudo tee /etc/nginx/conf.d/wuxia-media-http.conf >/dev/null
sudo sed -n '/PART 2: server/,$p' /etc/nginx/wuxia-media.conf | sudo tee /etc/nginx/snippets/wuxia-media-server.conf >/dev/null
```

The file already points at Ubuntu 24.04's PHP (`unix:/run/php/php8.3-fpm.sock`) and CA bundle, so nothing needs changing on this path.

### 2.7 nginx: the site

```bash
sudo tee /etc/nginx/sites-available/wuxia >/dev/null <<'EOF'
server {
	listen 80;
	server_name YOUR_DOMAIN www.YOUR_DOMAIN;
	return 301 https://$host$request_uri;
}

server {
	listen 443 ssl;
	http2 on;
	server_name YOUR_DOMAIN www.YOUR_DOMAIN;
	ssl_certificate     /etc/nginx/certs/origin.pem;
	ssl_certificate_key /etc/nginx/certs/origin.key;

	root /var/www/wuxia;
	index index.php;
	client_max_body_size 32m;
	server_tokens off;

	# Video (Wuxia). Its ^~ locations take priority over the rules below.
	include snippets/wuxia-media-server.conf;

	location ~ /\. { deny all; }
	location = /xmlrpc.php { deny all; }
	location ~* ^/wp-content/uploads/.*\.php$ { deny all; }

	location / {
		try_files $uri $uri/ /index.php?$args;
	}

	location ~ \.php$ {
		try_files $uri =404;
		include fastcgi_params;
		fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
		fastcgi_pass unix:/run/php/php8.3-fpm.sock;
	}

	location ~* \.(css|js|webp|avif|jpg|jpeg|png|svg|ttf|woff2)$ {
		expires 30d;
		access_log off;
	}
}
EOF
sudo sed -i 's/YOUR_DOMAIN/example.com/g' /etc/nginx/sites-available/wuxia   # ← your domain here
sudo ln -sf /etc/nginx/sites-available/wuxia /etc/nginx/sites-enabled/wuxia
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

`nginx -t` must print `syntax is ok` and `test is successful`. If not, see [Troubleshooting](#8-troubleshooting).

Now set up [Cloudflare](#5-cloudflare), then open `https://YOUR_DOMAIN` and run the WordPress installer (database `wuxia`, user `wuxia`, the password from 2.2).

## 3. Path B: a hosting panel that runs nginx

Create the WordPress site in the panel as usual, then add the rules as **custom nginx configuration**:

| Panel | Where |
|---|---|
| CloudPanel | Site → **Vhost** (edit the file directly) |
| RunCloud | Web Application → **NGINX Config** → add a config of type `location.main-before` and one of type `http` |
| SpinupWP | Site → **Custom Nginx Config** (or `/etc/nginx/sites-available/<site>/server/` over SSH) |
| GridPane | `/var/www/<site>/nginx/` includes over SSH |
| Plesk | Domain → **Apache & nginx Settings** → *Additional nginx directives*, with "Proxy mode" **off** |

Then:

1. From [`nginx-wuxia-media.conf`](server/nginx-wuxia-media.conf), put **part 1** where the panel accepts `http`-level config. If it has none, ask your host to add those two lines (`limit_req_zone …` and `proxy_cache_path …`); both are harmless to other sites.
2. Put **part 2** in the site's server block.
3. Change `fastcgi_pass` to the one the panel already uses for PHP. Look for `fastcgi_pass` in the site's vhost; copy that value exactly.
4. Create the cache folder, or ask your host to: `mkdir -p /var/cache/nginx/wuxia`, owned by nginx's user.
5. Save; the panel reloads nginx. If it reports an error, the message names the line.

## 4. Path C: a server that already runs nginx

1. Download [`nginx-wuxia-media.conf`](server/nginx-wuxia-media.conf).
2. **Part 1** inside `http { }` (usually a new file in `/etc/nginx/conf.d/`).
3. **Part 2** inside the site's `server { }`, next to its other `location` blocks.
4. Lines marked `CHANGE`: set `fastcgi_pass` to the same value as your `location ~ \.php$` block; on RHEL, Alma or Rocky set the CA bundle to `/etc/pki/tls/certs/ca-bundle.crt`.
5. `sudo mkdir -p /var/cache/nginx/wuxia && sudo chown -R www-data /var/cache/nginx/wuxia` (the user is `nginx` on RHEL-family systems).
6. If the site is behind Cloudflare, add the visitor-IP file from [2.5](#25-nginx-visitor-ips-behind-cloudflare).
7. `sudo nginx -t && sudo systemctl reload nginx`

## 5. Cloudflare

1. Add the domain; create `A` records for `@` and `www` pointing at the server, **Proxied** (orange cloud).
2. **SSL/TLS → Overview → Full (strict).** Never *Flexible*: it loops wp-admin redirects.
3. **Caching → Cache Rules → Create rule** "Wuxia media": *URI Path starts with* `/media/` → **Eligible for cache**, Edge TTL **Use cache-control header if present**. Segments then come from Cloudflare instead of your server.
4. **Caching → Cache Rules**: bypass cache for `/wp-admin`, `/wp-login.php` and `/wp-json/`.
5. Never cache episode pages (`/episode/…`) or put `/media/` behind a Worker: the first sets each viewer's session, the second skips WordPress's checks.
6. Optional: **Security → WAF → Rate limiting rules**, `/media/` at about 600 requests per minute per IP.

## 6. Install the theme and plugin

1. Download [`wuxia-core.zip`](https://github.com/Wuxia-KH/wuxia-press-published-/releases/latest/download/wuxia-core.zip) and [`wuxia-theme.zip`](https://github.com/Wuxia-KH/wuxia-press-published-/releases/latest/download/wuxia-theme.zip).
2. **Plugins → Add New Plugin → Upload Plugin** → `wuxia-core.zip` → **Activate**.
3. **Appearance → Themes → Add New Theme → Upload Theme** → `wuxia-theme.zip` → **Activate**.
4. **Settings → Permalinks** → **Post name** → **Save**.
5. Recommended, **before adding storage**: give stored credentials their own key. Add to `wp-config.php`, above `/* That's all, stop editing! */`:

   ```php
   define( 'WUXIA_MEDIA_KEY', 'PASTE_64_RANDOM_CHARACTERS' );
   ```

   Make one with `openssl rand -hex 32`. Back it up with the database: if it is lost or changed, storage credentials must be entered again. Without it, the site's WordPress salts are used.
6. Optional, for password-reset and notification mail through an SMTP relay (Brevo, Mailgun, …), also in `wp-config.php`:

   ```php
   define( 'WUXIA_SMTP_HOST', 'smtp-relay.brevo.com' );
   define( 'WUXIA_SMTP_PORT', '587' );
   define( 'WUXIA_SMTP_USER', 'YOUR_SMTP_LOGIN' );
   define( 'WUXIA_SMTP_PASS', 'YOUR_SMTP_KEY' );
   define( 'WUXIA_MAIL_FROM', 'no-reply@YOUR_DOMAIN' );
   ```

7. **Drama Manager → Storage Providers**: connect your storage. **Drama Manager → Import**: upload iVault JSON, or **Add drama**. **Drama Manager → Settings**: Khmer or English.

## 7. Check that video plays

1. Open any episode and press play.
2. Open the browser's developer tools → **Network**, filter `media`.
3. `master.m3u8` and the segment files (`.ts`, `.m4s`, `.single`, `.married`) must answer **200**.
4. Click a segment: its response headers include `x-wuxia-origin-cache: MISS` the first time and `HIT` after, so nginx's cache works.

From a terminal, a quick check that the rules are in place (any episode number works; a bad link is expected):

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://YOUR_DOMAIN/media/1/0.AAAAAAAAAAAAAAAAAAAAAA/master.m3u8
```

`403` or `404` means the rules are working. **`501` means they are not** (see below).

## 8. Troubleshooting

| You see | Meaning | Fix |
|---|---|---|
| `501` "Media is served through nginx" | The request reached WordPress without the media rules. | Add part 2 to the site's `server { }` and reload nginx. On Apache or LiteSpeed hosting this cannot be fixed; move to nginx. |
| `nginx -t`: *"proxy_cache" zone "wuxia_media" is unknown* | Part 1 is missing. | Add part 1 inside `http { }`. |
| `nginx -t`: *"limit_req_zone" directive is not allowed here* | Part 1 was put inside `server { }`. | Move it to `http { }`. |
| Episodes fail and the error log says *Permission denied* under `/var/cache/nginx/wuxia` | nginx's workers can't write the cache folder. | `sudo chown -R www-data /var/cache/nginx/wuxia` (`nginx` on RHEL-family systems), then reload nginx. |
| `502` on every media request, and nginx's error log says *connect() to unix:… failed* | `fastcgi_pass` in part 2 doesn't match your PHP. | Copy the value from your `location ~ \.php$` block. `ls /run/php/` lists the sockets. |
| `502` "Storage did not answer" | nginx couldn't reach your storage. | Check the provider in **Storage Providers**. The error log may say *could not be resolved* (the `resolver` line) or *certificate verify failed* (the CA-bundle line). |
| `503` "Storage is busy" | Telegram asked to slow down. | It retries by itself. |
| `403` "This link has expired" | Media links last six hours. | Reload the page. |
| `404` | That episode or file doesn't exist. | Check the episode's link and provider. |
| `429` | Too many requests from one IP. | Behind Cloudflare, do step [2.5](#25-nginx-visitor-ips-behind-cloudflare) so viewers aren't counted as one. |
| wp-admin loops "too many redirects" | Cloudflare SSL is *Flexible*. | Set **Full (strict)** with the origin certificate. |
| Episode pages or `/shorts/` answer 404 | Permalinks are "Plain". | **Settings → Permalinks → Post name → Save**. |

nginx's error log is `/var/log/nginx/error.log`; media requests are also in the access log.

## 9. Updates and backups

- **Update**: download the new zips and upload them the same way; WordPress asks to replace the installed version. Every release lists `SHA256SUMS`. Check each release's notes for a new `nginx-wuxia-media.conf`.
- **Replaced a video at the same address?** Empty nginx's cache or it keeps the old copy for up to 7 days: `sudo rm -rf /var/cache/nginx/wuxia/*`
- **Back up** the database and `wp-config.php` (it holds `WUXIA_MEDIA_KEY`) every day, and keep a copy off the server:

  ```bash
  sudo mysqldump --single-transaction wuxia | gzip > ~/wuxia-$(date +%F).sql.gz
  ```
