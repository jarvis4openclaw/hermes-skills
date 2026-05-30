# Lightning Donate Button Pattern

Floating donate button (bottom-right FAB) that opens a modal with a Lightning Network QR code. Matches a dark-themed site's design system. Supports both BOLT11 (one-shot invoices) and BOLT12 (reusable offers).

## Which Standard to Use

| Standard | Reusable | Adoption | Best For |
|----------|----------|----------|----------|
| BOLT11 | ❌ One-shot, expires | Universal | Temp invoices, demos |
| BOLT12 offers | ✅ Lives forever | Growing (CLN, LDK, Phoenix, Zeus) | Static donate buttons |
| LNURL-pay | ✅ Yes | Near-universal | Also good for static |

**Recommendation:** For a static donate button on a website, use BOLT12 offers. They're reusable — you generate one QR code and it works forever. No expiry, no one-shot problems. BOLT11 breaks as soon as one person pays (or the invoice expires).

If BOLT12 isn't available, LNURL-pay is the fallback. BOLT11 should only be used for temporary/demo purposes.

## Implementation

### HTML (add before `</body>`)

For BOLT12 offers, include the lightning address display between the QR and the copy section:

```html
<!-- Donate Floating Button -->
<button id="donate-btn" class="donate-fab" aria-label="Donate">
  <span class="donate-icon">⚡</span>
  <span class="donate-text">Donate</span>
</button>

<!-- Donate Modal -->
<div id="donate-modal" class="donate-modal-overlay">
  <div class="donate-modal">
    <button class="donate-modal-close" aria-label="Close">&times;</button>
    <div class="donate-modal-header">
      <span class="donate-modal-icon">⚡</span>
      <h3>Support This Project</h3>
      <p>Scan to send Bitcoin via Lightning Network</p>
    </div>
    <div class="donate-modal-qr">
      <img src="donate-qr.png" alt="Lightning Offer QR Code">
      <div class="donate-qr-glow"></div>
    </div>
    <div class="donate-modal-address">
      <span class="donate-address-label">⚡</span>
      <code>pay@example.com</code>
    </div>
    <div class="donate-modal-invoice">
      <input type="text" id="donate-invoice" value="<BOLT12_OFFER>" readonly>
      <button id="donate-copy" class="donate-copy-btn">Copy Offer</button>
    </div>
    <p class="donate-modal-note">Thank you for your support! ⚡</p>
  </div>
</div>
```

Note the differences from BOLT11:
- `.donate-modal-address` section displays the user's lightning address
- Button text is "Copy Offer" not "Copy Invoice"
- QR `alt` is "Lightning Offer QR Code" not "Invoice"

### CSS for Lightning Address Display

```css
.donate-modal-address {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding: 0.55rem 1rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.donate-modal-address .donate-address-label {
  font-size: 1.1rem;
}

.donate-modal-address code {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  color: var(--accent);
  font-weight: 600;
}
```

### JS

See the full implementation in the app.js from the lightning-wallets-comparison project for:
- Modal open/close logic
- Escape key handler
- Overlay click-to-close
- Copy-to-clipboard with visual feedback
- Button text reverts to "Copy Offer" (not "Copy Invoice") after 2s

### Generating the QR Code

**For BOLT12 offers** (reusable):

```bash
pip3 install --break-system-packages qrcode[pil]

python3 -c "
import qrcode
qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data('<BOLT12_OFFER_STRING>')
qr.make(fit=True)
img = qr.make_image(fill_color='white', back_color='#121216').convert('RGBA')
img.save('donate-qr.png')
"
```

**For BOLT11 invoices** (one-shot, temporary):

```bash
python3 -c "
import qrcode
qr = qrcode.QRCode(version=7, box_size=5, border=2)
qr.add_data('<BOLT11_INVOICE>')
qr.make(fit=True)
img = qr.make_image(fill_color='#f7931a', back_color='#0a0a0f')
img.save('donate-qr.png')
"
```

**BOLT12 QR settings:**
- `fill_color='white'` — white QR on dark modal background
- `back_color='#121216'` — matches modal card background
- `error_correction=H` — high error correction for readability
- No fixed `version` — let it auto-scale for the long offer string
- BOLT12 offers typically ~100 chars (much shorter than BOLT11)

**BOLT11 QR settings:**
- `fill_color='#f7931a'` — Bitcoin orange on dark
- `version=7` — BOLT11 invoices are long (~400+ chars)
- Higher version needed to fit the data

## DNS TXT Record for BOLT12

You can point a lightning address to a BOLT12 offer via DNS:

```
Name:  _bolt12._domainkey
Type:  TXT
Value: lno1...
```

Wallets that support this will resolve the offer automatically from the domain.

**Diagnostic:** Not all lightning addresses use `.well-known/lnurlp` — some (like `pay@wahid.my`) use DNS TXT records for BOLT12. If `GET /.well-known/lnurlp/pay` returns empty, check DNS TXT:
```bash
dig TXT _bolt12._domainkey.<domain> +short
# or
dig TXT <domain> +short | grep lno
```

## Pitfalls

- **BOLT11 is one-shot.** If your site is static (no dynamic invoice generation), use BOLT12 or LNURL-pay. A BOLT11 QR embedded in static HTML breaks after the first payment.
- **BOLT11 invoices are long** (~400 chars). QR `version` must be high enough (7+) or the data won't fit.
- **BOLT12 offers are shorter** (~100 chars) but QR still needs error correction H for dark backgrounds.
- **QR color must contrast with the modal background.** For dark modal cards, use white QR on matching dark background. Test on both pages.dev and custom domain.
- **Cloudflare Pages CDN caches static assets.** After updating the QR image, use the hash deploy URL (`<hash>.<project>.pages.dev`) to verify, as custom domains may serve stale cached files.
