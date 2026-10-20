#!/usr/bin/env bash
set -euo pipefail
: "${PROFILE_UUID:?Signing profile was not prepared}"
: "${SIGNING_IDENTITY:?Signing identity was not prepared}"

workspaces=(ios/*.xcworkspace)
projects=(ios/*.xcodeproj)
if [ "${#workspaces[@]}" -ne 1 ] || [ ! -d "${workspaces[0]}" ] || [ "${#projects[@]}" -ne 1 ] || [ ! -d "${projects[0]}" ]; then
  echo 'Expected one generated Expo workspace and project'
  exit 1
fi
mkdir -p output

# Set signing only on the app target; global profile overrides would also affect Pods.
ruby -r xcodeproj - "${projects[0]}" <<'RUBY'
project = Xcodeproj::Project.open(ARGV.fetch(0))
apps = project.targets.select { |target| target.product_type == 'com.apple.product-type.application' }
abort 'Expected one application target' unless apps.length == 1
apps.each do |target|
  target.build_configurations.each do |configuration|
    settings = configuration.build_settings
    settings['CODE_SIGN_STYLE'] = 'Manual'
    settings['DEVELOPMENT_TEAM'] = ENV.fetch('APPLE_TEAM_ID')
    settings['CODE_SIGN_IDENTITY'] = ENV.fetch('SIGNING_IDENTITY')
    settings['PROVISIONING_PROFILE_SPECIFIER'] = ENV.fetch('PROFILE_UUID')
    settings['PRODUCT_BUNDLE_IDENTIFIER'] = ENV.fetch('APPLE_BUNDLE_ID')
    settings['CURRENT_PROJECT_VERSION'] = ENV.fetch('GITHUB_RUN_NUMBER')
  end
end
project.save
RUBY

xcodebuild -workspace "${workspaces[0]}" -scheme AimHarder \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath "$PWD/output/AimHarder.xcarchive" \
  -resultBundlePath "$RUNNER_TEMP/AimHarderArchive.xcresult" \
  archive 2>&1 | tee "$RUNNER_TEMP/aimharder-archive.log"

xcodebuild -exportArchive -archivePath "$PWD/output/AimHarder.xcarchive" \
  -exportPath "$PWD/output" \
  -exportOptionsPlist "$RUNNER_TEMP/aimharder-export-options.plist" \
  2>&1 | tee "$RUNNER_TEMP/aimharder-export.log"

ipas=(output/*.ipa)
test -f "${ipas[0]}" || { echo 'IPA export produced no file'; exit 1; }
