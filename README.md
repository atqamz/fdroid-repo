# Hand Companion F-Droid repository

This repository publishes the F-Droid repository for Hand Companion, the Android
companion of Hand. Nothing is built here: the release job in
https://github.com/atqamz/hand builds the APK and signs it with the app's
release key, and this repository downloads that APK, indexes it with `fdroidserver`
and serves the index and the APK from GitHub Pages. The app is MIT licensed and its
source, releases and issue tracker are in that repository; this repository is a
build product and has no licence of its own.

The repository address:

    https://atqamz.github.io/fdroid-repo/repo

## Add it to the F-Droid client

1. Open F-Droid, then Settings, then Repositories.
2. Add the address above.
3. The client shows the fingerprint of the repository's signing key. It must be
   the line below. If it differs, do not add the repository.

       FINGERPRINT: B5:53:C4:9C:8D:FD:96:AB:F1:1D:F5:1A:CB:2F:C0:54:8A:5D:A4:49:40:E2:C9:A7:7B:5E:6F:D3:19:F8:98:F5

4. Go back to the latest tab and refresh. Hand Companion appears there.

The app needs a laptop that runs Hand. It shows nothing without one: you pair the
phone with the laptop, with a link or a QR code, and the phone dials the laptop over
iroh.

## Check what the repository serves

    curl -sS https://atqamz.github.io/fdroid-repo/repo/index-v2.json | jq '.packages["io.github.atqamz.handcompanion"].versions'
    curl -sS -o index-v1.jar https://atqamz.github.io/fdroid-repo/repo/index-v1.jar
    keytool -printcert -jarfile index-v1.jar

The first prints every published version with the APK's sha256 and its size. The
next two print the certificate that signed the index; its SHA-256 is the fingerprint
above, and the same key signs `index-v1.jar` in `archive/`. Then the APK itself:

    curl -sS -o hand-android-0.1.0.apk https://atqamz.github.io/fdroid-repo/repo/hand-android-0.1.0.apk
    sha256sum hand-android-0.1.0.apk
    apksigner verify --print-certs hand-android-0.1.0.apk

The sha256 is the one the index lists. The certificate SHA-256 is
`9e3c4fecdfd067297cd73e69fa9a8dcedffb11a86f438c5f253a067a6b7f514b`, the app's
release key and the value `AllowedAPKSigningKeys` pins. `apksigner` ships with the
Android build-tools.

## What is here

- `metadata/io.github.atqamz.handcompanion.yml` — name, summary, description,
  licence, the APK's URL pattern for `Binaries` and the allowed signing key. There is
  no build recipe and no `Builds:` entry: this repository publishes the APK that
  `atqamz/hand` signed, it does not rebuild it, and `fdroid update` reads each APK's
  version name and version code from the APK itself. `UpdateCheckMode` is `None`
  because the workflow picks the release itself and `fdroid checkupdates` never runs,
  so a tag pattern would name a check nothing performs. The file has no `RepoType`
  line: `fdroidserver` 2.4.5 rejects `RepoType: None`, and an absent one means no
  source tree is fetched, which is what a binary-only entry needs.
- `config.example.yml` — the `fdroidserver` settings, with `${FDROID_...}`
  placeholders for the three values that are secret. `render_config.py` writes the
  real `config.yml` from it at run time.
- `config/en-US/categories.yml` — the category the app is listed under, for
  `fdroid lint`.
- `icon.png` — the repository's icon in the F-Droid client, the app's own icon.
- `.github/workflows/repo.yaml` — rebuilds the index and deploys it to Pages.
- `repo/` and `archive/` — built by the workflow and never committed. `repo/` holds
  the index and its three newest versions (`archive_older: 3`); older APKs move to
  `archive/`, which has its own index, so an older version stays downloadable.

## For the maintainer

The workflow reads three repository secrets of `atqamz/fdroid-repo`:

- `FDROID_INDEX_KEYSTORE` — base64 of the PKCS#12 keystore that signs the index.
- `FDROID_INDEX_PASSWORD` — the keystore's password.
- `FDROID_KEY_PASSWORD` — the password of the key in it.

Make that key once, offline, and keep a backup. The client pins its fingerprint, so
replacing it means every user removes the repository and adds it again:

    keytool -genkeypair -keystore index.p12 -storetype PKCS12 -alias handcompanion -keyalg RSA -keysize 4096 -validity 10000 -dname "CN=Hand Companion, O=atqamz, C=ID"
    base64 -w0 index.p12

`FDROID_INDEX_KEYSTORE` is the output of the second command, and the alias must stay
`handcompanion`, which is `repo_keyalias` in the template. The fingerprint in this
README is

    keytool -list -v -keystore index.p12 -alias handcompanion | sed -n 's/.*SHA256: //p'

printed as it comes.

A release reaches this repository from `atqamz/hand`: its Android release job
publishes the APK to an `android-vMAJOR.MINOR.PATCH` release and sends a
`repository_dispatch` of type `hand-android-release`. While that step does not
exist, the nightly run at 04:17 UTC and any manual run of the workflow do the same
work from the newest published `android-v*` release of `atqamz/hand`. The selector
takes the first non-draft `android-v*` release and ignores Hand's own `v*` releases
and `edge`, so none of them is mistaken for the app. With no `android-v*` release
yet the run prints `no android-v* release yet; nothing to index` and stops before
the index build and the Pages deploy, leaving the published site alone. A draft
release is invisible to that lookup, so the first run waits until a release is
published.

Publish a version by publishing an `android-vMAJOR.MINOR.PATCH` release with its
APK; no metadata edit is needed, because `fdroid update` takes the version from the
APK. The tag's version is `version` in `android/src-tauri/tauri.conf.json`, and its
`bundle.android.versionCode` is `MAJOR*1000000 + MINOR*1000 + PATCH`; Android
refuses a lower one.

The workflow keeps `repo/` and `archive/` in the Actions cache between runs, so an
APK is downloaded from `atqamz/hand` once and the index is rebuilt from the cached
APKs. A run that finds a release whose APK is missing fails before anything is
published, and the index already on Pages stays. Pages serves the workflow's `site/`
artifact at https://atqamz.github.io/fdroid-repo/; the APKs and the index never
enter this git history.
