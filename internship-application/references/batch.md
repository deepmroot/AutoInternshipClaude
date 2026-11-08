# Batch runs: one subagent per posting

Read this when the user asks to work through jobs.txt or gives several links. Everything in SKILL.md still applies; this file says how to split the work.

## Why subagents

Every model call re-reads the whole conversation. Done in one conversation, a batch piles up: on 2026-11-04 a five-job Fill all run grew to about 476,000 tokens, five resumes plus every page of every form, and each click on the last form paid to re-read all of it (214 calls, $18.82). A subagent starts fresh and hands back only a short summary, so each posting costs about what it would alone, and this conversation stays small.

Subagents also make a batch faster, because forms in separate tabs can fill at the same time. In Claude Code on 2026-11-06 and 07, one conversation filled forms one after another at about 9 minutes each, roughly half of it waiting on the browser and half deciding the next step.

Use the subagent tool (Task or Agent, type `general-purpose`). Without one, run the batch yourself as in "Without subagents" at the end.

## The run

1. **Fetch the queue** in one call (SKILL.md, "Batch runs"). Skip postings the tracker already has, as in step 1. Order the rest by deadline, soonest first, then postings with no deadline, newest first, since many internships review applications as they arrive.

   **At most two per company.** Recruiters see every application one person sends their company in one system, so many roles at once reads as applying to anything. For each company, count its postings in this batch plus its tracker rows from the last 5 days (the user's choice) (`in_tracker` in the fetch result, by `date_added`; Skipped rows don't count). Keep at most two in all: the ones whose titles fit the user best (their major and skills, and the kind of role they asked for), the earlier deadline on a tie. For a posting the fetch couldn't read, take the company from its jobs.txt note or its link. Leave the rest in jobs.txt above `# done`, adding `held: 2 per company` to the line's note if it isn't there yet, so a later batch picks them up once the earlier applications are 5 days old. If the user asks for more from one company ("all the Northwind roles"), use their number.
2. **Tailor**: one subagent per posting, with the tailoring prompt below, all started at once, since each touches only its own job folder. Postings the fetch couldn't get are read in the browser, so those follow "Sharing the browser" below. You don't read tailoring.md, overleaf.md or the master yourself; the subagents do.
3. **Checkpoint** (step 4), from the summaries, one short block per posting. Read a drafts file only to show its answers, and not at all in auto mode. Add one line for the postings held back by the company limit (company: roles), so the user can swap one in or say to do them all. In auto mode they stay held.
4. **Fill**: one subagent per application, with the filling prompt below, **all at once**, following "Sharing the browser". Start every one that isn't queued behind a sign-in in one message, then start each queued one as the form ahead of it replies (if your subagent tool waits for all of them, start the queued ones in the next message). Each fills its form up to the review page or the first thing that needs the user, writes application-record.md and the tracker row (tracker.py waits its turn, so rows logged at the same moment are all kept), and leaves its tab open. If they reply NO BROWSER, fill them all yourself in this conversation, as in "Without subagents".
5. **Hand-off**: one message for the whole batch, built from the summaries: one line per tab (company and role, and what's needed: "sign in to Workday", "attach C:\\...\\Maya_Chen_Resume_Northwind.pdf"), then the questions from every form, grouped so one answer covers every form that asks it. Before you send it, check each question against profile.json yourself (every field and `savedAnswers`, by meaning, as in filling.md): send the ones it answers straight back to their subagents (step 6) instead of asking. This way the user is interrupted once or twice for the whole batch, not once per application. In Submit mode without auto, also show the written answers the filling subagents drafted on the form (Workday's and most other sites' questions appear only there): read them from each record's "Written answers" section. The user must see them before anything is submitted, so send this message even when nothing else needs the user, and wait for their reply.
6. **Continue**: when the user says they're done, run the filling prompt again for each application, all at once as in step 4, with what the user did and their answers. Each picks up from its application-record.md in the same tab. Repeat once more if new steps came up.
7. **Submit** (Submit mode only): do this yourself, never in a subagent, because the mode comes from the user's own words to you, and so does the rule of one click. For each application whose summary says the check passed (or failed only on check 3, the written answers, which the user has since seen in the hand-off and accepted), switch to its tab, make sure it's on the review page, and follow "Submitting" in submitting.md: click Submit once, wait for the confirmation, then update the record's status line and the tracker row.
8. **Report** once, one line per posting (step 8), and move processed links in jobs.txt below the `# done` line, editing the file in place. Held postings get one line together at the end ("Held, 2 per company: ...") and stay above `# done`. Save the answers the summaries list under `To save:` to profile.json without asking (`references/profile.md`), and say in one line what you saved.

If one posting hits a wall the user can't clear in the hand-off (a broken page, a closed posting, an assessment), its row is `Needs you`; move on.

## Sharing the browser

Subagents in one conversation share its Chrome tab group, so several can work at once, each in its own tab:

- **Make the group yourself first.** Before the first subagent that uses the browser, load the browser tools (tool search) and call `tabs_context_mcp` with `createIfEmpty: true`. Make sure the group has a tab of yours (the one it opens, or a new one) and leave that tab open until the batch ends. Subagents that start at the same time would each make a group of their own, and a group ends when its last tab closes, which would cut off the rest.
- **No limit on how many at once.** Start every application that's ready, except the ones the next rule queues. Each form spends about half its time waiting on the browser, so running them side by side is what makes a batch fast. On 2026-11-07, two separate sessions filled forms in the user's Chrome at the same time without getting in each other's way, and the user then removed the earlier limit of three. If the user asks for a limit, use their number.
- **One at a time per sign-in.** Never run two at once that use the same account: two forms on one Workday site (such as `northwind.wd5.myworkdayjobs.com`), or two on one company's own careers site. The tabs share the sign-in, so signing in, signing out or timing out in one tab changes the other mid-form. Queue the second behind the first. Boards that don't sign you in (Greenhouse, Lever, Ashby) can run forms for different companies at the same time.
- **If they get in each other's way** (two subagents report screenshots failing, clicks that didn't take, or their own tab missing), let the running ones finish, then fill the rest one at a time.
- **If the tab group disappears** (usually because the user closed or moved its tabs), each running subagent stops with `stopped: tab group lost`. Wait for the ones still running, make the group again as above, and send each the filling prompt with the third kind of `Tab:` line: a new tab, continuing from application-record.md. Never fill from the start: the record lists the pages and fields already done (filling.md, "If the tab group disappears").

## Tailoring prompt

Fill in the `<...>` parts and send only this; the subagent reads the rest from the skill.

```
You're tailoring one internship application in a batch run by the internship-application skill.
Read <skill>/SKILL.md, then <skill>/references/tailoring.md (and references/overleaf.md if the master is .tex),
with your file-reading tool, not cat (long command output gets cut off).
Do SKILL.md steps 1 to 3 for this posting only (the tracker check is already done): save job-posting.md, check eligibility, create the job folder,
tailor, check and save the resume, write changes.md, and draft any written answers into <scratch>/answers/<NN>.md.
Don't open the application form, don't change the tracker, and don't start subagents of your own.
- Posting: <fetched file> | <link: open it in a new tab of your own, read it, close that tab; pass its id on every browser action and leave other tabs alone>
- Job-search folder: <folder>  Master resume: <path>  Profile: <folder>/profile.json
- Scratch space: <scratch>/<NN>   Today: <YYYY-MM-DD>
- Master template check: <add --check-template | already done, leave it out>
Reply with only these lines:
Posting: <Company> - <Role>, deadline <date or none>
Eligibility: ok | skip: <reason>
Folder: <job folder>
Resume: <PDF file name>; page <filled, or N lines free and why>
Changes: <two or three short lines>
Gaps: <one line>
Answers: <drafts file, or none>
Problems: <none, or what needs the user>
```

For a posting that comes back `skip`, you log it `Skipped` with its reason (step 2, in auto mode) or show it at the checkpoint. Give `--check-template` only to the first tailoring subagent, since the master is the same for all.

## Filling prompt

```
You're filling one internship application in a batch run by the internship-application skill.
Read <skill>/SKILL.md and <skill>/references/filling.md (and references/submitting.md unless the mode is
Review), with your file-reading tool, not cat (long command output gets cut off).
Mode: <Review | Fill all | Submit>. Never click Submit in any mode: in Submit mode, fill as in Fill all,
then run "The check before Submit" from submitting.md on the review page and report the result.
The user <saw | didn't see (auto)> the drafted answers.
Do SKILL.md steps 5 to 7 for this application only: fill the form in the user's browser up to the review
page or the first thing that needs the user, add each page's fields to application-record.md as you go,
and log the tracker row (Ready to submit, or Needs you with the reason). Don't start subagents of your own.
Fill everything you can. Before you list a question, check profile.json (every field and savedAnswers, by meaning,
as filling.md says): list only what nothing there, in the master resume or in the posting answers. Don't edit
profile.json; put new answers under To save.
- Job folder: <folder>  Application link: <url>  Resume: <PDF path>  Answers: <drafts file, or none>
- Profile: <folder>/profile.json  Tracker: <folder>/tracker.xlsx
- Tab: <open a new tab of your own | continue in tab <id>: the user has since <what they did>, and answered: <answers>
  | open a new tab of your own and continue from application-record.md: the tab group was lost>
The browser tools (claude-in-chrome) may be deferred: load them with your tool search first. Only if none
exist after that, stop and reply only "NO BROWSER".
Other subagents may be filling forms in other tabs of this browser at the same time. Pass your tab's id on
every browser action, and never switch to, close or use any other tab. If your tab is gone but the group is
still there, open a new tab and continue from application-record.md. If the group itself is gone ("This
session's tab group no longer exists"), don't make a new one, since the others share it: stop and reply with
Status: stopped: tab group lost.
Reply with only these lines:
Status: review page | needs the user | stopped: tab group lost | stopped: <why>
Tab: <id> <url>
For the user: <one line, or none>
Questions: <each question word for word, with its choices, or none>
Written answers: <none, or "in application-record.md" for ones you drafted on the form>
Agreed for you: <short list, or none>
To save: <answers the user gave that will come up again, for profile.json, or none>
Submit check: <passed | failed: which> (Submit mode only)
```

## Without subagents

Do the same run in this conversation: tailor everything first (steps 1 to 3 for each posting), one combined checkpoint, then fill each application in its own tab up to the point where it needs the user, one hand-off for the whole batch, continue each form when the user is done, record and log each, and report once. It costs more, because this conversation re-reads every resume and form page on every call.
