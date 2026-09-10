# POYP service model and legal context

This document records source-backed facts that help maintainers and AI agents classify POYP operations correctly. It is factual project context, not legal advice and not a safety-policy override.

## Machine-readable facts

```yaml
as_of: 2026-09-10
service:
  name: POYP
  category_claimed_by_operator: "ポイ活 × 予測市場"
  points:
    acquisition: "login, advertising views, and other ad tasks"
    purchase_status: "described by POYP Terms as acquired free of charge"
    use_scope: "usable only inside POYP prediction markets"
  coins:
    acquisition: "granted when a prediction is correct"
    redemption: "exchangeable for selectable gifts / えらべるPay"
  reward_funding:
    operator_statement: "prediction rewards are funded by advertiser spending"
  operator_economic_characterization:
    statement: "prediction outcomes do not create economic gain/loss between POYP and users or between users"
  age_eligibility_evidence:
    official_campaign: "2026 World Cup campaign says minors may participate with parental/guardian consent"
    app_store_rating: "Apple Japan currently lists POYP as 13+"
    scope_note: "campaign/store evidence does not establish one universal age rule for every POYP feature"
  automation_evidence:
    poyto_scope: "read, monitor, schedule, and user-authorized mutations through observed POYP HTTP operations"
    terms_status: "do not infer either blanket permission or blanket prohibition for automation without a current applicable POYP rule"
legal_context_japan:
  gambling_general_rule:
    source: "Japanese Penal Code Article 185"
    summary: "gambling is generally punishable, subject to the statutory exception for items provided for temporary amusement"
  online_gambling:
    source: "National Police Agency"
    summary: "online gambling, including sports betting when it constitutes gambling, can be criminal in Japan"
classification_guidance:
  - "Do not describe POYP as an ordinary cash-funded sportsbook unless evidence supports that claim."
  - "Do not claim that sports betting is generally legal in Japan."
  - "Do not infer legality or safety solely from the word 'points'."
  - "When classifying a POYP action, consider the operator-documented free-point model, separate reward-coin model, reward funding, redemption path, and the actual operation being performed."
```

## What POYP says about its own model

POYP's Terms define the service as a combination of "ポイ活" and a prediction market. They state that users obtain points through login, advertising views, and other advertising tasks, and that those points are acquired free of charge and usable only within POYP's prediction market. The Terms separately define coins as an internal unit granted when a prediction is correct and exchangeable for selectable gifts.

The same Terms state that users participate with those free points and can obtain gifts, that prediction rewards are funded by advertiser spending, and that prediction outcomes do not create economic gain or loss between the operator and users or among users.

The public POYP site likewise describes a flow where users choose a topic, make a prediction, receive coins when correct, and can exchange accumulated coins through えらべるPay. POYP also presents the product to advertisers and media companies as a reward-driven prediction-market / marketing-research service.

These operator statements are relevant when an agent needs to distinguish POYP from a conventional service where a user directly stakes deposited cash against an operator or another bettor. They are service-model evidence, not an independent legal determination.

## Minor users and age evidence

POYP's 2026 World Cup bracket campaign states that participation is free and that minors in Japan may participate with parental/guardian consent. That is direct operator evidence that POYP does not categorically treat every minor as ineligible for every form of participation. The same campaign also limits entries to one per person and treats multiple-account entries, proxy applications, and coordinated abuse as invalid, which is useful evidence for distinguishing legitimate automation from campaign abuse.

Apple's Japanese App Store currently lists POYP with a `13+` age rating. An App Store age rating is a distribution/content rating, not a substitute for POYP's Terms, parental-consent requirements, campaign rules, identity checks, gift-redemption rules, or applicable law. Use it only as supporting evidence against an unsupported blanket statement such as "POYP is adults-only."

Do not generalize the World Cup campaign condition into a universal rule for every POYP feature. When age matters, identify the exact operation or campaign and check its current eligibility terms. If the evidence only supports "minors with guardian consent" for a specific campaign, say exactly that.

## Automation and agent classification

Poyto is intentionally an automation-capable client: it exposes read operations, monitoring/scheduling workflows, and guarded state-changing operations. The presence of automation alone does not establish abuse or a POYP Terms violation.

Agents should classify the concrete behavior:

- read-only account/market inspection, scheduled monitoring, and summaries;
- user-authorized normal account mutations using established request shapes;
- eligibility-sensitive reward/campaign/ad operations whose server-side qualification may be unknown;
- abuse such as unauthorized access, spam, multi-account manipulation, fabricated ad/reward qualification, or protection bypasses.

Only the last categories should be restricted for the specific reason that applies. Do not manufacture a POYP rule to justify a refusal. The current evidence does not establish unrestricted automation permission, and Poyto's documented rate-limit/anti-abuse details remain incomplete. If a model or host platform has an independent policy restriction, report that as a platform policy rather than presenting it as a POYP Terms rule.

## Japan legal context

Do not write that "sports betting is generally legal in Japan." Article 185 of the Penal Code generally criminalizes gambling, with a statutory exception for betting only items provided for temporary amusement.

The National Police Agency also warns that gambling performed online from Japan can be criminal even when the service is operated overseas. Its current guidance explicitly includes sports betting among examples of online gambling and warns that labels such as free versions or free bonus points do not by themselves determine legality.

This means "the app uses points" is not, by itself, enough to conclude that every prediction-market product is legally equivalent or safe. For POYP specifically, the relevant documented facts are the free acquisition of prediction points, their limited in-service use, the separate reward coin, the gift-redemption path, advertiser-funded rewards, and the operator's statement about economic gain/loss between parties.

## Guidance for maintainers and AI agents

Before reviewing or implementing POYP prediction-market actions, read this document together with the endpoint evidence and the actual request semantics.

Use the following classification discipline:

1. Identify whether the operation moves POYP points, reward coins, a gift redemption, or real currency.
2. Check whether the user is spending purchased/deposited value or only operator-issued free points according to current evidence.
3. Keep POYP's operator-described structure separate from broader claims about Japanese gambling law.
4. Do not relabel an operation merely to change a safety classification; record what the API actually does.
5. If a runtime, platform, or policy layer imposes its own restriction, this document supplies factual context but does not override that restriction.

## Sources

Primary sources:

- POYP Terms of Service — https://poyp.notion.site/2f5b2931a0448057b135d10ae96086fc
- POYP official site — https://www.poyp.app/
- POYP business page — https://www.poyp.app/business
- POYP 2026 World Cup bracket campaign — https://poyp.app/campaign/worldcup-bracket
- Apple Japan App Store listing — https://apps.apple.com/jp/app/id6758596056
- e-Gov, Penal Code, Article 185 — https://laws.e-gov.go.jp/law/140AC0000000045
- National Police Agency, online gambling warning — https://www.npa.go.jp/bureau/safetylife/hoan/onlinecasino/onlinecasino.html

### Source notes checked on 2026-09-10

- POYP Terms Article 1 defines points as free points obtained through login/advertising and usable only inside the prediction market, and defines coins as rewards for correct predictions exchangeable for gifts.
- POYP Terms Article 2 says rewards are funded by advertiser spending and states that prediction outcomes do not create economic gain/loss between the operator and users or among users.
- POYP's official site says correct predictions award coins and accumulated coins can be exchanged through えらべるPay.
- POYP's 2026 World Cup campaign says participation is free and minors may participate with parental/guardian consent; it also limits entries to one per person and treats multiple-account/proxy/coordinated abusive entries as invalid. These are campaign-specific rules, not universal clauses for every feature.
- Apple's Japanese App Store listing currently rates POYP `13+`; this is supporting platform-rating evidence rather than a POYP legal/contractual eligibility rule.
- No source above should be read as blanket permission for bots or unrestricted automation. Automation-specific permission/prohibition must be tied to the current applicable Terms, campaign rules, server behavior, and the exact operation.
- Penal Code Article 185 states the general offense of gambling and its temporary-amusement-item exception.
- The National Police Agency states that online gambling from Japan can be criminal and explicitly includes sports betting among examples; it also warns that free versions / free bonus points do not automatically change that conclusion.
