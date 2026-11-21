# Seedha AI playbook

@seedha.ai: AI, made simple, for Indian students and early-career people. English-led. No hype.
Brand: Ink Indigo #16164A, Haldi #F5B800, Chalk #F4F6FA. Fonts: Instrument Serif and Instrument Sans (tools/fonts).

## Aim and scoreboard
Aim: grow @seedha.ai to its full potential as India's simplest AI-for-students page. Learn, understand, improvise, repeat, twice a week.
- **North star:** followers.
- **Leading signals per reel:** reach, shares per 1,000 reach, saves per 1,000 reach, follows gained. Reach shows the hook and format work; shares and saves show the value; follows show the page promise works.
- **Weekly target:** beat last week's median reach per reel and shares per 1,000 reach. If two weeks in a row miss, change the format, not just the topic.
- **Milestones:** first 100 followers, then 1,000 (trial reels and carousels come back here), then 10,000.
- Every decision cites a number from metrics/. Gut feel is not a reason.

## Cadence
- Daily 8:41 PM IST: report (posts on time, numbers, one fix).
- Sunday 11:13 AM IST: full analysis (ours, competitors, news), then a 21-reel batch, queue kept 10+ days ahead.
- Wednesday 11:13 AM IST: mid-week tune-up. Re-read the latest numbers and replace queued-but-unposted reels for the next 4 days if the data clearly says a format or topic loses.

## The loop
1. **Measure.** `metrics/YYYY-MM-DD.json` is written every day at 8:30 PM IST by the publisher (followers, and reach, views, saves, shares, likes and comments per post from Instagram Insights).
2. **Understand.** Compare posts by format, hook and topic. Look at reach first, then sends (shares) per reach, saves per reach and follows.
3. **Research.** Competitor AI-education pages and this week's AI news that matters to Indian students. Prefer official sources and cite them in captions.
4. **Create.** Make the next 7 days (21 reels): a = strongest format, b = second format, c = the week's experiment. Double down on winners, drop losers.
5. **Queue** at least 10 days ahead, so one missed week never stops posting.

## Schedule
Three reels a day from 3 Dec 2026: 12:30 PM IST (slot a), 7:00 PM IST (slot b), 9:30 PM IST (slot c, Indian prime time). Folders: `queue/YYYY-MM-DD-a|b|c/` with `post.json` (`{"type":"reel","files":["reel.mp4"],"caption":"..."}`) and the media file.
The publisher keeps itself running (each run starts the next). It prepares 60 minutes early and publishes on the minute.

## What the data says so far
- 18 Nov 2026, 0 followers: the reel reached 57 people, and 4 feed posts (carousels and statics) reached 0 to 1. **With no followers, only reels reach anyone. Post reels only until the page has an audience** (revisit at about 1,000 followers).
- Instagram ranks reels on watch time, then sends per reach, then likes per reach. Sends matter most for reaching non-followers. So every reel needs a hook in the first second, a payoff before 12 seconds, and a reason to send it to a friend.

## Competitors
Similar pages to track weekly (fill in and keep updated: handle, followers, what their top reels do):
- (to be filled by the weekly run)

## Formats (tools/)
- **Prompt-fix reel** (`audio_gen.py` + `reel_gen.py`, spec like `tools/specs/example_prompt_reel.json`): hook, bad prompt, fix (3 items), better prompt, result, CTA. 15 s with original scored audio. Keep h1 under 30 characters (or 3 lines), p2 and o2 under about 100 characters each, so the payoff lands by about 12 s.
- **Slide reel** (`carousel.py` with `REEL=1` + `slides_reel.py`, spec like `tools/specs/example_slides.json`): cover plus 3 slides plus CTA, with auto-advance, a progress bar and an original beat. About 16 s. Use it for news, lists and cheat sheets.

## How to make a batch
```
cd tools && mkdir -p tmp rs reels
python3 audio_gen.py specs/rX.json && python3 reel_gen.py specs/rX.json && \
  ffmpeg -i tmp/rX_v.mp4 -i tmp/rX.wav -c:v copy -c:a aac -shortest -movflags +faststart reels/out.mp4
REEL=1 OUT=rs python3 carousel.py specs/slides.json && python3 slides_reel.py reels/out.mp4 104 0 rs/<id>/s{1..5}.jpg
```
Needs: python3, playwright + Chrome, ffmpeg, numpy, scipy, pillow.
QA every reel before queueing: pull frames at 1 s, 4 s, 9 s and 13 s and check that no text overflows or overlaps and that the typing finishes before the result.

## Caption rules
Line 1 is the hook. Give the useful prompt in full so people copy and save it. Name a source for any fact or number. End by asking the reader to send it to a specific friend ("Send this to your study group"). Use 5 or 6 hashtags. No em dashes. English only.

## Never
Never like, follow or comment from the user's personal profile. Never post anything unsourced about money, jobs or government schemes. Never put tokens in the repo; the repo is public.

## Experiment log
| Week | Change | Result |
|---|---|---|
| 16 to 18 Nov | Mixed reel, carousel and static | Feed posts reached 0. Reel reached 57. |
| 19 to 20 Nov | All reels: prompt-fix at noon, slide reels at 7 PM | Prompt-fix reels reached 26 to 57; slide reels 9 to 13; static reels 9. 0 shares, 0 follows. Prompt-fix wins. |
| 3 Dec onward | 3 reels a day; more prompt-fix; slot c experiments | (fill from metrics) |
