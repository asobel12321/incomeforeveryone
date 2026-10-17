# AI Jobs Brief operations

## Current configuration

- Delivery: Wednesdays at 1 PM America/New_York through the active Brevo `AI Jobs Brief RSS` integration.
- Content: newest full daily article from the feed window, not a multi-article weekly digest. Repeatable block limit is one; template uses `{{ item.CONTENT_ENCODED | safe }}`.
- Feed: `/ai-jobs-brief.xml`, newest 30 dated daily articles. Drafts and special-issue filenames are excluded.
- Audience: dedicated `AI Jobs Brief` list. The hosted form requires consent and adds subscribers without confirmation email, as requested by the owner. The site collects no addresses.
- Sender: verified `newsletter@incomeforeveryone.org`; authenticated domain. Subject: `AI Jobs Brief | Weekly AI and Labor Update`.
- Footer: Income for Everyone, 100 Broad St, New York, NY 10004, with provider unsubscribe link.

This configuration was verified October 3, 2026. An owner signup and controlled template delivery succeeded. The RSS preview showed full article content and source links; the standalone template test did not populate RSS. The first scheduled subscriber campaign is October 7 if new feed items exist. Its end-to-end content and unsubscribe behavior remain to be checked.

## Maintenance

October 17 audit: production returned HTTP 200 but the feed failed XML parsing because an October 8 summary contained HTML-only named entities (`&ldquo;`, `&lsquo;`). The repair decodes HTML entities and escapes XML text, and safely splits embedded CDATA terminators. Generated-interface validation and deployed publication health now parse this feed; the latter also requires a fresh full article with source links. This failure does not establish whether Brevo accepted or delivered the October 7/14 campaigns; inspect provider records separately.

Check the first real campaign for full content, correct sender/subject, source and article links, mobile layout, and working unsubscribe. Do not send tests or change recipients without appropriate user authorization. Do not reactivate the superseded daily schedule.

The setup used Brevo Free's 300-send/day allowance; recheck the account limit before audience growth exceeds it. Sender, schedule, list, and template live in Brevo, not the repository. The signup link is `params.newsletterSignupURL` in `config.toml`.

For a local unsent review edition:

```powershell
python scripts/prepare_newsletter.py --date YYYY-MM-DD --output-dir newsletter-preview
```

This tool sends nothing. It accepts published daily articles with the expected three-story structure.

## Delivery audit — October 17, 2026

Brevo campaign #6 was sent October 7 at 13:03 America/New_York: 2 delivered (100%), 1 reported open. The owner inbox contains the rendered full October 7 article, three source links, sender newsletter@incomeforeveryone.org, and resolved provider unsubscribe/mirror links; SPF, DKIM, and DMARC passed. No unsubscribe was executed. Campaign-list records and the owner inbox show no October 14 campaign.

The AI Jobs Brief RSS integration remains Active with the correct feed URL and Wednesday 13:00 schedule. The malformed feed was present after October 8, but no provider error record has established why October 14 was skipped. The feed repair is deployed. Verify the next scheduled campaign before declaring weekly delivery fully recovered; do not resend missed editions or change recipients to clear the gap.
