#!/usr/bin/env bash
set -euo pipefail
umask 077

DISTRIBUTION_METHOD="${IOS_DISTRIBUTION_METHOD:-ad-hoc}"
case "$DISTRIBUTION_METHOD" in
  ad-hoc) PROFILE_SECRET=IOS_ADHOC_PROFILE_BASE64 ;;
  app-store-connect) PROFILE_SECRET=IOS_APPSTORE_PROFILE_BASE64 ;;
  *) echo "Unsupported IOS_DISTRIBUTION_METHOD: $DISTRIBUTION_METHOD"; exit 1 ;;
esac
: "${!PROFILE_SECRET:?Missing provisioning profile secret $PROFILE_SECRET}"
export PROFILE_SECRET DISTRIBUTION_METHOD
KEYCHAIN_PATH="$RUNNER_TEMP/aimharder-signing.keychain-db"
CERTIFICATE_PATH="$RUNNER_TEMP/aimharder-dist.p12"
PROFILE_PATH="$RUNNER_TEMP/aimharder-adhoc.mobileprovision"
PROFILE_PLIST="$RUNNER_TEMP/aimharder-adhoc.plist"
KEYCHAIN_PASSWORD="$(openssl rand -hex 32)"
echo "::add-mask::$KEYCHAIN_PASSWORD"

python3 - <<'PY'
import base64, os
from pathlib import Path
for key, filename in [('IOS_P12_BASE64', 'aimharder-dist.p12'), (os.environ['PROFILE_SECRET'], 'aimharder-adhoc.mobileprovision')]:
    Path(os.environ['RUNNER_TEMP'], filename).write_bytes(base64.b64decode(''.join(os.environ[key].split()), validate=True))
PY

security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security import "$CERTIFICATE_PATH" -P "$IOS_P12_PASSWORD" -A -t cert -f pkcs12 -k "$KEYCHAIN_PATH"
security set-key-partition-list -S apple-tool:,apple:,codesign: -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH" >/dev/null
security list-keychains -d user -s "$KEYCHAIN_PATH" "$HOME/Library/Keychains/login.keychain-db"
security cms -D -i "$PROFILE_PATH" > "$PROFILE_PLIST"
security find-identity -v -p codesigning "$KEYCHAIN_PATH" > "$RUNNER_TEMP/aimharder-identities.txt"

python3 - <<'PY'
import datetime, hashlib, os, plistlib, re, shutil
from pathlib import Path

temp = Path(os.environ['RUNNER_TEMP'])
profile = plistlib.loads((temp / 'aimharder-adhoc.plist').read_bytes())
entitlements = profile.get('Entitlements', {})
team = os.environ['APPLE_TEAM_ID']
bundle = os.environ['APPLE_BUNDLE_ID']
if team not in profile.get('TeamIdentifier', []) or entitlements.get('com.apple.developer.team-identifier') != team:
    raise SystemExit('Provisioning profile does not match APPLE_TEAM_ID')
prefixes = profile.get('ApplicationIdentifierPrefix', [])
if entitlements.get('application-identifier') not in [f'{prefix}.{bundle}' for prefix in prefixes]:
    raise SystemExit('Provisioning profile must match the exact APPLE_BUNDLE_ID')
method = os.environ['DISTRIBUTION_METHOD']
if entitlements.get('get-task-allow'):
    raise SystemExit('Expected a distribution provisioning profile, not Development')
if profile.get('ProvisionsAllDevices'):
    raise SystemExit('Enterprise distribution profiles are not supported')
if method == 'ad-hoc' and not profile.get('ProvisionedDevices'):
    raise SystemExit('Expected an Ad Hoc distribution profile with registered devices')
if method == 'app-store-connect' and profile.get('ProvisionedDevices') is not None:
    raise SystemExit('Expected App Store Connect profile without registered devices')
if profile.get('ExpirationDate', datetime.datetime.min) <= datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
    raise SystemExit('Provisioning profile has expired')
identities = (temp / 'aimharder-identities.txt').read_text()
certificate = next((hashlib.sha1(cert).hexdigest().upper() for cert in profile.get('DeveloperCertificates', [])
                    if hashlib.sha1(cert).hexdigest().upper() in identities), None)
if not certificate:
    raise SystemExit('Imported signing identity does not match profile certificates, or certificate/private key is invalid')
uuid = profile.get('UUID', '')
if not re.fullmatch(r'[A-Fa-f0-9-]{36}', uuid):
    raise SystemExit('Invalid provisioning profile UUID')
paths = [Path.home() / 'Library/MobileDevice/Provisioning Profiles' / f'{uuid}.mobileprovision',
         Path.home() / 'Library/Developer/Xcode/UserData/Provisioning Profiles' / f'{uuid}.mobileprovision']
for path in paths:
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(temp / 'aimharder-adhoc.mobileprovision', path)
with open(os.environ['GITHUB_ENV'], 'a') as output:
    for key, value in {'SIGNING_PROFILE_PATH': paths[0], 'SIGNING_XCODE_PROFILE_PATH': paths[1],
                       'PROFILE_UUID': uuid, 'SIGNING_IDENTITY': certificate}.items():
        output.write(f'{key}={value}\n')
export = {'method': method, 'destination': 'export', 'signingStyle': 'manual',
          'teamID': team, 'signingCertificate': certificate,
          'provisioningProfiles': {bundle: uuid}, 'stripSwiftSymbols': True}
with (temp / 'aimharder-export-options.plist').open('wb') as output:
    plistlib.dump(export, output)
print(f'{method} profile, team and certificate verified')
PY
