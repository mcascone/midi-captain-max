# GitHub Secrets Setup for Code Signing

This document describes the GitHub secrets required for automatic code signing and notarization of the Config Editor app in CI/CD.

## Required Secrets

These secrets are **already configured** in the repository:

| Secret Name | Description | Current Status |
|-------------|-------------|----------------|
| `MACOS_APPLICATION_CERT` | Base64-encoded Developer ID Application .p12 | ✅ Configured |
| `MACOS_APPLICATION_CERT_PWD` | Password for the .p12 file | ✅ Configured |
| `APPLE_ID` | Apple ID email for notarization | ✅ Configured |
| `APPLE_APP_PASSWORD` | App-specific password for notarization | ✅ Configured |
| `APPLE_TEAM_ID` | Team ID for notarization | ✅ Configured |

**Note:** The workflow gracefully handles missing secrets - if not configured, the app is built unsigned with a warning in the build summary. Users will see the right-click-to-open Gatekeeper warning.

---

## Step 1: Export Certificate as Base64

1. Open **Keychain Access** on Mac
2. Find certificate: `Developer ID Application: Maximilian Cascone (9WNXKEF4SM)`
3. Right-click → **Export** → Save as `.p12` with a password
4. Convert to base64:
   ```bash
   base64 -i certificate.p12 | pbcopy
   ```
5. Paste into GitHub secret `APPLE_CERTIFICATE`
6. Save the password as `APPLE_CERTIFICATE_PASSWORD`

---

## Step 2: Create App-Specific Password

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in with your Apple ID
3. Navigate to **Security → App-Specific Passwords**
4. Click **+** to generate a new password
5. Label it "GitHub Actions - MIDI Captain"
6. Copy the password and save it as `APPLE_PASSWORD` secret

---

## Step 3: Add Secrets to GitHub

1. Go to repository settings: https://github.com/MC-Music-Workshop/midi-captain-max/settings/secrets/actions
2. Click **New repository secret**
3. Add each secret from the table above
4. Save

---

## Verification

After adding secrets, the next CI run will:
1. ✅ Import the certificate and sign the app
2. ✅ Notarize the DMG with Apple
3. ✅ Staple the notarization ticket
4. ✅ Upload a signed, notarized DMG

**Users will NOT see Gatekeeper warnings** when opening the app.

---

## Troubleshooting

### "No signing identity found"
- Verify `APPLE_CERTIFICATE` is base64-encoded correctly
- Check that certificate is for "Developer ID Application" (not Installer)
- Ensure certificate hasn't expired

### "Notarization failed"
- Verify `APPLE_ID` and `APPLE_PASSWORD` are correct
- Check that app-specific password hasn't been revoked
- Review notarization logs in GitHub Actions output

### "Invalid signing identity in tauri.conf.json"
- Ensure the identity string matches exactly:
  ```
  Developer ID Application: Maximilian Cascone (9WNXKEF4SM)
  ```

---

## Conditional Signing

The CI workflow supports **conditional signing**:
- If secrets are configured → App is signed and notarized
- If secrets are missing → App is built unsigned (users see Gatekeeper warning)

This allows the workflow to run on forks without access to certificates.
