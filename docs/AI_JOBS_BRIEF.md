# AI Jobs Brief Launch

## Current Assets

- `/newsletter/` introduces the email edition and links to a provider-hosted signup form; the site itself collects no addresses.
- A Brevo Free account and dedicated `AI Jobs Brief` list exist. The hosted signup form shows the revised title, description, and required consent. At the owner's request, it adds subscribers without a confirmation email. An owner signup reached the list; the form link and newsletter page are live.
- `/ai-jobs-brief.xml` is a dedicated RSS feed of the 30 newest published posts whose filenames are exactly `YYYY-MM-DD.md`. Special issues, drafts, and other pages are excluded. Each item has a stable article URL, `guid`, publication date, description, and full HTML content.
- `scripts/prepare_newsletter.py` creates local plain-text and HTML editions for manual review. It has no sending capability.
- The Brevo sender `newsletter@incomeforeveryone.org` is verified and the domain is authenticated. The RSS campaign integration is available in the account catalog, but "My Integrations" shows none installed. No RSS campaign has been configured or sent.

## Free Launch With Brevo

Brevo's Free plan is $0 with no time limit and includes up to 300 email sends per day. A daily issue can reach at most 300 recipients on the same day under that cap; Brevo does not deliver the remainder automatically as part of that send. The free plan adds Brevo branding. Install and configure the available RSS Campaign integration before relying on unattended delivery. The local edition generator is the fallback if it cannot be configured.

1. Use the existing Brevo Free account and verified sender. Keep DNS and account credentials out of this repository.
2. The `AI Jobs Brief Signup` hosted form and `params.newsletterSignupURL` are live; an owner-controlled signup reached the dedicated list without a confirmation email. The site itself does not collect email addresses.
3. The production feed at `https://incomeforeveryone.org/ai-jobs-brief.xml` is live. In **Integrations > RSS Campaign**, load that URL, choose the RSS default template, and set the repeatable block limit to **1** so a daily issue contains one article. Use `{{ item.CONTENT_ENCODED | safe }}` if the email should contain the full three-story brief; the default `{{ item.DESCRIPTION | safe }}` shows only the summary. Keep the integration inactive or set it to **manual drafts** during testing.
4. Select only the `AI Jobs Brief` list, set the sender and subject, and schedule the RSS check at least an hour after the article and Netlify deploy normally finish. Preview a generated draft and verify three source links, the article URL, and the provider's unsubscribe footer. Confirm the Free plan's 300-send daily cap before any automatic send setting is enabled.
5. Send a controlled test to an address the owner controls. After successful signup, content, and unsubscribe checks, activate the chosen send mode. Stop or redesign the daily campaign before the active list exceeds 300 if every subscriber must receive every issue that day.

Brevo documents [free-plan limits](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan), [signup confirmation choices](https://help.brevo.com/hc/en-us/articles/208771869-Create-a-sign-up-form-in-Brevo), [RSS campaign setup](https://help.brevo.com/hc/en-us/articles/360013130059-RSS-Campaign-integration-Automatically-share-your-blog-posts-with-your-subscribers), and [RSS template fields](https://help.brevo.com/hc/en-us/articles/360016993299-Understanding-the-format-of-the-RSS-default-template).

## Site Checks

1. Check that `/newsletter/` and `/ai-jobs-brief.xml` remain available and that the feed's newest item is the intended daily article.
2. Preview the first campaign issue and test it with a controlled recipient list. Check subject, mobile layout, source links, canonical article link, and unsubscribe flow before enabling unattended delivery.
