---
name: unbroker-onboarding
description: Complete onboarding workflow for Unbroker privacy tool — subject intake, Phase 1 scan, Phase 2 opt-out execution, human task handoff, and weekly cron setup. Use when setting up a new subject for autonomous data broker removal.
trigger_conditions:
  - "unbroker onboarding"
  - "privacy tool setup"
  - "data broker removal"
  - "subject intake"
  - "broker scan"
  - "opt-out execution"
  - "human task handoff"
  - "weekly cron setup"
  - "autonomous removal"
  - "subject details"
  - "browserbase API key"
  - "agentmail configured"
version: 1.1.0
metadata:
  hermes:
    tags: [unbroker, privacy, data-brokers, onboarding, automation]
---

# Unbroker Onboarding Workflow

Complete workflow for setting up a new subject in Unbroker and achieving full autonomy.

## When to Use

- You need to **onboard a new subject** → use for intake and scanning
- You're setting up **privacy protection** → use for broker removal
- You want **autonomous data broker removal** → use for full workflow
- You're starting with **subject details** → use for intake processing
- You need **browserbase integration** → use for stealth sessions
- You have **AgentMail configured** → use for email opt-outs

## Not For

- **Single broker removal** → use direct `unbroker` commands instead
- **Manual opt-out processes** → use browser automation directly instead
- **General privacy advice** → use a privacy consultant instead
- **Legal compliance checks** → use a legal professional instead
- **Real-time monitoring of broker sites** → use specialized monitoring tools instead
- **Data breach response** → use incident response protocols instead

## Prerequisites

- Unbroker skill installed: `skill_view(name='unbroker')`
- AgentMail configured (for sending opt-out emails)
- Browserbase API key in `/home/wahid/.hermes/.env` (for stealth browser sessions)
- Subject details: full name, known locations, emails, phones, prior addresses

## Phase 1: Subject Intake & Scan

1. **Create subject:**
   ```bash
   cd /home/wahid/.hermes/skills/security/unbroker
   python3 scripts/pdd.py intake --name "First Last" --location "City, State" --email "email@example.com" --phone "555-555-5555" --prior-location "Previous City, State"
   ```

2. **Scan all brokers:**
   ```bash
   python3 scripts/pdd.py plan <subject_id> --batch
   ```
   This dispatches parallel subagents to scan all 51 brokers.

3. **Wait for completion** (typically 2-5 minutes for full scan).

4. **Review results:**
   ```bash
   python3 scripts/pdd.py status <subject_id>
   ```

## Phase 2: Opt-Out Execution

### Email-Based Opt-Outs (Highest Priority)

For brokers with documented deletion emails:

```bash
# Render the email draft
python3 scripts/pdd.py render-email <subject_id> <broker_id> --listing "<profile_url>"

# Send via AgentMail
export AGENTMAIL_API_KEY=$(grep '^AGENTMAIL_API_KEY=' /home/wahid/.hermes/.env | cut -d= -f2-)
python3 << 'EOF'
import os
from agentmail import AgentMail

client = AgentMail(api_key=os.environ["AGENTMAIL_API_KEY"])
result = client.inboxes.messages.send(
    inbox_id="jarvis4wahid@agentmail.to",  # or your AgentMail inbox
    to="<broker_email>",
    subject="Data Removal Request - <Subject Name>",
    text="<email_body>",
    labels=["unbroker", "<broker_id>", "deletion"]
)
print(f"Sent: {result}")
EOF

# Record submission
python3 scripts/pdd.py record <subject_id> <broker_id> submitted --found true --evidence '{"listing_urls":["<url>"]}' --disclosed contact_email,full_name,listing_urls --channel email
```

### Web Form Opt-Outs via Browserbase

For brokers requiring web forms:

```bash
export PATH="/home/wahid/.npm-global/bin:$PATH"
export BROWSERBASE_API_KEY=$(grep '^BROWSERBASE_API_KEY=' /home/wahid/.hermes/.env | cut -d= -f2-)

# Create stealth browser session
browse open "<optout_url>" --timeout 45

# Fill form fields
browse fill "@<ref>" "<value>"

# Handle CAPTCHAs
# - Soft CAPTCHAs (checkbox): browse click "@<ref>"
# - Hard CAPTCHAs (image challenges): Record as blocked, present to human

# Submit form
browse click "@<submit_button_ref>"

# Record submission
python3 scripts/pdd.py record <subject_id> <broker_id> submitted --found true --evidence '{"listing_urls":["<url>"]}' --disclosed contact_email,full_name --channel web_form
```

## Phase 3: Human Task Handoff

After Phase 2, present the human digest:

```bash
python3 scripts/pdd.py next <subject_id>
```

This returns:
- `human_digest`: List of brokers requiring human intervention (phone calls, gov ID uploads, email verification clicks)
- `actions`: Recommended next steps

**Present this ONCE at the end of the run, not per item.**

## Phase 4: Weekly Cron Setup

Set up automated weekly rechecks:

```bash
cronjob action='create' \
  name='unbroker-weekly-recheck' \
  schedule='0 9 * * 1' \
  prompt='Run the unbroker weekly recheck for subject <subject_id> (<subject_name>).

Steps:
1. Load the unbroker skill: skill_view(name="unbroker")
2. cd /home/wahid/.hermes/skills/security/unbroker
3. Run: python3 scripts/pdd.py due <subject_id>
4. For each broker that is due or still blocked, attempt a stealth browser rescan using Browserbase (export BROWSERBASE_API_KEY from /home/wahid/.hermes/.env)
5. Record findings with: python3 scripts/pdd.py record <subject_id> <broker_id> <new_state>
6. Run: python3 scripts/pdd.py status <subject_id>
7. If any new listings are found, attempt opt-out via web form or email
8. Report: summary of changes, new findings, and any human tasks required

Use local Ollama model qwen2.5:7b for this task. Be thorough but efficient — focus on brokers that were previously blocked and may now be accessible.' \
  model='{"model": "qwen2.5:7b", "provider": "ollama"}' \
  deliver='telegram' \
  enabled_toolsets='["terminal", "web", "file"]'

# Attach the unbroker skill to the cron job
cronjob action='update' job_id='<job_id>' skills='["unbroker"]'
```

## Pitfalls

1. **Missing Browserbase API key** — The stealth browser sessions require a Browserbase API key in `/home/wahid/.hermes/.env`. Recovery action: Add the key to the environment file and export it in the script.

2. **AgentMail not configured** — Email-based opt-outs require AgentMail setup. Recovery action: Run the AgentMail setup flow before attempting email removals.

3. **Missing subject details** — The intake process requires complete information. Recovery action: Collect full name, locations, emails, phones, and prior addresses before starting.

4. **Not waiting for scan completion** — The broker scan takes 2-5 minutes. Recovery action: Always wait for the `python3 scripts/pdd.py status <subject_id>` command to return complete results.

5. **Attempting to solve image CAPTCHAs** — This violates the skill's rules and will fail. Recovery action: Record as blocked and present to human for resolution.

6. **Not re-scanning before submitting** — Cannot transition from `blocked` directly to `submitted`. Recovery action: Re-scan the broker and confirm it's accessible before submitting.

7. **Forgetting parent-child relationships** — Some brokers clear others (e.g., BeenVerified clears PeopleLooker). Recovery action: Re-scan child brokers after removing a parent before submitting separately.

8. **Using expensive models in cron jobs** — The `manifest.build` auto-routing can lead to costly calls. Recovery action: Pin `qwen2.5:7b` with `provider: ollama` in cron job configuration.

9. **Not clicking verification emails** — The human must manually click verification links sent by brokers. Recovery action: After the human clicks, run `python3 scripts/pdd.py record <subject_id> <broker_id> awaiting_processing`.

10. **Skipping the human digest presentation** — All human tasks should be presented at once. Recovery action: Run `python3 scripts/pdd.py next <subject_id>` once at the end to get the complete digest.

11. **Not setting up the weekly cron job** — Automated rechecks are essential for ongoing protection. Recovery action: Create the cron job with the specified schedule `0 9 * * 1` using the `cronjob` command.

12. **Attaching unbroker skill to cron job** — The cron job needs access to the unbroker functionality. Recovery action: Run `cronjob action='update' job_id='<job_id>' skills='["unbroker"]'` after creation.

## Success Criteria

- All 51 brokers scanned (100% coverage)
- Email-based opt-outs sent to all brokers with documented deletion emails
- Web-form opt-outs attempted for all T0/T1 brokers
- Human digest presented with clear action items
- Weekly cron job scheduled and verified
- Subject status shows `fully_done: false` but `done_for_now: true`

## Example: Radaris Opt-Out

```bash
# 1. Verify listing
web_extract urls='["https://www.radaris.com/p/First/Last/"]'

# 2. Render email draft
python3 scripts/pdd.py render-email <subject_id> radaris --listing "https://www.radaris.com/p/First/Last/"

# 3. Send email (no "View Profile" link for subject → email fallback)
export AGENTMAIL_API_KEY=$(grep '^AGENTMAIL_API_KEY=' /home/wahid/.hermes/.env | cut -d= -f2-)
# ... send via AgentMail ...

# 4. Record submission
python3 scripts/pdd.py record <subject_id> radaris submitted --found true --evidence '{"listing_urls":["https://www.radaris.com/p/First/Last/"]}' --disclosed contact_email,full_name,listing_urls --channel email --reason "No View Profile link for subject; emailed customer-service@radaris.com for removal"

# 5. Human clicks verification email, then:
python3 scripts/pdd.py record <subject_id> radaris awaiting_processing
```

## Related Skills

- `unbroker` — Core privacy tool with broker database and opt-out methods
- `agentmail` — Email sending via AgentMail API
- `cron-model-optimization` — Prevent expensive model routing for cron jobs
