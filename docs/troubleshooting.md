# Troubleshooting

Start with `wwxd doctor`. It checks yt-dlp, the JavaScript runtime, ffmpeg, Whisper
and `$WWXD_HOME`, marks each one OK, WARN or FAIL, and makes no network calls.

## YouTube asks you to sign in

Let yt-dlp use your browser's YouTube cookies. Set
`WWXD_COOKIES_FROM_BROWSER=firefox` (or `chrome:Profile 1`), or pass
`--cookies-from-browser` to `discover`, `update` or `fetch`. You only need this if
YouTube asks you to sign in.

## YouTube rate limits a fetch (HTTP 429)

wwxd waits and retries up to 3 times, at most a minute apart. If a source still
fails, `wwxd fetch <slug> --retry-failed` tries it again later.

## A URL with `?` fails in the shell

Put URLs in quotes, as in `wwxd add jane "https://www.youtube.com/watch?v=…"`. On
macOS the default shell, zsh, otherwise treats the `?` as a filename pattern.
