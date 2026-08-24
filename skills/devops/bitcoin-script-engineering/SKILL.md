---
name: bitcoin-script-engineering
description: Bitcoin P2WSH/P2TR lockbox scripts for sendbitcoin.gift.
version: 1.1.0
metadata:
  hermes:
    tags: [bitcoin, taproot, p2tr, p2wsh, cltv, script, miniscript]
    trigger_conditions:
      - "build taproot output"
      - "bitcoin script construction"
      - "CLTV refund leaf"
      - "deriveaddresses validation"
      - "witness assembly"
      - "taproot lockbox"
---

# Bitcoin Script Engineering (sendbitcoin.gift)

Patterns used in v1 P2WSH (IF/ELSE/CLTV), legacy v2 P2WSH (same but code v2), and **v3 P2TR** (claim key-path, refund script-path) lockbox engines. Source of truth: `/home/wahid/timelock-gift/src/lockbox.js` (v1/v2 P2WSH) and `src/taproot.js` (v3 P2TR).

## When to Use

- Building or editing the timelock-gift lockbox engines: v1/v2 P2WSH (`src/lockbox.js`) or v3 P2TR (`src/taproot.js`)
- Generating taproot (tb1p) or P2WSH (tb1q) addresses from descriptors
- Signing a claim (key-path Schnorr) or refund (script-path) transaction
- Debugging witness serialization, CLTV leaf construction, or descriptor parse errors
- Validating a descriptor with `deriveaddresses` before locking funds
- Sweeping legacy v1/v2 codes when upgrading to the P2TR engine

## Not For

- Deploying or updating the bitcoin-fits.onrender.com calculator site → use `bitcoin-fits-site` instead
- Building or troubleshooting the StartOS Blockclock Adapter s9pk → use `blockclock-adapter-packaging` instead
- Updating the Lightning wallets comparison site → use `update-lightning-wallets-site` instead
- Designing the Bitcoin business-card artwork → use `bitcoin-business-card` instead

## v1/v2 P2WSH (tb1q, code v1/v2)

Script: `OP_IF <claim> CHECKSIG OP_ELSE <height> CLTV DROP <refund> CHECKSIG OP_ENDIF`

Witness:
- **Claim**: `[sig, <1>, witnessScript]` — selector byte `0x01` for IF branch
- **Refund**: `[sig, <empty>, witnessScript]` — empty item for ELSE, needs nLockTime

### Bitcoinjs auto-finalizer trap

CLTV script is classified 'nonstandard' — `finalizeAllInputs()` rejects. Pass an **explicit finalizer** that builds `finalScriptWitness` as a single compact-size-serialized buffer: compactSize(itemCount) then for each item: compactSize(itemLen) + itemBytes.

### Compact-size vs ScriptNum trap

`bitcoin.script.number.encode(0)` returns **empty bytes** — corrupts witnesses with empty items (OP_IF refund selector). Never use it for witness serialization. Write a real `compactSize(n)` function.

## v3 P2TR (tb1p, code v3 — NOT v2)

**This is the current P2TR encoding.** Never label P2TR as `v: 2` — that was the P2WSH+IF/ELSE code set. New locks use `addrType: "p2tr"`, `v: 3`, `tb1p`/`bc1p` addresses. `v: 1`/`v: 2` P2WSH codes are legacy and swept by the old spender (branch on `addrType` or address prefix, not `v` alone).

Layout: **key path = claim** (internal key), **one leaf = CLTV+VERIFY + refund**.

| Path | Witness |
|------|---------|
| Key path (claim) | `<64-byte Schnorr sig>` (SIGHASH_DEFAULT, no sig byte) |
| Script path (refund) | `<refund sig> <leaf_script> <control_block>` |

### Leaf: CLTV+VERIFY, not CLTV+DROP

Core's `and_v(v:after(H), pk(K))` compiles to **CLTV VERIFY** (`0x69`), not **CLTV DROP** (`0x75`). One-byte difference — different tapleaf → different address.

Leaf hex skeleton (height `149854`): `03 5e4902  b1 69  20 <32-byte refund x-only>  ac`

### Tweak derivation (BIP341)

```
tweak = TaggedHash("TapTweak", P ‖ merkle_root)
Q = lift_x(P) + tweak·G
```

Parity via `ecc.xOnlyPointAddTweak(internalKey, tweak)` → `{parity, xOnlyPubkey}`. Do NOT use `payments.p2tr.parity` — bitcoinjs v6 doesn't expose it.

### Claim signing

1. Compressed pub `03…` prefix = odd Y → `d_adj = ecc.privateNegate(d)`
2. `d_tweak = ecc.privateAdd(d_adj, tweak)`
3. `ecc.signSchnorr(sighash, d_tweak)` → 64 bytes (SIGHASH_DEFAULT)

### Descriptor format

Correct (no braces, Core accepts): `tr(key,and_v(v:after(H),pk(refund)))`

Wrong (`{braces}` cause Core parse error). `deriveaddresses` needs checksum suffix from `getdescriptorinfo`.

## Positional byte checks (never substring-scan)

Pubkey and height bytes may contain opcode values. NEVER substring-scan for `63`/`64`/`67`/`b175` — assert at exact structural offsets.

## Bitcoin Core RPC (StartOS)

Host `192.168.100.31:62642`, user `jarvis`, pass in `~/.hermes/.env` as `BITCOIN_RPC_PASSWORD`. Cookie auth: `ssh start9@192.168.100.31 'sudo cat /media/startos/data/package-data/volumes/bitcoind/data/main/.cookie'`. Chain = main.

## Pitfalls

1. **CLTV finalizer rejected by bitcoinjs** — Always write an explicit finalizer for nonstandard scripts. `finalizeAllInputs()` only knows pubkey/multisig shapes.
2. **Witness serialization with ScriptNum(0)** — Returns empty bytes. Use real compact-size encoder.
3. **CLTV+DROP vs CLTV+VERIFY** — Core miniscript uses VERIFY (`0x69`). Using DROP (`0x75`) produces different tapleaf → wrong address.
4. **x-only key length** — P2TR refund push must be `0x20` (32 bytes), not `0x21` (33 bytes like P2WSH).
5. **Descriptor braces** — `tr(key,{script})` is WRONG. No braces: `tr(key,script)`.
6. **bitcoinjs p2tr.parity is undefined** — Use `ecc.xOnlyPointAddTweak` instead.
7. **Deriveaddresses needs checksum** — Run `getdescriptorinfo` first, pass the checksum-suffixed descriptor.
8. **Opcode values inside pubkey/height bytes** — Byte sequences can contain opcode bytes like `0x63`/`0x64`/`0x67`/`0xb1`/`0x75`. Never substring-scan the script for markers; assert at exact structural offsets (see Positional byte checks section).
9. **Wrong network RPC** — `deriveaddresses` on mainnet vs testnet4 returns different addresses. The StartOS bitcoind is mainnet; when testing lockboxes use the testnet4 node and confirm `-chain` before deriving (see `references/testnet4-test-matrix.md`).
10. **Schnorr sig length** — key-path claim needs a 64-byte signature (SIGHASH_DEFAULT, no trailing sighash byte). Appending a sighash byte (P2WSH habit) invalidates the taproot spend.