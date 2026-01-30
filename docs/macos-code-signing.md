# macOS Code Signing Guide

This document describes how to obtain an Apple Developer certificate and sign the MIDI Captain installer package.

> **Status:** Not yet implemented (Issue #3)  
> **Impact:** Without signing, macOS shows "unidentified developer" warning on first install.

---

## Why Sign?

macOS Gatekeeper blocks unsigned apps by default. Users must right-click → Open to bypass. A signed package:
- Opens without warnings
- Shows your developer identity
- Can be notarized for additional trust

---

## Requirements

1. **Apple Developer Account** — $99/year at [developer.apple.com](https://developer.apple.com)
2. **Developer ID Installer Certificate** — For signing `.pkg` files
3. **Keychain Access** — To store the certificate locally
4. **Notarization** (optional) — For full Gatekeeper approval

---

## Step 1: Enroll in Apple Developer Program

1. Go to [developer.apple.com/programs/enroll](https://developer.apple.com/programs/enroll)
2. Sign in with your Apple ID
3. Complete enrollment ($99/year for individuals)
4. Wait for approval (usually instant for individuals)

---

## Step 2: Create Developer ID Installer Certificate

1. Open **Keychain Access** on your Mac
2. Go to **Keychain Access → Certificate Assistant → Request a Certificate From a Certificate Authority**
3. Fill in:
   - Email: Your Apple ID email
   - Common Name: Your name
   - CA Email: Leave blank
   - Request is: Saved to disk
4. Save the `.certSigningRequest` file

5. Go to [developer.apple.com/account/resources/certificates](https://developer.apple.com/account/resources/certificates)
6. Click **+** to create a new certificate
7. Select **Developer ID Installer** (for signing `.pkg` files)
8. Upload your `.certSigningRequest` file
9. Download the certificate (`.cer` file)
10. Double-click to install in Keychain

---

## Step 3: Verify Certificate Installation

```bash
# List available signing identities
security find-identity -v -p basic

# Look for "Developer ID Installer: Your Name (TEAMID)"
```

---

## Step 4: Update Build Script

Modify `tools/build-installer.sh` to sign the package:

```bash
# After productbuild, sign the package
productsign --sign "Developer ID Installer: Your Name (TEAMID)" \
    "$OUTPUT_DIR/${PKG_NAME}.pkg" \
    "$OUTPUT_DIR/${PKG_NAME}-signed.pkg"

# Replace unsigned with signed
mv "$OUTPUT_DIR/${PKG_NAME}-signed.pkg" "$OUTPUT_DIR/${PKG_NAME}.pkg"
```

**Note:** The build script already includes conditional signing that checks for certificate availability.

---

## Step 5: Notarization (Optional but Recommended)

Notarization adds an extra layer of trust. Apple scans your package and staples a ticket.

```bash
# Submit for notarization
xcrun notarytool submit "${PKG_NAME}.pkg" \
    --apple-id "your@email.com" \
    --password "app-specific-password" \
    --team-id "TEAMID" \
    --wait

# Staple the ticket to the package
xcrun stapler staple "${PKG_NAME}.pkg"
```

### App-Specific Password

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign In → Security → App-Specific Passwords
3. Generate a password for "notarytool"
4. Store securely (use Keychain or CI secrets)

---

## CI/CD Integration

For GitHub Actions, store credentials as secrets:

| Secret | Value |
|--------|-------|
| `APPLE_DEVELOPER_ID` | Your Apple ID email |
| `APPLE_APP_PASSWORD` | App-specific password |
| `APPLE_TEAM_ID` | Your 10-character Team ID |
| `MACOS_CERTIFICATE` | Base64-encoded .p12 certificate |
| `MACOS_CERTIFICATE_PWD` | Password for .p12 file |

### Export Certificate for CI

```bash
# Export from Keychain as .p12
security export -k login.keychain -t identities -f pkcs12 -o cert.p12 -P "password"

# Encode for GitHub secret
base64 -i cert.p12 | pbcopy
```

### GitHub Actions Workflow Addition

```yaml
- name: Import Certificate
  env:
    MACOS_CERTIFICATE: ${{ secrets.MACOS_CERTIFICATE }}
    MACOS_CERTIFICATE_PWD: ${{ secrets.MACOS_CERTIFICATE_PWD }}
  run: |
    echo $MACOS_CERTIFICATE | base64 --decode > cert.p12
    security create-keychain -p "" build.keychain
    security import cert.p12 -k build.keychain -P $MACOS_CERTIFICATE_PWD -T /usr/bin/productsign
    security list-keychains -s build.keychain
    security unlock-keychain -p "" build.keychain
    security set-key-partition-list -S apple-tool:,apple: -s -k "" build.keychain

- name: Sign Package
  run: |
    productsign --sign "Developer ID Installer: Your Name (${{ secrets.APPLE_TEAM_ID }})" \
      input.pkg output.pkg

- name: Notarize
  run: |
    xcrun notarytool submit output.pkg \
      --apple-id "${{ secrets.APPLE_DEVELOPER_ID }}" \
      --password "${{ secrets.APPLE_APP_PASSWORD }}" \
      --team-id "${{ secrets.APPLE_TEAM_ID }}" \
      --wait
    xcrun stapler staple output.pkg
```

---

## Costs

| Item | Cost |
|------|------|
| Apple Developer Program | $99/year |
| Certificate | Included |
| Notarization | Free |

---

## References

- [Apple Developer Program](https://developer.apple.com/programs/)
- [Creating Developer ID Certificates](https://developer.apple.com/help/account/create-certificates/create-developer-id-certificates)
- [Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [GitHub Actions: Signing macOS Apps](https://docs.github.com/en/actions/deployment/deploying-xcode-applications/installing-an-apple-certificate-on-macos-runners-for-xcode-development)

---

*Last updated: January 30, 2026*
