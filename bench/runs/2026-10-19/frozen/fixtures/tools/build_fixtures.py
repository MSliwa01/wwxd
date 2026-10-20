"""Build the wwxd-eval-v2 fixture JSON files from the data below.

Run from the fixtures directory: python3 -I tools/build_fixtures.py
Source paths, hashes, titles and dates come from source-inventory.json, so an
evidence entry only names the source id, segment timestamp, speaker and quote.
"""

import hashlib
import json
from pathlib import Path

import yaml

FX = Path(__file__).resolve().parent.parent
INV = {s["source_id"]: s for s in json.loads((FX / "source-inventory.json").read_text())["sources"]}
GOLD = {
    "hormozi": "/home/mateusz/Desktop/pyprograms/wwxd/bench/gold/hormozi-ask12.yaml",
    "yc": "/home/mateusz/Desktop/pyprograms/wwxd/bench/gold/yc-ask12.yaml",
}

# Default speaker attribution per source, with the basis for it. Transcripts
# carry no speaker labels, so anything beyond a solo talk is inferred.
SPEAKER = {
    "yt-JDR-R--4HhM": ("hormozi", "solo video on the Alex Hormozi channel"),
    "yt--j8_YCWZ05Q": ("hormozi", "solo video; he relays Skool platform data credited to Sam (Skool)"),
    "yt-jfW6gL6hKhk": ("hormozi", "solo video on the Alex Hormozi channel"),
    "yt--JLN1d1ZKUU": ("hormozi", "solo video on the Alex Hormozi channel"),
    "yt-uWdIgftpvBI": ("hormozi", "solo video on the Alex Hormozi channel"),
    "yt-rMJIOK_FgJk": ("hormozi", "solo video on the Alex Hormozi channel"),
    "yt-tGhe3sBuk34": ("hormozi", "vlog with team members; line inferred from content"),
    "yt-OQf2Ba-Lp_4": ("hormozi", "consulting episode with guest Corey; unlabeled >> turns, advisory line inferred from content"),
    "yt-MH-IMJxbUY4": ("hormozi", "consulting episode with guest Joel; unlabeled >> turns, advisory line inferred from content"),
    "yt-o64cI6tebnU": ("hormozi", "consulting episode with guest Caleb; unlabeled >> turns, advisory line inferred from content"),
    "yt-x3e73Qn6NOo": ("hormozi", "podcast interview; no speaker labels, inferred from content"),
    "yt-ii1jcLg-eIQ": ("pg", "solo lecture"),
    "yt-QHJkUw31YX8": ("pg", "solo talk"),
    "yt-5bxp78i96S8": ("pg", "interview answer, inferred from content"),
    "web-c75e015ff81a": ("pg", "essay on paulgraham.com (frontmatter author field is empty)"),
    "web-19ac0b6d18d2": ("pg", "essay on paulgraham.com (frontmatter author field is empty)"),
    "web-278ac10fa14b": ("pg", "essay on paulgraham.com (frontmatter author field is empty)"),
    "yt-1hHMwLxN6EM": ("seibel", "solo Startup School lecture; speaker introduces himself as Michael"),
    "yt-7TU636F_yVQ": ("caldwell_or_seibel", "two-host show; captions have no speaker labels"),
    "yt-s1YszjhzQ6U": ("caldwell_or_seibel", "two-host show; captions have no speaker labels"),
    "yt-ozhRhElbVcI": ("caldwell_or_seibel", "two-host show; captions have no speaker labels"),
    "yt-rQtrzBcf_Us": ("caldwell_or_seibel", "two-host show; captions have no speaker labels"),
    "yt-ZIaOBAjvc38": ("altman", "conversation with Garry Tan; answer inferred from content (refers to people he started OpenAI with)"),
    "yt-8d-cApFHjeY": ("livingston", "solo conference talk"),
    "yt-eRrc1pUY5oU": ("tan", "solo talk"),
}


def ev(source_id, timestamp, quote, speaker=None, basis=None, supports=None):
    s = INV[source_id]
    spk, bas = SPEAKER[source_id]
    out = {
        "source_id": source_id,
        "source_path": s["source_path"],
        "source_sha256": s["source_sha256"],
        "source_title": s["title"],
        "source_date": s["date"],
        "speaker": speaker or spk,
        "speaker_basis": basis or bas,
        "timestamp": timestamp,
        "quote": quote,
    }
    if supports:
        out["supports"] = supports
    return out


GUEST_COREY = ("guest_corey", "business owner answering Hormozi's question; content-inferred")
GUEST_CALEB = ("guest_caleb", "business owner describing his own company; content-inferred")
HOST_DOAC = ("host_doac_interviewer", "the interviewer on The Diary Of A CEO; the raw file does not name him; content-inferred from 'my company went public' and 'flight story'")
SEIBEL_SOCIALCAM = ("seibel", "inferred: speaker co-founded Socialcam and Justin.tv, which the video description assigns to Michael Seibel")

# ---------------------------------------------------------------- diagnostics

DIAG = [
    {
        "id": "hz-02", "vault": "hormozi", "category": "known",
        "question": "Should my ads admit the weaknesses of my product, and if so how do I word it? What would Alex Hormozi say?",
        "key_status": "confirmed_expanded",
        "actual_stance": "Yes. Use damaging admissions: own your real flaws up front, because what you give up in promise you gain in trust. Word it as flaw, then 'but', then the benefit, since people believe the clause after 'but'; reversing the order stresses the flaw. List the things customers already complain about and claim them; humor earns extra credit. In a sales setting he applies the same idea by opening with the bad before the good and saying who the offer will not work for, so prospects self-qualify.",
        "required_points": [
            "Yes, admit real weaknesses (damaging admissions); it builds trust and makes later claims more believable.",
            "Order matters: flaw first, then 'but', then the benefit; the part after 'but' is what people believe.",
        ],
        "supporting_points": [
            "Trust beats promise; sacrificing some promise is worth it.",
            "Write down every flaw and complaint and claim it before the prospect thinks it.",
            "Humor is a bonus.",
            "In sales calls: tell them the bad before the good and who it is not for, so they self-qualify (MH-IMJxbUY4).",
            "Admissions must be true, not invented.",
        ],
        "errors": [
            "Advising to hide weaknesses or wait until the prospect raises them.",
            "Putting the benefit first and the flaw after 'but' as the recommended order.",
            "Recommending invented or fake flaws.",
        ],
        "primary_sources": ["yt-JDR-R--4HhM"],
        "evidence": [
            ev("yt-JDR-R--4HhM", "12:30", "you want to always own your flaws of course you have them of course your product isn't perfect say so and"),
            ev("yt-JDR-R--4HhM", "13:09", "what you'll sacrifice in promise you'll gain in trust and trust trumps promise"),
            ev("yt-JDR-R--4HhM", "13:44", "the statement that comes after the word but is the part that is the thing you want them to believe"),
            ev("yt-JDR-R--4HhM", "14:26", "these markers write four times longer than others but they smell like crap what am I emphasizing i'm actually emphasizing the fact that they smell bad not the fact that they write longer"),
            ev("yt-JDR-R--4HhM", "15:03", "write down all of the flaws all the things that people complain about the things that you know you could do better and claim them"),
            ev("yt-JDR-R--4HhM", "15:39", "if you can do with humor you get even more bonus points"),
            ev("yt-MH-IMJxbUY4", "19:42", "Listen, before I tell you about the good, let me tell you about the bad."),
            ev("yt-MH-IMJxbUY4", "20:14", "So, you can have what you want, just not when you want."),
        ],
        "gold_discrepancies": [
            "Gold stance and quotes match the raw transcript. Gold omitted the 'write down all the flaws and claim them' step, the humor bonus, and the sales-call version in MH-IMJxbUY4; these are now supporting points, not requirements.",
        ],
        "uncertainty": [],
    },
    {
        "id": "hz-05", "vault": "hormozi", "category": "fresh",
        "question": "What's a good monthly churn rate for a paid online community, and when should I worry about it? What would Alex Hormozi say?",
        "key_status": "confirmed_expanded",
        "actual_stance": "Using Skool platform data that he credits to Sam at Skool: average monthly retention is 80% (20% churn); the best groups churn under 10%; groups under 70% retention (30%+ churn) should make retention their top priority because it is the highest-ROI lever. Churn falls with tenure: 20%+ in months 1 to 3, about 10% or less after day 90, about 2% by month 6. So judge churn by cohort. A community younger than 90 days will show inflated churn, and high month-one churn is normal unless almost everyone leaves. Focus on getting members past month one (onboarding, expectations), day 90 (an outcome) and month 6 (connections). He says these benchmarks fit online and consumer services, not insurance-style or alarm-system subscriptions.",
        "required_points": [
            "Average about 80% monthly retention (20% churn); best groups under 10% churn.",
            "Worry when retention is under 70% (churn above 30%): retention becomes the highest-ROI fix.",
            "Churn depends on tenure: highest in months 1 to 3, about 10% or less after day 90, about 2% by month 6.",
        ],
        "supporting_points": [
            "Do not overhaul the business because month-one churn is high, unless basically everyone is leaving.",
            "A community under 90 days old will show inflated churn.",
            "Cutting churn from 20% to 10% doubles customer lifetime value.",
            "Benchmarks fit online/consumer services, not insurance or alarm-type subscriptions.",
            "Tactics: first-month onboarding, a day-90 outcome, month-6 connections; ask cancellers why, look for patterns.",
        ],
        "errors": [
            "Presenting SaaS 3 to 7% churn benchmarks as his view.",
            "Saying high month-one churn alone means the business is broken.",
            "Attributing the platform data to a source other than Skool.",
        ],
        "primary_sources": ["yt--j8_YCWZ05Q"],
        "evidence": [
            ev("yt--j8_YCWZ05Q", "1:05", "this isn't uh churn for like an insurance premium or an alarm system"),
            ev("yt--j8_YCWZ05Q", "1:39", "the platform average across School is 80% monthly retention. So said differently, it's 20% churn."),
            ev("yt--j8_YCWZ05Q", "1:39", "Now the best groups have less than 10% churn, aka 90% retention month over month. The not good groups have less than 70% retention, aka 30% or higher."),
            ev("yt--j8_YCWZ05Q", "1:39", "you probably need to work on your retention more than anything else. It'll be the highest ROI lever."),
            ev("yt--j8_YCWZ05Q", "2:13", "you got a double in the LTV per customer"),
            ev("yt--j8_YCWZ05Q", "3:53", "Now, if you keep someone 90 days, which seems to be the first kind of big churn drop-off point, it drops to around 10% or less."),
            ev("yt--j8_YCWZ05Q", "3:53", "So, it goes from like 10% to 2%."),
            ev("yt--j8_YCWZ05Q", "4:24", "if your community or recurring revenue thing is less than 90 days old, then your churn is always going to be inflated"),
            ev("yt--j8_YCWZ05Q", "4:57", "that's normal for it to be higher than the other months, unless basically everyone's leaving, in which case, yes, you should go fix that."),
        ],
        "gold_discrepancies": [
            "Gold matches raw. Added the scope caveat (online/consumer services, not insurance or alarm subscriptions), the under-90-days caveat and the 'unless everyone leaves' exception.",
            "Auto-captions spell the platform 'School'; it is Skool. Quotes keep the caption spelling.",
        ],
        "uncertainty": [
            "The benchmarks are Skool platform averages relayed by Hormozi, not his own measurements. Answers that say so are correct.",
        ],
    },
    {
        "id": "hz-09", "vault": "hormozi", "category": "fresh",
        "question": "My service business is profitable, but I'm carrying about $60k of debt. Should I pay it off or keep the cash for growth? What would Alex Hormozi say?",
        "key_status": "corrected_context",
        "actual_stance": "Pay it off. In the source the owner (Corey, HVAC duct cleaning, about $479k profit on $1.25M) already planned to clear the $60k in four to five months, and Hormozi approved ('Okay, good') and kept 'continue to pay off the debt' in the final plan. He calls it partly an emotional, back-of-mind issue and says he skews close to the Dave Ramsey side because debt increases risk, risk over a long horizon tends to come due, businesses have seasons and volatility, and many enduring companies such as Chick-fil-A run debt free. He did not frame it as debt instead of growth: in the same session he told Corey to keep raising ad spend while ROAS and CAC hold, after fixing the landing page and ads.",
        "required_points": [
            "Lean toward paying off the debt (he skews close to the Ramsey side).",
            "Reason: debt increases risk, and risk over a long time horizon tends to come due; businesses have seasons and volatility.",
        ],
        "supporting_points": [
            "Enduring companies like Chick-fil-A operate debt free.",
            "He calls it partly an emotional, back-of-mind issue.",
            "In context the owner already planned to pay it off in four to five months from cash flow, and Hormozi approved.",
            "Not either/or: in the same plan he kept funding proven ads while ROAS and CAC held.",
            "Paying it off adds only a few percent to profit but removes a lot of headache (speaker of the '5%' figure is uncertain; see uncertainty).",
        ],
        "errors": [
            "Saying he advises keeping cheap debt because leverage is a tool.",
            "Saying he told the owner to stop investing in growth until the debt is gone.",
            "Stating the 5% and '100% in headache' figures as a firm quantified rule he gave.",
        ],
        "primary_sources": ["yt-OQf2Ba-Lp_4"],
        "evidence": [
            ev("yt-OQf2Ba-Lp_4", "0:33", "So, right now, we're allocating about 10% of our profit going towards paying off some of our debt.", *GUEST_COREY),
            ev("yt-OQf2Ba-Lp_4", "3:15", "Profit on that is 479,000. Uh, our net margin is 38%.", *GUEST_COREY),
            ev("yt-OQf2Ba-Lp_4", "8:37", "We are planning to pay off completely in the next four to five months.", *GUEST_COREY),
            ev("yt-OQf2Ba-Lp_4", "8:37", "Okay, good. That's one of those things that like I'd say this is more of an emotional thing"),
            ev("yt-OQf2Ba-Lp_4", "8:37", "I tend to skew like very close to the Ramsey side and the single argument that I have around it is basically debt"),
            ev("yt-OQf2Ba-Lp_4", "9:10", "increases risk. Risk when multiplied over a long time horizon tends to come due."),
            ev("yt-OQf2Ba-Lp_4", "9:10", "businesses have seasons, they have volatility"),
            ev("yt-OQf2Ba-Lp_4", "9:10", "If you look at some of the most enduring companies, a lot of like Chick-fil-A operate debt free."),
            ev("yt-OQf2Ba-Lp_4", "10:48", "we just want to continue to spend month over month provided our ROAS and our CAC stay more or less the same."),
            ev("yt-OQf2Ba-Lp_4", "30:45", "Two is you're going to continue to pay off the debt."),
            ev("yt-OQf2Ba-Lp_4", "32:53", "But at least 100% in headache.", "uncertain", "unlabeled >> turn after a separate '5%' turn; could be Hormozi or Corey"),
        ],
        "gold_discrepancies": [
            "Gold says paying off 'adds only about 5% to profit but removes 100% in headache' as Hormozi's argument. In the raw, '5%.' and 'But at least 100% in headache.' are separate unlabeled >> turns, so the speaker is uncertain. Demoted to a supporting point.",
            "Gold omits that the owner had already decided to pay it off and that Hormozi approved rather than argued him into it, and that the same plan kept funding growth through ads. Added as context so answers that say 'pay it off and keep funding proven growth from cash flow' are not marked wrong.",
            "Raw-internal inconsistency: 10% of $479k profit is about $48k a year, which does not clear $60k in four to five months. Not material to the stance.",
        ],
        "uncertainty": [
            "The question gives no profit, interest rate or growth return. His stance comes from a business with about $479k annual profit, where $60k is small. Conditional answers that ask for these numbers are acceptable if they still state his lean.",
            "yt-sL16tsGafcQ at 16:55 to 18:02 discusses acquisition/fund-level debt as leverage. That is distinct from this operating-business debt case. A conditional answer noting that distinction is not itself an error; the specific Ramsey lean and cash-flow context remain the required factual stance.",
        ],
    },
    {
        "id": "hz-11", "vault": "hormozi", "category": "applied",
        "question": "I own a residential HVAC duct-cleaning company doing about $1.2M a year at a 38% net margin, and we close about 82% of in-home inspections. Should I keep prices where they are so I don't hurt the close rate? What would Alex Hormozi say?",
        "key_status": "confirmed_with_correction",
        "actual_stance": "No, raise prices. A close rate of 80% or more tells him there is room on price. He penciled in a 10% raise, framed as 'more asking than telling'. At this business's numbers that is roughly a 25% increase in net profit (about $100k+ a year at last year's volume), and it still makes more money as long as the close rate stays above about 65%. For a normal, non-luxury service, a higher price can raise the customer's conviction that you can deliver, and this owner's earlier 23% raise produced a higher close rate and more money. He says charging more is among the biggest levers for businesses under roughly $3M to $5M.",
        "required_points": [
            "Raise prices; an 80%+ close rate signals room on price.",
            "About 10%; the raise still pays as long as the close rate stays above about 65%.",
        ],
        "supporting_points": [
            "10% raise is roughly +25% net profit at a 38% margin (about $100k+ a year).",
            "Higher price can increase conviction that you deliver (normal goods, not Veblen goods).",
            "The owner's earlier 23% raise increased close rate and revenue.",
            "Framed as a suggestion ('more asking than telling').",
        ],
        "errors": [
            "Recommending keeping prices to protect the close rate.",
            "Claiming the 65% break-even is a general rule rather than this business's math.",
            "Treating the higher-price-higher-close effect as a luxury/Veblen effect.",
        ],
        "primary_sources": ["yt-OQf2Ba-Lp_4"],
        "evidence": [
            ev("yt-OQf2Ba-Lp_4", "1:05", "full end price for us is 1575 per HVAC unit.", *GUEST_COREY),
            ev("yt-OQf2Ba-Lp_4", "3:47", "And then our close rate is 82%.", *GUEST_COREY),
            ev("yt-OQf2Ba-Lp_4", "5:54", "So, you did a 23% price increase after the first time we talked to you."),
            ev("yt-OQf2Ba-Lp_4", "6:26", "And so, that resulted in a higher close rate and more money."),
            ev("yt-OQf2Ba-Lp_4", "7:00", "if you raise your prices, what sometimes happens is that the conviction of the customer that you can actually deliver on the promise you're making goes up."),
            ev("yt-OQf2Ba-Lp_4", "8:06", "So whenever I hear 80% or over 80% close rates, I usually know that there's room in sale."),
            ev("yt-OQf2Ba-Lp_4", "8:06", "Basically, what I penciled out was a 10% price raise. This is more asking than telling."),
            ev("yt-OQf2Ba-Lp_4", "8:06", "As long as we close more than 65%, we make more money. Thing is is that 10% price raise for you equals roughly a 25% increase in net profit."),
            ev("yt-OQf2Ba-Lp_4", "8:37", "So that'd be roughly a hundred plus thousand a year. And that's at last year's volume and profit."),
            ev("yt-OQf2Ba-Lp_4", "30:45", "Number one is we're going to do price raise of 10%. So, around 1650 per unit."),
        ],
        "arithmetic_checks": [
            "Profit $479k on $1.25M revenue (38%). A 10% raise at the same volume adds about $125k, all profit: 125/479 = +26%, consistent with 'roughly 25%' and 'a hundred plus thousand'.",
            "Break-even close rate if costs scale with jobs: 0.82 x 479 / (479 + 125) = 0.650, matching 'more than 65%'.",
        ],
        "gold_discrepancies": [
            "Gold matches raw. Added the prior 23% raise as direct evidence for 'higher price, higher close rate'.",
            "Raw-internal inconsistency: stated price is $1,575 per unit, but the plan says '10%, so around 1650 per unit'. 1,575 x 1.10 = about 1,733; 1,650 is about +4.8% (or 10% on $1,500). Answers should not be marked down for using either figure.",
        ],
        "uncertainty": [],
    },
    {
        "id": "hz-16", "vault": "hormozi", "category": "attribution",
        "question": "What's the story Hormozi tells about his company being worth four times more just by listing on the NASDAQ, and the IPO equity deal he took afterward?",
        "key_status": "confirmed_speaker_inferred",
        "actual_stance": "False attribution. The story is the interviewer's, not Hormozi's. The host of The Diary Of A CEO says his company went public on a European exchange, banks told him the same business would be worth four times more on the NASDAQ, and he later applied his social-media and marketing skills to companies heading to IPO, earning equity worth about $7M to $8M on IPO day for 9 to 12 months of work, which led to the company now called Flight Story. Hormozi only agreed and gave his own version: the biggest debt we pay is ignorance, fish where the fish are, 'same work, more zeros'. A 20% conversion lift is worth $200k to a $1M store (he takes $20k at 10%) but $20M to a $100M company (he takes $2M), 100x for the same work.",
        "required_points": [
            "Says the story is not Hormozi's; it belongs to the interviewer/host.",
            "Summarizes the host's story: European listing, banks said 4x on NASDAQ, pre-IPO equity worth about $7M to $8M for 9 to 12 months of work.",
        ],
        "supporting_points": [
            "Identifies the host as Steven Bartlett (external knowledge; consistent with 'Flight Story').",
            "Hormozi agreed and gave the 'same work, more zeros' CRO example ($20k vs $2M).",
            "The 4x NASDAQ figure was what banks told him, not an actual relisting.",
        ],
        "errors": [
            "Telling the story as Hormozi's own career lesson.",
            "Saying Hormozi's company listed on the NASDAQ.",
        ],
        "primary_sources": ["yt-x3e73Qn6NOo"],
        "evidence": [
            ev("yt-x3e73Qn6NOo", "1:33:37", "when my company went public on a Stock Exchange in um Europe", *HOST_DOAC),
            ev("yt-x3e73Qn6NOo", "1:34:12", "they told me that our business would be worth four times more if it was just on a different stock market if you move it to the NASDAQ the exact same business would be worth four times more", *HOST_DOAC),
            ev("yt-x3e73Qn6NOo", "1:35:51", "I think on the day of the IPO the equity that I got for for the 9 to 12 months work that i' done was worth in the region of 7 to8 million", *HOST_DOAC),
            ev("yt-x3e73Qn6NOo", "1:36:23", "company which is now called flight story", *HOST_DOAC),
            ev("yt-x3e73Qn6NOo", "1:36:23", "100% I thoroughly agree with everything you just said", "hormozi", "turn change inferred from content; captions have no speaker labels"),
            ev("yt-x3e73Qn6NOo", "1:38:03", "same work yeah same amount of time same Rod more zeros", "hormozi", "inferred: continues his fishing analogy and cites 'the first book'"),
            ev("yt-x3e73Qn6NOo", "1:38:38", "do the same work to a business doing $100 million a year I make them $20 million for my 20% bump and I get 10% that and I make $2 million 20,000 2 million 100x same work", "hormozi", "inferred from content"),
        ],
        "gold_discrepancies": [
            "Gold names Steven Bartlett. The raw file never names the host; the channel is The Diary Of A CEO and the speaker mentions Flight Story. The identification is external knowledge and is kept as a supporting point, not a requirement.",
        ],
        "uncertainty": [
            "All speaker attribution in this transcript is inferred from content because auto-captions carry no labels. The inference is strong here (first-person European IPO and Flight Story).",
        ],
    },
    {
        "id": "hz-20", "vault": "hormozi", "category": "abstain",
        "question": "Why did Hormozi tell that young roofing company owner to stop door-knocking and move his budget into Google Ads?",
        "key_status": "corrected",
        "actual_stance": "False premise. The sources do cover a young roofing company (Caleb, Keys Roofing in St. Louis, about two months old), and Hormozi told him the opposite: go all in on door-to-door as the primary growth engine and build a door-knocking sales team ('DDD army'). The transcript contains no Google Ads advice for this business. Other advice in the episode: shift toward repair volume, add VSLs, use a menu close, sell a maintenance membership and charge for speed. At the 90-day check-in Caleb said he went all in on door-to-door.",
        "required_points": [
            "Rejects the premise: he did not tell the roofer to stop door-knocking or move to Google Ads.",
            "States what he actually advised: go all in on door-to-door and build a door-to-door sales team.",
        ],
        "supporting_points": [
            "Names the case (Caleb, Keys Roofing, St. Louis, about two months in business).",
            "Mentions other advice (repairs focus, VSLs, menu close, maintenance membership, speed premium) or the 90-day outcome.",
        ],
        "errors": [
            "Accepting the premise and explaining why paid search beats door-knocking.",
            "Saying only 'the sources do not cover this' without noting they show the opposite (partial credit at most).",
            "Inventing a Google Ads recommendation.",
        ],
        "primary_sources": ["yt-o64cI6tebnU"],
        "evidence": [
            ev("yt-o64cI6tebnU", "0:32", "we are a premium and luxury roofing, gutter, and downspout contractor in St. Louis, Missouri.", *GUEST_CALEB),
            ev("yt-o64cI6tebnU", "0:32", "So, we've been in business for 2 months.", *GUEST_CALEB),
            ev("yt-o64cI6tebnU", "1:06", "two primary acquisition channels currently is door-knocking.", *GUEST_CALEB),
            ev("yt-o64cI6tebnU", "9:49", "Now I think that in terms of scale, you should go all in door to door."),
            ev("yt-o64cI6tebnU", "10:54", "I think you building out this DDD army is like the clear straight shot."),
            ev("yt-o64cI6tebnU", "24:27", "the first thing we said was go all in on door to door as primary growth engine."),
            ev("yt-o64cI6tebnU", "23:21", "So I went all in on door todoor first off", *GUEST_CALEB),
        ],
        "absence_check": "The word 'Google' appears in yt-o64cI6tebnU only as 'Google review'. No other Hormozi raw file mentions a roofer.",
        "gold_discrepancies": [
            "Gold stance begins 'The sources don't cover this' and then says the sources show the opposite. The two claims conflict; the raw supports the second. Corrected to a false-premise key with evidence.",
            "Gold had empty must_cite and evidence. Added the roofing episode as must_cite and seven verified quotes.",
            "The raw never states Caleb's age; 'young' fits the two-month-old business. Not material.",
        ],
        "uncertainty": [
            "Revenue figures in the episode are internally inconsistent (about $41k so far, '20K a monthish', 'a little under 32,000' three months earlier, then about $247k to $250k). Not needed for the key.",
        ],
    },
    {
        "id": "yc-01", "vault": "yc", "category": "known",
        "question": "I'm a 20-year-old CS student with a side project I'm excited about. Would Paul Graham tell me to start a startup now, while I'm still in college?",
        "key_status": "confirmed_expanded",
        "actual_stance": "No. He tells students not to start a startup in college: a startup takes over your entire life, so you cannot really be both a student and a founder, and 20 is not the optimal age. You give up nothing by waiting because you will be more likely to succeed later. In college, learn powerful things, build domain expertise and work on your own projects with people you like, because side projects are where the best ideas and cofounders come from ('just learn'). The exception: if a side project takes off on its own, like Facebook, it may be reasonable to run with it. His August 2026 essay repeats that running a startup is incompatible with being a full-time student and stresses students' own projects.",
        "required_points": [
            "No, do not start a startup while in college; a startup takes over your whole life, which is incompatible with being a full-time student.",
            "Exception: if the side project takes off on its own, it may be reasonable to run with it.",
        ],
        "supporting_points": [
            "Waiting costs nothing; you are more likely to succeed if you wait.",
            "Learn powerful things, get domain expertise; 'just learn'.",
            "Keep working on your own projects; they produce the best ideas and cofounders.",
            "The 2026 essay restates the incompatibility and the value of student projects.",
        ],
        "errors": [
            "Saying he recommends starting now because college is low risk.",
            "Telling the student to drop the side project entirely.",
        ],
        "primary_sources": ["yt-ii1jcLg-eIQ"],
        "evidence": [
            ev("yt-ii1jcLg-eIQ", "18:22", "you can't do that in college for the reason I just explained, that startups take over your entire life."),
            ev("yt-ii1jcLg-eIQ", "18:56", "Do not start a startup in college."),
            ev("yt-ii1jcLg-eIQ", "18:56", "20 is not the optimal time to do it."),
            ev("yt-ii1jcLg-eIQ", "21:12", "You're not sacrificing anything if you forego starting a startup at 20, cuz you'll be more likely to succeed if you wait."),
            ev("yt-ii1jcLg-eIQ", "21:12", "you're 20 and you have some side project that takes off like Facebook did. Then you face the choice of either running with it or not, and maybe it's reasonable to run with it."),
            ev("yt-ii1jcLg-eIQ", "30:15", "If you wanna start a startup, what you should do in college is learn powerful things."),
            ev("yt-ii1jcLg-eIQ", "30:49", "So here, is the ultimate advice for young would-be startup founders reduced to two words, just learn."),
            ev("web-c75e015ff81a", None, "Running a startup is incompatible with being a full time student."),
            ev("web-c75e015ff81a", None, "random side projects are where the best startup ideas come from."),
        ],
        "gold_discrepancies": [
            "Gold matches the 2014 lecture. It did not cite the August 2026 essay 'How Universities Should Prepare Founders', which confirms the same stance. Added; either source satisfies the key.",
        ],
        "uncertainty": [
            "The main source is from 2014. The 2026 essay supports the same position, so the stance is not stale.",
        ],
    },
    {
        "id": "yc-05", "vault": "yc", "category": "fresh",
        "question": "I'm building a startup in Stockholm. Does Paul Graham think I really need to move to Silicon Valley?",
        "key_status": "confirmed_expanded",
        "actual_stance": "Yes, at least for a while: go, and you can come back. You get the best peers, more serendipitous meetings, investors who decide faster, more respect from investors back home, and a realistic view of how good you are. Going and then actually returning is also one of the best things founders can do for Stockholm. He calls YC the optimal way to do the stint (four to six months). He cites YC data that startups going home after YC are only about half as likely to become unicorns, and discounts it three ways: selection bias, it measures valuation rather than performance, and half as well is still very good. He thinks Stockholm could become the Silicon Valley of Europe.",
        "required_points": [
            "Yes, go to Silicon Valley, at least for a while; you can come back.",
            "Mentions the unicorn-rate caveat or the benefit of returning to help Stockholm.",
        ],
        "supporting_points": [
            "Reasons: best peers, serendipitous meetings, faster investors, respect back home.",
            "YC is the optimal way to go for a bit and come back.",
            "Startups that go home after YC are about half as likely to become unicorns, discounted for selection bias, valuation vs performance, and 'half as well is still good'.",
            "Stockholm could become the Silicon Valley of Europe.",
        ],
        "errors": [
            "Saying he thinks remote work makes location irrelevant.",
            "Saying he advises moving permanently and never returning.",
        ],
        "primary_sources": ["yt-QHJkUw31YX8"],
        "evidence": [
            ev("yt-QHJkUw31YX8", "0:36", "And the answer is the same now as it always is. Yes, you should. You can go there for a bit and then come back, but you should at least go."),
            ev("yt-QHJkUw31YX8", "1:09", "You get the best peers."),
            ev("yt-QHJkUw31YX8", "5:00", "investors in Silicon Valley decide a lot faster."),
            ev("yt-QHJkUw31YX8", "16:10", "as long as you do actually come back, that's one of the best things you can do to help Sweden to help Stockholm thrive as a startup hub."),
            ev("yt-QHJkUw31YX8", "17:16", "Surely the optimal way to go to Silicon Valley for a bit and then come back is to do YC."),
            ev("yt-QHJkUw31YX8", "18:57", "startups that go back home after YC are only about half as likely to become unicorns."),
            ev("yt-QHJkUw31YX8", "18:57", "there's a lot of selection bias in this."),
            ev("yt-QHJkUw31YX8", "19:30", "even if you only do half as well, that's still pretty good."),
            ev("yt-QHJkUw31YX8", "20:04", "you could make it the Silicon Valley of Europe."),
        ],
        "gold_discrepancies": [
            "Gold matches raw. Added the reasons for going and the 'as long as you do actually come back' condition.",
        ],
        "uncertainty": [],
    },
    {
        "id": "yc-08", "vault": "yc", "category": "fresh",
        "question": "I've spent months pitching seed investors, polishing my deck and taking follow-up meetings. How would Michael Seibel tell me to think about fundraising?",
        "key_status": "confirmed_speaker_caveat",
        "actual_stance": "Fundraising comes down to leverage, meaning your ability to walk away, and the deck is not doing the work. Ask whether you are growing; if you are not growing or not launched, deck work may be the biggest waste of your time. The effective way to raise is to grow so fast, with so many proof points, that you can raise quickly with little preparation. Michael's own evidence: when Socialcam was hot he asked investors what share of deals they chase versus take from the front door, and every answer was between 80/20 and 90/10 chase; at Justin.tv he spent eight months fundraising without success, and the two months of forced focus on profitability that followed got far more done. Investors who string founders along for months are in effect buying an option on them.",
        "required_points": [
            "Stop polishing the deck; it is not doing the work. Leverage (traction, growth, ability to walk away) decides fundraising.",
            "Spend the time building, launching, talking to users and growing, so investors chase you.",
        ],
        "supporting_points": [
            "Investors chase 80% to 90% of their deals (his Socialcam-era poll).",
            "Justin.tv: eight months of failed fundraising vs two productive months focused on profitability.",
            "Being strung along for months means the investor is buying an option on you.",
            "Raise fast at the end, with little prep, once things are working.",
        ],
        "errors": [
            "Recommending a bigger investor list and a tighter deck as the main fix.",
            "Inventing statistics not in the source.",
        ],
        "primary_sources": ["yt-7TU636F_yVQ"],
        "evidence": [
            ev("yt-7TU636F_yVQ", "2:48", "If you're not growing and not launched, in many ways, working on this deck could be the biggest waste"),
            ev("yt-7TU636F_yVQ", "3:21", "the deck isn't doing the work at all."),
            ev("yt-7TU636F_yVQ", "3:54", "Leverage is also another way of thinking about is your ability to walk away."),
            ev("yt-7TU636F_yVQ", "5:02", "the way to be very effective at fundraising is to be growing so quickly and have so many proof points that your startup is working"),
            ev("yt-7TU636F_yVQ", "6:44", "one of the times we almost died at Justin TV you know I had spent the eight months prior trying to fundra", *SEIBEL_SOCIALCAM),
            ev("yt-7TU636F_yVQ", "6:44", "And the amount of we got done in that two months versus slinging decks", *SEIBEL_SOCIALCAM),
            ev("yt-7TU636F_yVQ", "8:57", "it's sort of like you're buying an option."),
            ev("yt-7TU636F_yVQ", "10:03", "And the answers I got only varied between 8020 chase and 9010 chase.", *SEIBEL_SOCIALCAM),
            ev("yt-7TU636F_yVQ", "10:03", "if you can invest that time in making your company something that investors will chase after versus decksmithing,", *SEIBEL_SOCIALCAM),
        ],
        "gold_discrepancies": [
            "Gold attributes everything to Michael Seibel. The episode is a two-host conversation with unlabeled captions. The Socialcam poll and the Justin.tv story are Michael's (he co-founded both). The leverage definition, the deck lines and the 'buying an option' point come from the joint conversation and may be Dalton's. Grade the content; do not penalize an answer that credits the episode to both hosts.",
        ],
        "uncertainty": [
            "Speaker split between Dalton Caldwell and Michael Seibel is not recoverable from the captions except where noted.",
        ],
    },
    {
        "id": "yc-12", "vault": "yc", "category": "applied",
        "question": "My cofounder and I are 9 months in, pre-product-market fit, and it's clearly over. He's vested a chunk of his stock and wants to keep it, and we've both hired lawyers who are trading letters. What would Michael Seibel tell us to do?",
        "key_status": "confirmed_speaker_caveat",
        "actual_stance": "Stop paying lawyers. Before product-market fit the stock is worth essentially nothing, so you are fighting over ego. Make the split no-fault and clean, and keep your mouths shut. Even if he has vested, the leaving founder should get down to under 5% of the company, and since this is within the first year, under 2% (they cite 1% to 2%, sometimes under 1%), so the remaining team has the equity to create the value. The staying founder should be generous with severance because everyone in the company is watching. Sign clean paperwork; it can be done in about a week for about $2,000. Do not make your advisor judge and jury; the facts no longer matter. Exception: lawbreaking or unethical conduct, where you call the lawyers.",
        "required_points": [
            "Stop the lawyer fight; pre-PMF stock is worth almost nothing.",
            "Leaving founder gives most of it back even if vested: under 5%, and under 2% within the first year (this case is at 9 months).",
            "No-fault, clean separation with clean paperwork.",
        ],
        "supporting_points": [
            "About a week and about $2,000.",
            "Staying founder offers reasonable severance and is generous; everyone is watching.",
            "Do not make an advisor the judge; facts do not matter once you are splitting.",
            "Exception for lawbreaking or unethical behavior.",
        ],
        "errors": [
            "Advising to enforce the agreements through litigation or negotiate a full buyout of vested shares.",
            "Giving the 5% figure for a first-year departure without the under-2% adjustment.",
        ],
        "primary_sources": ["yt-s1YszjhzQ6U"],
        "evidence": [
            ev("yt-s1YszjhzQ6U", "11:36", "in a situation where you're having a co-founder breakup and the stock is worth nothing, paying lawyers a bunch of money makes no sense."),
            ev("yt-s1YszjhzQ6U", "13:42", "the way it should go is sort of no fault from both sides."),
            ev("yt-s1YszjhzQ6U", "14:14", "Optimize for cleanliness for both sides."),
            ev("yt-s1YszjhzQ6U", "14:47", "regardless of your vesting, um you need to make sure that that company has as much equity as possible to motivate the people who are there"),
            ev("yt-s1YszjhzQ6U", "17:01", "you have an opportunity to be generous."),
            ev("yt-s1YszjhzQ6U", "17:33", "understand that everyone in your company is looking at you right now."),
            ev("yt-s1YszjhzQ6U", "18:39", "even if you vested, like get down to under 5% of the company, if it's within the first year, under 2%."),
            ev("yt-s1YszjhzQ6U", "18:39", "Do reasonable severance, sign clean paperwork and and peace out, right? Like you could do that whole thing in a week and spend like $2,000."),
            ev("yt-s1YszjhzQ6U", "21:22", "After a number of years, 5% typical. Under a year, 1%, 2%, sometimes less than 1%."),
            ev("yt-s1YszjhzQ6U", "21:54", "don't make your poor startup advisor into judge and jury."),
            ev("yt-s1YszjhzQ6U", "21:54", "if your co-founder is breaking the law, doing something unethical, killing people, none of this applies."),
            ev("yt-s1YszjhzQ6U", "21:54", "On this point, I maybe I'll be a little bit less nice than Dalton.", "seibel", "speaker refers to Dalton in the third person, so this turn is Michael's"),
        ],
        "gold_discrepancies": [
            "Gold attributes the whole framework to Michael Seibel. It is presented jointly in a two-host episode; only some turns can be assigned (for example the 'less nice than Dalton' turn is Michael's). The hosts say YC has these standards written down. Grade the content.",
            "Premise note: at 9 months, a standard four-year vesting schedule with a one-year cliff would usually mean nothing has vested. The source's advice holds 'even if you vested', so the stance does not change. Answers that point out the cliff are fine.",
        ],
        "uncertainty": [
            "Speaker split between the two hosts is mostly unrecoverable.",
        ],
    },
    {
        "id": "yc-17", "vault": "yc", "category": "attribution",
        "question": "Why does Garry Tan say the premium on doing YC is bigger than ever and that the gap between YC and second place has grown?",
        "key_status": "confirmed_with_interpretation_flag",
        "actual_stance": "False attribution. Sam Altman said it, in his closing conversation with Garry Tan at Startup School 2026, prefacing it with 'I can say this, Garry probably can't'. He explained the widening gap as network effects: networks put you where you meet future cofounders (he met his OpenAI cofounders years earlier), and that takes a long time to compound. Just before, he said YC's once-heretical push to move to San Francisco was clearly right, though he has less intuition about it now.",
        "required_points": [
            "Corrects the attribution: Sam Altman said it, not Garry Tan.",
            "Gives his reason: network effects (meeting future cofounders, compounding over time).",
        ],
        "supporting_points": [
            "Prefaced with 'I can say this, Garry probably can't'.",
            "Context: Startup School 2026 conversation with Garry Tan.",
            "Context: moving to SF was clearly right in hindsight; he has less intuition about it now.",
            "Inference that it would sound self-serving from YC's CEO is reasonable but not stated in the source.",
        ],
        "errors": [
            "Attributing the claim to Garry Tan.",
            "Explaining it with reasons the source does not give (bigger checks, brand) as if quoted.",
        ],
        "primary_sources": ["yt-ZIaOBAjvc38"],
        "evidence": [
            ev("yt-ZIaOBAjvc38", "16:25", "it used to be very heretical that YC told people they had to move to San Francisco. And looking back, it was clearly right."),
            ev("yt-ZIaOBAjvc38", "16:56", "I also think that I I can say this, Gary probably can't. I I I think the premium on doing YC is bigger now than it's like ever been before."),
            ev("yt-ZIaOBAjvc38", "16:56", "the distance between like YC and second place is has expanded. And this is a reminder of the power of"),
            ev("yt-ZIaOBAjvc38", "17:28", "network effects."),
            ev("yt-ZIaOBAjvc38", "17:28", "the people that I started OpenAI with, I met like many many years in some cases before uh starting OpenAI"),
            ev("yt-ZIaOBAjvc38", "17:28", "the sooner you can put yourself just in a flow where you're going to meet the people that will be your eventual co-founders"),
        ],
        "gold_discrepancies": [
            "Gold says Altman prefaced the line 'because it would sound self-serving coming from YC's current CEO'. The raw gives the preface but not the reason. Kept as an acceptable inference, not a required point.",
            "Captions spell the name 'Gary'; quotes keep the caption spelling.",
        ],
        "uncertainty": [
            "Speaker attribution is inferred from content (answer references OpenAI cofounders; Tan asks the questions). The description confirms the conversation format.",
        ],
    },
    {
        "id": "yc-20", "vault": "yc", "category": "abstain",
        "question": "Jessica Livingston has said early YC deliberately backed the most aggressive, ruthless founders because they're the ones who win. Why did she believe that?",
        "key_status": "confirmed_expanded",
        "actual_stance": "False premise: the sources contain no such statement, and she said the opposite. Her role in early selection was judging character: did applicants seem earnest, determined and flexible-minded, and how did the cofounders relate. She was careful to fund only earnest people and rejected people she could tell were conceited. She describes YC as feeling like a family with her as its mom, and herself as soft and sensitive at a time when investors were hardened and aggressive, adding 'ruthless' for a couple she knew. Determination is one trait she looked for; ruthlessness is not.",
        "required_points": [
            "Rejects the premise; there is no such statement, and her stated approach was the opposite.",
            "She funded earnest people and turned down conceited ones.",
        ],
        "supporting_points": [
            "She looked for earnest, determined, flexible-minded founders and healthy cofounder relationships.",
            "She described herself as soft and sensitive when investors were hardened, aggressive and sometimes ruthless.",
            "YC felt like a family and she was its mom.",
            "Context only: PG separately says investors want 'formidable' founders who get what they want; that is not Jessica's claim and is not ruthlessness.",
        ],
        "errors": [
            "Accepting the premise and explaining why ruthless founders win.",
            "Recasting PG's 'formidable' as Jessica endorsing ruthlessness.",
        ],
        "absence_check": "Corpus check on 2026-10-19 across all 24 YC raw files: the whole word 'ruthless' appears only in yt-8d-cApFHjeY at 17:44, where Livingston describes other investors, not founders she selected. Her selection criteria and rejection of conceited applicants are supported by the quoted passages.",
        "primary_sources": ["yt-8d-cApFHjeY"],
        "evidence": [
            ev("yt-8d-cApFHjeY", "14:51", "did they seem earnest did they seem determined were they flexible minded"),
            ev("yt-8d-cApFHjeY", "14:51", "from the beginning I was very careful about only funding earnest people"),
            ev("yt-8d-cApFHjeY", "15:27", "if I could tell someone was a conceited we did not fund them"),
            ev("yt-8d-cApFHjeY", "17:44", "it felt like a family and I was its mom"),
            ev("yt-8d-cApFHjeY", "17:44", "I was soft and sensitive at a time when investors tended to be hardened and aggressive and I'll throw in ruthless - for a couple of them that I know"),
            ev("yt-5bxp78i96S8", "9:57", "it's someone who gets what they want in any situation.", supports="context only: PG's definition of 'formidable'; not part of the Jessica key"),
        ],
        "gold_discrepancies": [
            "Gold had must_cite empty while listing evidence from yt-8d-cApFHjeY. Set must_cite to that source, since citing the counter-evidence is the correct behavior for this false premise.",
            "Added 'determined' from her own criteria so an answer mentioning determination is not marked as accepting the premise.",
        ],
        "uncertainty": [],
    },
]

# ------------------------------------------------------------------- advice

ADVICE_Q = [
    ("advice-hz-01", "hormozi", "offers",
     "I run a one-person bookkeeping service for Shopify stores. I have 45 clients on month-to-month plans at $400 a month. Software and payment fees cost me about $40 per client per month, and nothing else scales with the number of clients, so I clear about $16,200 a month. I work 50 hours a week and can't go above that: roughly 1 hour per client per week plus 5 hours of admin. About 8 of my clients do over $2M a year in sales, and they keep asking for help with cash-flow forecasting, inventory planning and coordinating with their tax preparer, which I now do for free when I have time. My goal is at least $25,000 a month in profit within 6 months, without hiring. I'm considering three moves: (1) raise my standard price to $500 for everyone with 60 days' notice; (2) add a premium tier at $2,000 a month for up to 5 clients, which I estimate would add 2 hours per client per week on top of the normal hour; (3) record a $49-a-month self-serve course for small stores. Which should I do, in what order, and what exactly should the premium tier include if I add it? Please give me a clear decision and show that the plan fits my hours."),
    ("advice-hz-02", "hormozi", "pricing",
     "I own a mobile dog-grooming business with one fitted van and two groomers who alternate, so the van runs 6 days a week. We do 6 grooms per van-day at an average ticket of $95. Groomers are paid 40% of each ticket, and supplies plus fuel run about $12 per groom. Fixed costs (van loan, insurance, software) are $3,800 a month. We're booked solid three and a half weeks out, about 70% of bookings are regulars who rebook every 6 to 8 weeks, and we turn away or waitlist around 15 requests a week. A second fitted van would cost $78,000, about $1,650 a month financed, and hiring and training two more groomers takes about 2 months. I want more profit this year but I don't want to lose my regulars. What should I change about pricing and booking in the next 90 days, and should I buy the second van now or wait? Make a call and show the numbers."),
    ("advice-hz-03", "hormozi", "ads",
     "We sell one product online, a vitamin C face serum at $58 a bottle, and about 30% of customers reorder within 3 months. Over the last 30 days Meta Ads Manager reports a 3.2 ROAS at $300 a day, using a 7-day-click, 1-day-view attribution window. We have $45,000 to spend on ads from now through December 31, and enough stock for about 4,000 more bottles; a reorder from our manufacturer takes 10 weeks. Our agency wants to raise spend to $1,000 a day starting this week and hold it through the end of December to catch Black Friday and the holidays. Should we approve that plan? If not, what spend plan would you run instead? I need a yes or no on the $1,000-a-day plan."),
    ("advice-hz-04", "hormozi", "customer_acquisition",
     "My commercial cleaning company does about $1.1M a year. The average contract is $2,400 a month at a 35% gross margin, and clients stay about 20 months on average. About 80% of our new contracts, roughly 4 buildings a month, come from one property-management firm. That firm was just acquired, and the new owner already uses a national cleaning vendor, so I could lose that flow within 6 months. I can spend $8,000 a month on growth, and my operations manager could take on sales part-time. The options in front of me: (a) a Google Ads agency that quotes about $150 per lead and a 12% lead-to-contract rate, plus a $2,000 monthly fee; (b) a full-time outbound sales rep at $5,500 a month all-in, aiming for 3 qualified walkthroughs a week, and we close about 30% of walkthroughs; (c) a formal referral program with other property managers and with vendors who serve the same buildings, such as HVAC, pest control and security companies. What should I do first, how should I set it up, and what should the next 6 months look like? Please commit to a plan."),
    ("advice-hz-05", "hormozi", "offers_retention",
     "I run an online strength-training membership for women over 40 at $79 a month: app-based workout plans, one live Q&A call a week, a recipe library and a private community. We have 600 members. We add about 90 new members a month, almost all from Instagram ads at about $110 per new member, and about 18% of members cancel each month, mostly in their first 60 days. My goal is 1,000 members by next October. My team's ideas are: add two more live classes a week and a meal-planning tool; cut the price to $49 to get more sign-ups; launch an annual plan; or double the ad budget. I only have the time and money to do two of these. Which two should I pick and why, and is 1,000 members by next October realistic?"),
    ("advice-hz-06", "hormozi", "first_business_decision",
     "I'm 27 and work full time as a receptionist at a dental office. I take home $3,400 a month, my expenses are $2,900, and I have $11,000 saved. I can give a side business about 20 hours a week, and I want it to replace my salary within 18 months. I have three ideas: (1) a new-patient lead-generation and appointment-setting service for dental offices, based on what I've seen of how front desks handle new-patient calls; (2) an online store for ergonomic office products, which needs about $6,000 for the first inventory order; (3) buying an existing vending-machine route for $9,000, which the seller says nets $700 a month. Which one should I pick, and what should my first 90 days look like? Please pick one."),
    ("advice-yc-01", "yc", "startup_decision_mvp",
     "My cofounder and I are both engineers. Over the last 5 weeks we used coding agents to build an AI assistant for small veterinary clinics. It records the exam and writes the clinical notes, drafts discharge instructions for pet owners, suggests inventory reorders, sends appointment reminders, helps with billing codes, adds a chat widget to the clinic website, and has about 30 smaller features. Three clinics agreed to pilot it for free. After a month, one clinic uses the note-writing every day and the other two have logged in twice each. We have $210,000 in the bank and spend about $22,000 a month. One investor told us to move to human hospitals because the market is bigger. We're choosing between three paths: keep building toward a complete practice-management system before charging anyone, cut the product down and get it into many more clinics now, or switch to hospitals. What should we do, and what should the next 8 weeks look like? We have to decide this week."),
    ("advice-yc-02", "yc", "pricing_customer_segment",
     "We're a three-person startup with an API that pulls structured data out of invoices and receipts. We have $640,000 left and burn $45,000 a month. Two kinds of customers have shown up. Seed-stage startups sign up on their own, integrate in a day and pay usage-based pricing: 30 of them, averaging $210 a month, and total monthly revenue has grown about 15% a month for the last 4 months. Separately, a large logistics company has offered a $90,000-a-year contract, but it needs SOC 2, an on-premises deployment option and custom fields, and their procurement usually takes 6 to 7 months; a second logistics company is interested on similar terms. This year we can realistically build either the enterprise requirements or self-serve improvements (better docs, more document types, a usage dashboard), not both. Which segment should we focus on, and should we change our pricing? Give us a recommendation with your reasoning on runway."),
    ("advice-yc-03", "yc", "startup_decision_quit_job",
     "I'm a product designer at a large bank. For the last 4 months I've been building, in the evenings, a budgeting app for couples who share expenses. It launched in July and has 1,400 sign-ups, mostly from two Reddit posts and one TikTok that took off. I don't have a cofounder. I have about 9 months of living expenses saved. My manager has offered me a promotion that requires committing to stay at least a year, and I have to answer by the end of the month. Should I quit and work on the app full time, or take the promotion and keep building on the side? I want a yes or no."),
    ("advice-yc-04", "yc", "customer_acquisition_launch",
     "We sell scheduling and crew-dispatch software to electrical and plumbing subcontractors. We have 15 paying customers at $400 a month, all from the founders' personal networks and two trade-association meetups. We just closed a $1.5M seed round and plan a public launch next month. A PR agency has pitched $12,000 a month, with a 3-month minimum, to get us coverage in tech and business press around the launch. Our other ideas are founder-led cold outreach to subcontractors in three metro areas, sponsoring trade-association events, and posting regular field-operations content on LinkedIn and YouTube. Should we hire the agency? If not, where should that $36,000 go? Recommend one plan for the next 3 months."),
    ("advice-yc-05", "yc", "hiring",
     "We're a 4-person startup, 2 founders and 2 engineers, building a developer tool. We raised a $3M seed round 3 months ago and need two senior backend engineers. In the last 6 weeks we interviewed 7 people and made 3 offers at $185,000 salary plus 0.5% equity; all 3 took offers from large AI companies at roughly twice the cash. Our process takes about 3 weeks from first call to offer, and the founders spend about 2 hours a week on recruiting. The options we're weighing: raise the cash offer to $240,000 and cut the equity, pay a recruiting agency 25% of first-year salary, hire a contract team overseas, or stop hiring and lean harder on coding agents with the team we have. What should we change, and which option should we choose?"),
    ("advice-yc-06", "yc", "startup_decision_idea_choice",
     "I have to choose between two startup ideas and can only do one. Idea A is an AI sales-development tool that writes and sends personalized outbound emails for B2B companies. I already have 3 letters of intent from friends' companies, two seed investors have said they would probably invest, and there are dozens of funded competitors. Idea B is software that helps small municipal water utilities, serving fewer than 10,000 people, predict pipe failures and plan repairs. I spent 4 years as a civil engineer at a water utility and know the data and the problems well, but utilities buy slowly and need council approval, and no investor I've spoken to is excited. My technical cofounder will join me on either idea. I have 14 months of savings. Which idea should we pursue, and how should we reduce the risk in the first 6 months? Please pick one."),
]

COMMON_JUDGING = [
    "Judge usefulness for this person's stated goal and constraints. Matching the source's stance is not required.",
    "Several recommendations are defensible; do not lower a score because the answer differs from the source-inspired direction.",
    "Hard errors are arithmetic mistakes, plans that break a stated constraint, and invented facts about the user's situation.",
]

ADVICE_EV = [
    {
        "id": "advice-hz-01", "vault": "hormozi", "domain": "offers",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Business, prices and hours are invented. Principles drawn from: premium one-to-one tiers, anchoring and capping supply (yt-uWdIgftpvBI); repackaging for the segment that buys the top package (yt-x3e73Qn6NOo); focus on one thing (yt--JLN1d1ZKUU).",
        "hard_checks": [
            "Status quo: 45 x $400 = $18,000 revenue; 45 x $40 = $1,800 costs; profit $16,200; hours 45 + 5 = 50.",
            "Option 1 alone, no churn: 45 x $460 = $20,700 profit. Short of $25,000 even if nobody leaves. With 4 clients leaving: 41 x $460 = $18,860 and 46 hours.",
            "Option 2 alone as 5 upgrades of existing clients: $16,200 + 5 x $1,600 = $24,200 profit but 60 hours. Breaks the 50-hour cap.",
            "Option 2 alone as 5 new clients: $26,000 profit but 65 hours. Breaks the cap.",
            "Options 1 + 2 combined (5 upgrades at $2,000, others at $500, release the 10 smallest): 5 x $1,960 + 30 x $460 = $23,600 profit; hours 15 + 30 + 5 = 50. Fits the cap but is about $1,400 short; reaching $25,000 on this structure needs a premium price of about $2,280 or more, or a further adjustment.",
            "Option 3: adding $8,800 a month at $49 needs about 180 paying subscribers, with no stated audience, and recording time competes with the 50-hour cap.",
        ],
        "constraint_checks": [
            "Any recommended plan must stay at or under 50 hours a week; a plan that adds premium work without freeing hours violates the stated constraint.",
            "No hiring within 6 months.",
            "A claim that a plan reaches $25,000 must hold under the stated numbers.",
        ],
        "defensible_answers": [
            "Premium tier first, sold to the 8 large clients, priced high enough to hit the goal, while raising standard price or releasing the smallest clients to free hours.",
            "Raise standard price first (low effort, frees hours through churn), then launch the premium tier.",
            "Premium tier only, priced at $2,500 or more for fewer clients, with explicit time limits, plus a price raise later.",
            "Any order is acceptable if the hours and profit math hold and the course is either deferred or justified with a distribution plan.",
        ],
        "credit_signals": [
            "Notices the 50-hour cap binds and does the arithmetic.",
            "Defines concrete premium deliverables (for example monthly cash-flow forecast, inventory plan, tax-preparer coordination, response-time commitment) and a cap on seats.",
            "Uses the 8 large clients' existing requests as demand evidence.",
            "Gives a clear order and a decision.",
        ],
        "source_support": [
            ev("yt-uWdIgftpvBI", "0:00", "either sell extremely expensive stuff to a select few or sell something super cheap to everyone. The middle is where people die."),
            ev("yt-uWdIgftpvBI", "5:28", "when you have demand, cut supply."),
            ev("yt-uWdIgftpvBI", "10:19", "have something that's $1,000 a month. Have something that's $10,000 one time."),
            ev("yt-uWdIgftpvBI", "13:04", "Likely the person that's going to spend the $1,000 is a different person."),
            ev("yt-uWdIgftpvBI", "15:19", "be willing to take 5 10% of your time, charge 10 times more"),
            ev("yt-x3e73Qn6NOo", "1:23:11", "85% of their customers were small business owners and turned out in like three or four months 15% of their custom"),
            ev("yt-x3e73Qn6NOo", "1:23:44", "package and stayed like forever and I was like hey crazy idea what if we only served these customers"),
            ev("yt-x3e73Qn6NOo", "1:23:44", "were able to 10x our prices"),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-hz-02", "vault": "hormozi", "domain": "pricing",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: supply-constrained vs demand-constrained diagnosis (yt-OQf2Ba-Lp_4); charging for speed and priority when supply-constrained (yt-o64cI6tebnU); raising price when demand exceeds supply (yt-uWdIgftpvBI).",
        "hard_checks": [
            "Current: 6 grooms x 26 van-days = 156 grooms a month; profit per groom $95 - $38 - $12 = $45; 156 x $45 = $7,020; minus $3,800 fixed = $3,220 a month.",
            "Groomer pay is 40% of the ticket, so a price rise is shared: at +15% ($109.25) profit per groom is 0.6 x 109.25 - 12 = $53.55, +$8.55 per groom, about +$1,334 a month (+41%) if volume holds.",
            "Second van demand: 15 requests a week is about 65 grooms a month, about 42% of a second van's 156-groom capacity. At $45 each that is about $2,925 a month against $1,650 financing, before added insurance or marketing, and after a 2-month hiring and training lag.",
        ],
        "constraint_checks": [
            "Retain regulars: a plan that raises regulars' prices sharply without a transition or communication plan ignores the stated concern.",
            "90-day window for pricing and booking changes.",
        ],
        "defensible_answers": [
            "Raise prices for new clients now and for regulars after notice or at a smaller step; add a paid priority or short-notice fee; wait on the van until the waitlist proves it can fill most of a second van.",
            "Buy the second van now if the owner can fill it through marketing, with the utilization math shown; acceptable if the plan addresses the fill-rate gap and hiring lag.",
            "Add a recurring membership or prepaid plan for regulars combined with a price increase.",
        ],
        "credit_signals": [
            "Identifies the business as supply-constrained.",
            "Accounts for the 40% groomer share when computing price-rise gains.",
            "Checks second-van utilization rather than assuming full demand.",
            "Gives an explicit van decision.",
        ],
        "source_support": [
            ev("yt-OQf2Ba-Lp_4", "3:47", "I think the first problem I try to delineate is this is a supply constraint business or a demand constraint business."),
            ev("yt-OQf2Ba-Lp_4", "4:19", "they're trying to fix a problem that's already a problem that if you fix it, makes your existing problem worse."),
            ev("yt-o64cI6tebnU", "18:33", "But literally just reshifting the order of the work by allowing people to spend more to go first"),
            ev("yt-o64cI6tebnU", "20:10", "especially if you're supply constraint, meaning you have more people who want your stuff than you have the ability to do, add speed incentives"),
            ev("yt-uWdIgftpvBI", "5:28", "when you have demand, cut supply."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-hz-03", "vault": "hormozi", "domain": "ads",
        "case_types": ["missing_critical_input"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: spend more only while ROAS and CAC hold and attribution is verified (yt-OQf2Ba-Lp_4); scaling into a spend wall where CPA rises and creative caps spend (yt-MH-IMJxbUY4); spending as much as possible while staying at break-even or better (yt-tGhe3sBuk34).",
        "missing_critical_inputs": [
            "Contribution margin per order (product cost, shipping, payment fees, returns). Without it the break-even ROAS is unknown: break-even ROAS = 1 / contribution margin. At 30% margin break-even is 3.33, so the reported 3.2 loses money; at 60% it is 1.67, so 3.2 is comfortably profitable.",
            "Whether the platform-reported 3.2 matches blended results (total revenue / total ad spend) given view-through attribution.",
        ],
        "how_good_answers_handle_it": "Ask for or state the margin assumption and give the decision as a rule (for example scale only if contribution margin is above about 31% and blended returns confirm the platform number), or make the call conditional with thresholds. An unconditional 'scale to $1,000' or 'never scale' without addressing margin should score lower.",
        "hard_checks": [
            "October 19 through December 31, 2026 is 74 days. $1,000 a day for 74 days is $74,000, above the $45,000 budget; at $1,000 a day the budget runs out after 45 days. The average affordable rate over the whole period is about $608 a day.",
            "At 3.2 ROAS, $1,000 a day is about $3,200 revenue, about 55 bottles a day; 45 days is about 2,480 bottles. Spending the full $45,000 at 3.2 ROAS sells about 2,480 bottles, under the 4,000 in stock, but reorders from the 30% repeat rate add demand and a new production run takes 10 weeks.",
            "Every answer and judge receives the explicit evaluation date 2026-10-19. Counting October 19 through December 31 inclusively gives 74 days. Accept roughly 70 to 75 days with a reasonable counting convention, while checking that $45,000 cannot fund $1,000 a day for the whole remaining period.",
            "ROAS at 3.3x the spend is unlikely to stay at 3.2; any plan should step up spend and watch CPA.",
        ],
        "constraint_checks": [
            "$45,000 total ad budget through December 31.",
            "Inventory of about 4,000 bottles with a 10-week reorder lead time.",
            "User asked for a yes or no on the $1,000-a-day plan.",
        ],
        "defensible_answers": [
            "No as stated (budget does not cover it), with a stepped plan that front-loads or concentrates spend around Black Friday within $45,000, conditional on margin.",
            "Yes for a limited window (for example Black Friday through Cyber Monday) if margin clears break-even, with stop rules.",
            "No until margin and blended returns are confirmed, then scale stepwise.",
        ],
        "credit_signals": [
            "Flags missing margin and computes or explains break-even ROAS.",
            "Catches the budget arithmetic.",
            "Mentions attribution or blended returns.",
            "Checks inventory and reorder timing.",
        ],
        "source_support": [
            ev("yt-OQf2Ba-Lp_4", "10:48", "we just want to continue to spend month over month provided our ROAS and our CAC stay more or less the same."),
            ev("yt-OQf2Ba-Lp_4", "11:21", "Now, if you're not sure, then you have a data problem. So, you got to go make sure the attribution's right. But, if you know that's where the money's coming from, by all means, spend more."),
            ev("yt-MH-IMJxbUY4", "2:12", "I spent 150 grand last month and it got 10% extra book sales.", "guest_joel", "business owner describing his own results; content-inferred"),
            ev("yt-MH-IMJxbUY4", "12:00", "the creative unlock is usually why someone gets limited."),
            ev("yt-MH-IMJxbUY4", "13:06", "as soon as you hit you try to break through this wall, your CPA goes up because the new creative's not good enough."),
            ev("yt-tGhe3sBuk34", "8:17", "the goal is to spend as much money as humanly possible uh while maintaining break even or better."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-hz-04", "vault": "hormozi", "domain": "customer_acquisition",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: affiliate partner offers, referral limits and a full-time owner per channel (yt-OQf2Ba-Lp_4); single-channel dependence and squeezing the existing channel first (yt-MH-IMJxbUY4); one owned lead channel as the priority (yt--JLN1d1ZKUU).",
        "hard_checks": [
            "Lifetime gross profit per contract: $2,400 x 35% x 20 months = $16,800.",
            "Account base: $1.1M / 12 / $2,400 is about 38 accounts; at a 20-month average life about 1.9 leave a month. New contracts are about 5 a month (4 from the partner). Without the partner, about 1 new a month against about 1.9 leaving, so the business shrinks.",
            "Google Ads option within $8,000: $2,000 fee + $6,000 media = 40 leads x 12% = 4.8 contracts, about $1,667 per contract all-in ($1,250 media only).",
            "Sales rep: 3 walkthroughs a week is about 13 a month x 30% = 3.9 contracts, about $1,410 per contract at full productivity, before ramp time.",
            "Both paid options cost under 10% of lifetime gross profit per contract, so the decision turns on speed, reliability and capacity more than unit economics.",
        ],
        "constraint_checks": [
            "$8,000 a month growth budget.",
            "Ops manager is part-time on sales.",
            "Referral loss may happen within 6 months.",
        ],
        "defensible_answers": [
            "Start the referral/affiliate program with a concrete partner offer and a named owner, plus try to keep the acquired firm's business; add one paid channel.",
            "Hire the outbound rep first (predictable, controllable channel) and run referrals part-time.",
            "Google Ads first for speed, while building referrals; acceptable if lead quality risk is addressed.",
        ],
        "credit_signals": [
            "Does the LTV and CAC math.",
            "Recognizes the business shrinks without replacing the partner flow.",
            "Gives partners a real incentive rather than 'ask for referrals'.",
            "Assigns ownership and a timeline; addresses retaining the acquired partner.",
        ],
        "source_support": [
            ev("yt-OQf2Ba-Lp_4", "24:45", "most of times if you want to have like a true kind of affiliate partner program, we need to have some sort of offer for them."),
            ev("yt-OQf2Ba-Lp_4", "25:50", "Referrals everyone promises, no one delivers."),
            ev("yt-OQf2Ba-Lp_4", "28:02", "it's unlikely that you're going to have sufficient referral volume to send them all enough business."),
            ev("yt-OQf2Ba-Lp_4", "29:39", "I don't think you're going to be able to do both of these."),
            ev("yt-OQf2Ba-Lp_4", "30:12", "for each of these things, you basically need someone who's full-time in charge of that."),
            ev("yt-MH-IMJxbUY4", "2:12", "So, our biggest problem right now, single channel advertising.", "guest_joel", "business owner describing his own problem; content-inferred"),
            ev("yt-MH-IMJxbUY4", "5:27", "I feel like there's a lot more that you can work on the existing one by like a lot."),
            ev("yt--JLN1d1ZKUU", "3:52", "if we had a dedicated lead channel that we owned, that one thing would change everything."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-hz-05", "vault": "hormozi", "domain": "offers_retention",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: growth as joins minus cancels, annual plans, overwhelm as a churn driver, price objections from non-ideal customers (yt--j8_YCWZ05Q); subtracting features to cut overwhelm (yt--JLN1d1ZKUU). Distinct from diagnostic hz-05: this case asks for a decision under arithmetic, not a benchmark.",
        "hard_checks": [
            "Steady state = new per month / monthly churn = 90 / 0.18 = 500 members. The membership is shrinking: next month is 600 x 0.82 + 90 = 582.",
            "Twelve-month projection, m(next) = m x (1 - churn) + new: current inputs give about 509; doubling acquisition to 180 a month at 18% churn gives about 963; halving churn to 9% at 90 a month gives about 871; both together give about 1,549.",
            "So 1,000 by next October needs both more acquisition and lower churn, or a much larger change in one of them. Doubling ad spend at the same $110 cost per member is optimistic.",
            "Revenue per member at 18% churn: about 1 / 0.18 = 5.6 months x $79 = $439, about 4x the $110 acquisition cost. At $49, each member brings 38% less, so about 61% more members are needed for the same revenue.",
        ],
        "constraint_checks": [
            "Choose exactly two of the four ideas.",
            "Goal date about 12 months out.",
        ],
        "defensible_answers": [
            "Annual plan plus doubled ads, with first-60-day onboarding fixes inside the existing product.",
            "Annual plan plus an onboarding/retention fix, arguing more features add overwhelm; doubles ads later.",
            "Doubling ads plus annual plan, with the projection showing the shortfall if churn does not move.",
            "Picking the feature additions is defensible only with a reason they would reduce early churn; the price cut needs a reason to expect much lower churn or much higher conversion.",
        ],
        "credit_signals": [
            "Computes the steady state or projection and answers the realism question honestly.",
            "Targets early-tenure churn.",
            "Picks two and explains the tradeoff.",
        ],
        "source_support": [
            ev("yt--j8_YCWZ05Q", "0:33", "your MRR, meaning your monthly recurring revenue, grows when new members are greater than churn members."),
            ev("yt--j8_YCWZ05Q", "7:08", "If you can only do one thing that gets people to stay, why would you do five?"),
            ev("yt--j8_YCWZ05Q", "8:46", "If non-ideal people say it's too expensive, just ignore it."),
            ev("yt--j8_YCWZ05Q", "9:18", "The number one reason people churn, outside of price, is overwhelm."),
            ev("yt--j8_YCWZ05Q", "15:52", "annual always has lower churn than monthly"),
            ev("yt--j8_YCWZ05Q", "16:26", "16 16 or 17% which is usually buy 10 get two"),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-hz-06", "vault": "hormozi", "domain": "first_business_decision",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: cutting costs, using the hours around a job, choosing a skill people already pay for, one product to one avatar on one channel (yt-jfW6gL6hKhk); selling time one-to-one at a high price early (yt-uWdIgftpvBI); payment terms and outcome-based pricing (yt-rMJIOK_FgJk).",
        "hard_checks": [
            "Monthly surplus: $3,400 - $2,900 = $500.",
            "Vending route: $9,000 is 82% of savings; payback at the claimed $700 a month is about 12.9 months; replacing $3,400 a month would need about 5 routes, which the savings cannot fund within 18 months without more capital. The $700 is the seller's unverified claim.",
            "Store: $6,000 inventory is 55% of savings before ads or returns.",
            "Dental lead-generation service: low capital, uses the person's direct experience of the buyer.",
        ],
        "constraint_checks": [
            "About 20 hours a week while employed.",
            "$11,000 savings, $500 monthly surplus.",
            "Goal: replace a $3,400 monthly take-home within 18 months.",
            "User asked to pick one.",
        ],
        "defensible_answers": [
            "Dental lead-generation/appointment-setting service, with a 90-day plan to sign the first offices (possibly the current employer's network), priced per booked patient or per month, upfront or outcome-based.",
            "Vending route only with strong due diligence (verify statements, visit machines) and an honest note that it will not replace salary in 18 months alone.",
            "Online store only with a plan to test demand before buying full inventory.",
        ],
        "credit_signals": [
            "Uses the savings and payback arithmetic.",
            "Flags the seller's unverified income claim.",
            "Gives a concrete 90-day plan with customer acquisition steps.",
            "Notes employment conflicts (for example soliciting the employer's competitors or patients) if relevant.",
        ],
        "source_support": [
            ev("yt-jfW6gL6hKhk", "0:32", "The first step is that we have to cut all costs, so that we can take more risk."),
            ev("yt-jfW6gL6hKhk", "3:14", "Your nine-to-five job is not killing your dreams."),
            ev("yt-jfW6gL6hKhk", "7:34", "go find what people are already paying for"),
            ev("yt-jfW6gL6hKhk", "8:09", "you want to sell one product or service to one avatar on one channel until you make $1 million."),
            ev("yt-uWdIgftpvBI", "1:06", "one of the simplest ways to create an expensive offer is to sell your time one-on-one, even if it's unscalable."),
            ev("yt-rMJIOK_FgJk", "3:17", "third tier, which is you pay, then I work."),
            ev("yt-rMJIOK_FgJk", "6:37", "So if I say you don't pay me until you're top three in Google Maps rankings"),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-yc-01", "vault": "yc", "domain": "startup_decision_mvp",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Business and numbers invented. Principles drawn from: deleting most features built with coding agents, building what users pull (yt-rQtrzBcf_Us); launch quickly, keep the user and problem and fix the solution (yt-1hHMwLxN6EM); slow buyers such as hospitals (web-19ac0b6d18d2).",
        "hard_checks": [
            "Runway: $210,000 / $22,000 is about 9.5 months.",
            "Pilot signal: 1 of 3 clinics uses one feature (note-writing) daily; the other two logged in twice each.",
        ],
        "constraint_checks": [
            "Decision this week; plan for 8 weeks.",
            "Two engineers; no stated sales or clinical staff.",
        ],
        "defensible_answers": [
            "Cut to note-writing (the feature with daily use), charge for it, and put it into many more clinics now.",
            "Cut down and go deeper with the three pilots first to find why two clinics did not adopt, then expand.",
            "Hospitals only with a credible argument about access and sales cycle given 9.5 months of runway; weaker but not automatically wrong.",
        ],
        "credit_signals": [
            "Treats the one daily-used feature as the signal.",
            "Proposes charging early to test value.",
            "Addresses runway when weighing a long-cycle market.",
            "Gives a concrete 8-week plan with measurable targets.",
        ],
        "source_support": [
            ev("yt-rQtrzBcf_Us", "1:06", "it is so much easier to build features that for me to launch that, I had to delete 80% of the features that I built in the MVP."),
            ev("yt-rQtrzBcf_Us", "4:19", "it should be because users are pulling you towards building more stuff, I think, and not because Codex could crank it out."),
            ev("yt-rQtrzBcf_Us", "6:27", "Less features, more usage."),
            ev("yt-1hHMwLxN6EM", "1:41", "launch something bad quickly"),
            ev("yt-1hHMwLxN6EM", "3:19", "hold the problem you're solving tightly, hold the customer tightly, hold the solution you're building loosely."),
            ev("yt-1hHMwLxN6EM", "3:53", "keep the mechanic. Keep the problem."),
            ev("web-19ac0b6d18d2", None, "Whereas selling to customers like hospitals and school districts is like walking through mud."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-yc-02", "vault": "yc", "domain": "pricing_customer_segment",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: selling to early-stage companies with usage pricing, slow enterprise sales, pricing cheaply at first without losing the payment signal (web-19ac0b6d18d2); depending on one big customer and custom work (yt-7TU636F_yVQ); growth rate as the key number (web-278ac10fa14b).",
        "hard_checks": [
            "Runway: $640,000 / $45,000 is about 14.2 months.",
            "Current monthly revenue: 30 x $210 = $6,300.",
            "If 15% monthly growth continued: about $33,700 after 12 months (x5.35) and about $44,600 after 14 months; break-even at $45,000 would arrive around month 15, just past runway. So the self-serve path likely still needs a raise, which the growth rate would support.",
            "Enterprise: $90,000 a year is $7,500 a month, and only after a 6 to 7 month procurement plus the SOC 2 and on-prem work; roughly 7 months of runway left when the first payment could start.",
        ],
        "constraint_checks": [
            "Build capacity for only one of the two roadmaps this year.",
            "14 months of runway.",
        ],
        "defensible_answers": [
            "Focus on self-serve startups, keep usage pricing (possibly with a minimum or volume tiers), and keep enterprise conversations warm without building custom requirements.",
            "Pursue the two logistics companies if they can be signed with paid pilots or prepayment that fund SOC 2, with a clear stop date.",
            "Hybrid only if it avoids the custom on-prem build this year.",
        ],
        "credit_signals": [
            "Does runway and growth arithmetic.",
            "Notes the risk that 15% growth will not persist.",
            "Discusses pricing concretely (usage tiers, minimums, enterprise price floor).",
            "Addresses the risk of custom work for one customer.",
        ],
        "source_support": [
            ev("web-19ac0b6d18d2", None, "But if you get them as customers at the very beginning and you charge based on usage, your revenues will grow at startup rates."),
            ev("web-19ac0b6d18d2", None, "Now you're doing enterprise sales, which takes forever and is notoriously not a domain where the best product wins."),
            ev("web-19ac0b6d18d2", None, "I generally advise startups to sell as cheaply as they need to at first; get all the users, then worry about your margins."),
            ev("web-19ac0b6d18d2", None, "if you give away too much, you lose the signal that customers send by paying you."),
            ev("yt-7TU636F_yVQ", "12:18", "you're over the barrel of um doing custom for them."),
            ev("yt-7TU636F_yVQ", "12:18", "You might be moving further away from product market fit without realizing it."),
            ev("web-278ac10fa14b", None, "Now you see why, when I meet a founder, the first thing I ask about is their growth rate."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-yc-03", "vault": "yc", "domain": "startup_decision_quit_job",
        "case_types": ["missing_critical_input"],
        "inspiration": "Synthetic case. Details invented. Principles drawn from: growth rate as the first question and word of mouth as its cause (web-278ac10fa14b); getting people to use the product (yt-1hHMwLxN6EM); solo founders and losing faith (yt-s1YszjhzQ6U).",
        "missing_critical_inputs": [
            "Whether people keep using the app: weekly or monthly active couples and retention by sign-up cohort. 1,400 sign-ups from three viral posts says little about whether the product works.",
            "Organic growth rate since the spikes, and whether anyone pays or would pay.",
        ],
        "how_good_answers_handle_it": "Name the missing usage and growth numbers and give a decision rule tied to them (for example quit only if a meaningful share of couples still use it weekly after a month and sign-ups keep growing without new viral posts), or ask for them before answering. An unconditional yes or no based on sign-up count alone should score lower. A yes or no is still expected once the rule is stated.",
        "hard_checks": [
            "9 months of expenses saved; the promotion requires a 12-month commitment, decision due at month end.",
        ],
        "constraint_checks": [
            "User asked for a yes or no.",
            "Solo founder.",
        ],
        "defensible_answers": [
            "Conditional yes: quit if retention and organic growth clear stated thresholds; otherwise take the promotion and keep building.",
            "Take the promotion and keep building with explicit milestones, if the answer explains why the evidence is not yet strong enough.",
            "Quit, if the answer addresses the runway and the missing retention evidence with a test plan for the first months.",
        ],
        "credit_signals": [
            "Separates sign-ups from active use.",
            "Asks for or conditions on retention and growth.",
            "Addresses the no-cofounder risk and the 9-month runway.",
            "Notices the one-year commitment cost of the promotion.",
        ],
        "source_support": [
            ev("web-278ac10fa14b", None, "Now you see why, when I meet a founder, the first thing I ask about is their growth rate."),
            ev("web-278ac10fa14b", None, "To grow at a consistent rate every month, you have to make something so good that people tell their friends about it."),
            ev("yt-1hHMwLxN6EM", "2:14", "Get anyone using your product."),
            ev("yt-s1YszjhzQ6U", "2:11", "the number one cause of death when you're a founder is it just sort of dies on the vine and you run out of hope and you give up on it."),
            ev("yt-s1YszjhzQ6U", "3:14", "there is no way you can get around not having someone to talk to all the time to bounce ideas off of."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-yc-04", "vault": "yc", "domain": "customer_acquisition_launch",
        "case_types": [],
        "inspiration": "Synthetic case. Details invented. Principles drawn from: press driving few sign-ups, telling your own story, outbound worth replying to (yt-7TU636F_yVQ); getting customers before a press launch (yt-1hHMwLxN6EM); fewer, better conversations and distinctive writing (yt-rQtrzBcf_Us).",
        "hard_checks": [
            "$36,000 = 3 months x $12,000 = 90 customer-months at $400. If customers stayed 24 months, the agency would need to produce about 4 retained customers to recover its fee in revenue (36,000 / (400 x 24) = 3.75). Customer lifetime is not given, so this is an illustration.",
        ],
        "constraint_checks": [
            "Recommend one plan for 3 months.",
            "Launch planned next month.",
        ],
        "defensible_answers": [
            "Skip the tech-press agency; put the money into founder-led outreach in the three metros and trade-association presence, with content as support.",
            "A smaller, trade-press-focused PR effort aimed at subcontractors can be defensible if justified by how the buyers find vendors.",
            "Hire the agency only with a measurable target and a plan to track sign-ups from coverage; weak but acceptable if the measurement is real.",
        ],
        "credit_signals": [
            "Matches the channel to where subcontractors actually are.",
            "Uses the existing 15 customers (referrals, case studies).",
            "Sets measurable targets for the 3 months.",
        ],
        "source_support": [
            ev("yt-7TU636F_yVQ", "20:28", "And it is shocking how little um getting press helps a startup."),
            ev("yt-7TU636F_yVQ", "21:38", "tell your own story"),
            ev("yt-7TU636F_yVQ", "22:12", "when I read your email outbound, would you if you received this email, would you want to kill the company who sent it or would you want to respond?"),
            ev("yt-1hHMwLxN6EM", "10:39", "Let's push the press launch off and let's push the get any customers launch really really soon."),
            ev("yt-rQtrzBcf_Us", "5:22", "a smaller number of high-quality conversations where you really listen"),
            ev("yt-rQtrzBcf_Us", "10:15", "Versus if you take the time to write really unique stuff, you can build a following."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-yc-05", "vault": "yc", "domain": "hiring",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Numbers invented. Principles drawn from: hiring pipelines, competing with other startups rather than big companies, selling responsibility, same-day offers, hiring effort on par with sales (yt-7TU636F_yVQ); small teams with agents (yt-eRrc1pUY5oU).",
        "hard_checks": [
            "Agency fee: 25% x $185,000 = $46,250 per hire, $92,500 for two (about 3.1% of the $3M seed).",
            "Raising cash to $240,000: +$55,000 a year per hire, +$110,000 a year for two.",
            "Funnel: 7 interviews, 3 offers, 0 accepts. Founders spend about 2 hours a week on recruiting.",
        ],
        "constraint_checks": [
            "Two senior backend roles; competing offers at about 2x cash.",
        ],
        "defensible_answers": [
            "Fix the process first: far larger pipeline, much more founder time, faster offers, target candidates who want early-stage responsibility rather than big-lab cash; adjust comp moderately.",
            "Raise cash and keep equity meaningful if the candidates they want really price on cash; acceptable with the cost math.",
            "Hire one and lean on coding agents for the rest, if the answer argues what the agents can and cannot cover.",
            "Agency or overseas contractors with clear quality and management tradeoffs.",
        ],
        "credit_signals": [
            "Diagnoses the pipeline size and founder time, not only compensation.",
            "Does the cost math for the options.",
            "Recommends an explicit option.",
        ],
        "source_support": [
            ev("yt-7TU636F_yVQ", "15:01", "the biggest issue is they don't have a pipeline."),
            ev("yt-7TU636F_yVQ", "16:40", "you're probably competing against that other early stage startup, not Google"),
            ev("yt-7TU636F_yVQ", "16:40", "You can tell them about all the responsibility they're going to have"),
            ev("yt-7TU636F_yVQ", "17:45", "you probably should be putting as much effort into that as you are into sales."),
            ev("yt-7TU636F_yVQ", "18:51", "if someone was good, we had a printed and signed offer letter", *SEIBEL_SOCIALCAM),
            ev("yt-eRrc1pUY5oU", "21:56", "When they crossed $15 million in annualized revenue, they were 15 people."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
    {
        "id": "advice-yc-06", "vault": "yc", "domain": "startup_decision_idea_choice",
        "case_types": ["tradeoff_synthesis"],
        "inspiration": "Synthetic case. Details invented. Principles drawn from: low ambition and crowded AI sales tools, credible low-leap pitches rooted in what you know (yt-ozhRhElbVcI); slow buyers and starting with a faster-deciding subset (web-19ac0b6d18d2); understanding users deeply (web-278ac10fa14b).",
        "hard_checks": [
            "14 months of savings against utility procurement that needs council approval: a plan that depends on closing municipal contracts in months 1 to 6 without a way around procurement does not fit the runway.",
        ],
        "constraint_checks": [
            "Pick one idea.",
            "First 6 months of de-risking.",
        ],
        "defensible_answers": [
            "Idea B, starting with buyers that decide faster (for example consulting engineers serving utilities, private water operators, or paid pilots under small-purchase limits) and using domain expertise.",
            "Idea A, with a sharp differentiation thesis and a plan to convert the LOIs into paying customers quickly; acceptable if it addresses competition.",
            "Either, if the answer weighs the tradeoff (speed of feedback and funding vs domain advantage and competition) and gives concrete 6-month milestones.",
        ],
        "credit_signals": [
            "Weighs domain expertise against crowded competition.",
            "Addresses the slow-buyer problem concretely.",
            "Questions the strength of LOIs from friends.",
            "Makes an explicit choice.",
        ],
        "source_support": [
            ev("yt-ozhRhElbVcI", "0:00", "Whereas building the 17th AI SDR might raise you your $2 million seed round"),
            ev("yt-ozhRhElbVcI", "2:13", "Almost nothing in this video we're going to talk about is relevant to a un-venture funded company."),
            ev("yt-ozhRhElbVcI", "13:08", "The ambition has to be combined with a simple pitch"),
            ev("yt-ozhRhElbVcI", "14:43", "make very simple low leap of faith arguments on how you'll be able to do it."),
            ev("web-19ac0b6d18d2", None, "Whenever I meet a startup selling to customers like that, I ask if there's some way they could at least start by selling to a subset of the market that decides faster."),
            ev("web-278ac10fa14b", None, "The key to starting a successful startup is to understand some group of users so well that you can make exactly what they want."),
        ],
        "judging_notes": COMMON_JUDGING,
    },
]


def gold_questions():
    out = {}
    for vault, path in GOLD.items():
        for g in yaml.safe_load(Path(path).read_text(encoding="utf-8"))["questions"]:
            out[g["id"]] = (g["question"], g["category"])
    return out


def main():
    # Question text and category always come from the gold files, unchanged.
    gq = gold_questions()
    for d in DIAG:
        d["question"], cat = gq[d["id"]]
        assert cat == d["category"], d["id"]
    dq = [{"id": d["id"], "vault": d["vault"], "question": d["question"], "category": d["category"]} for d in DIAG]
    items = []
    for d in DIAG:
        item = dict(d)
        item["gold_file"] = GOLD[d["vault"]]
        item["gold_sha256"] = hashlib.sha256(Path(GOLD[d["vault"]]).read_bytes()).hexdigest()
        items.append(item)
    dr = {
        "meta": {
            "built": "2026-10-19",
            "scope": "Source-audited keys for the 12 existing ask12 diagnostic questions.",
            "sources_read": "Raw vault files under /home/mateusz/wwxd-lab/vaults/{hormozi,yc}/raw and the two ask12 gold files only.",
            "quote_rule": "Quotes are verbatim caption or article text after collapsing whitespace, inside the segment named by timestamp. Caption spelling errors are kept.",
            "key_status_values": {
                "confirmed_expanded": "gold stance correct; key adds missing points",
                "confirmed_with_correction": "gold stance correct; a detail is corrected",
                "confirmed_speaker_caveat": "gold content correct; speaker attribution is partly inferred",
                "confirmed_speaker_inferred": "gold correct; attribution rests on content inference",
                "confirmed_with_interpretation_flag": "gold correct; one gold claim is inference, not source text",
                "corrected_context": "gold direction correct; context and one quantified claim corrected",
                "corrected": "gold stance or evidence was wrong or empty; replaced from raw",
            },
        },
        "items": items,
    }
    aq = [{"id": i, "vault": v, "domain": dom, "question": q} for i, v, dom, q in ADVICE_Q]
    ae = {
        "meta": {
            "built": "2026-10-19",
            "private": "Not shown to answering models or to primary practical judges.",
            "scope": "Private source support, hard arithmetic and constraint checks, and the range of defensible answers for the 12 advice cases. No case has a single mandatory recommendation.",
            "synthetic": "Every case is a source-inspired synthetic scenario. Businesses, people and numbers are invented; only the principles come from the raw sources.",
        },
        "cases": ADVICE_EV,
    }
    for name, data in (
        ("diagnostic-questions.json", dq),
        ("diagnostic-reference.json", dr),
        ("advice-questions.json", aq),
        ("advice-evidence.json", ae),
    ):
        (FX / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
