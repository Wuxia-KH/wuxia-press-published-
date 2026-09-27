<p align="center">
  <a href="https://wuxia-kh.github.io/wuxia-press-published-/">
    <img src="assets/img/mark.svg" alt="Wuxia" width="120">
  </a>
</p>

<h1 align="center">Wuxia for WordPress</h1>

<p align="center">
  A free theme and plugin for a Netflix-style site of Chinese and Hong Kong series and films,<br>
  in Khmer or English, on a normal WordPress install.
</p>

<p align="center">
  <a href="https://wuxia-kh.github.io/wuxia-press-published-/"><strong>Website</strong></a>
  ·
  <a href="https://github.com/Wuxia-KH/wuxia-press-published-/releases/latest/download/wuxia-core.zip">Download the plugin</a>
  ·
  <a href="https://github.com/Wuxia-KH/wuxia-press-published-/releases/latest/download/wuxia-theme.zip">Download the theme</a>
</p>

<p align="center">
  <a href="https://github.com/Wuxia-KH/wuxia-press-published-/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/Wuxia-KH/wuxia-press-published-?color=e50914&label=release"></a>
  <img alt="WordPress 6.5+" src="https://img.shields.io/badge/WordPress-6.5%2B-3858e9">
  <img alt="PHP 8.1+" src="https://img.shields.io/badge/PHP-8.1%2B-777bb4">
  <a href="LICENSE"><img alt="GPL-2.0-or-later" src="https://img.shields.io/badge/license-GPL--2.0--or--later-e50914"></a>
</p>

<p align="center"><img src="assets/img/home.webp" alt="The Wuxia home page" width="820"></p>

## What you get

| Download | What it does |
|---|---|
| **`wuxia-core.zip`**, the plugin | The Drama Manager: dramas and episodes (English and Khmer), genres, countries, storage providers for HLS streams behind a signed media address, iVault imports, and **Settings → Site language**. |
| **`wuxia-theme.zip`**, the theme | The front end: billboard and poster rows, Top 10, title pages, an HLS player with subtitles and quality, New & Popular, search, and a Shorts feed. |

## Install

1. Install WordPress as usual.
2. **Plugins → Add New Plugin → Upload Plugin** → `wuxia-core.zip` → Activate.
3. **Appearance → Themes → Add New Theme → Upload Theme** → `wuxia-theme.zip` → Activate.
4. **Settings → Permalinks** → *Post name* → Save.
5. **Drama Manager → Import** (iVault JSON) or **Add drama**; connect storage under **Storage Providers**; pick the language under **Settings**.

Requires WordPress 6.5+ and PHP 8.1+. No Docker, Redis or command line needed. To update, upload the new zips the same way and let WordPress replace the old version. Every release lists `SHA256SUMS`.

## This repository

This repo holds the website (GitHub Pages, served from `main`) and the release downloads. The theme and plugin are developed elsewhere and published here as zips with each release.

## License

The theme and plugin are free software under the GNU General Public License, version 2 or later (see [LICENSE](LICENSE)). Bundled: hls.js (Apache-2.0) and the Kantumruy Pro font (SIL Open Font License 1.1).
