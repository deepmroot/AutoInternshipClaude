# Batch runs: one subagent per posting

Read this when the user asks to work through jobs.txt or gives several links.

Use the subagent tool (Task or Agent, type `general-purpose`). Without one, follow "Without subagents" at the end.

- **Keep this conversation small.** Never fill forms or read form pages here. Your only browser work is making the tab group and, in Submit mode, clicking Submit.
- **Models.** Start filling subagents with the `sonnet` model when your subagent tool lets you choose (steps 4 and 6). Tailoring subagents keep the default model.

## The run

1. **Fetch the queue** in one call (SKILL.md, "Batch runs"). Skip postings the tracker already has. Order the rest by deadline, soonest first, then those with no deadline, newest first.

   **At most two per company.** For each company, count its postings in this batch plus its tracker rows from the last 5 days (`in_tracker`, by `date_added`; Skipped rows don't count). Keep at most two: the titles that fit the user best (major, skills, the kind of role they asked for), the earlier deadline on a tie. For a posting the fetch couldn't read, take the company from its jobs.txt note or link. Leave the rest in jobs.txt above `# done`, adding `held: 2 per company` to the line's note if it isn't there yet. If the user asks for more from one company ("all the Northwind roles"), use their number.
2. **Tailor**: one subagent per posting with the tailoring prompt, all started at once. Postings the fetch couldn't get are read in the browser, so follow "Sharing the browser" for those. Don't read tailoring.md, overleaf.md or the master yourself.
3. **Checkpoint** (step 4) from the summaries, one short block per posting. Read a drafts file only to show its answers, and not at all in auto mode. Add one line for postings held by the company limit (company: roles), so the user can swap one in or say to do them all; in auto mode they stay held.
4. **Fill**: one subagent per application with the filling prompt, all at once, following "Sharing the browser". Start every one not queued behind a sign-in in one message, and each queued one when the form ahead of it replies (or in the next message, if your subagent tool waits for all). If they reply NO BROWSER, fill them all yourself, as in "Without subagents".
5. **Hand-off**: one message for the whole batch: one line per tab (company and role, and what's needed: "sign in to Workday", "attach C:\\...\\Maya_Chen_Resume_Northwind.pdf"), then the questions from every form, grouped so one answer covers every form that asks it. Before sending, check each question against profile.json yourself (every field and `savedAnswers`, by meaning); send the ones it answers straight back to their subagents (step 6) instead of asking. In Submit mode without auto, also show the written answers the subagents drafted on the form (each record's "Written answers"); send this message even when nothing else needs the user, and wait.
6. **Continue**: when the user is done, run the filling prompt again for each application, all at once as in step 4, with what the user did and their answers. Each continues from its application-record.md in the same tab. Repeat once if new steps came up.
7. **Submit** (Submit mode only): do it yourself, never in a subagent. For each application whose check passed (or failed only on check 3, written answers, which the user has since seen and accepted), switch to its tab, confirm it's on the review page, and follow "Submitting" in submitting.md.
8. **Report** once, one line per posting (step 8). Move processed links in jobs.txt below `# done`, editing in place. Held postings get one line together at the end ("Held, 2 per company: ...") and stay above `# done`. Save the answers listed under `To save:` to profile.json without asking (`references/profile.md`) and say in one line what you saved. End with one line telling the user to start a new conversation for the next batch.

A posting with a wall the user can't clear in the hand-off (a broken page, a closed posting, an assessment) is `Needs you`; move on.

## Sharing the browser

- **Make the group yourself first.** Before the first subagent that uses the browser, load the browser tools (tool search) and call `tabs_context_mcp` with `createIfEmpty: true`. Keep a tab of yours in the group open until the batch ends.
- **No limit on how many at once**, except the queueing below. If the user asks for a limit, use their number.
- **One at a time per sign-in.** Never run two forms at once on the same account: two on one Workday site (such as `northwind.wd5.myworkdayjobs.com`) or two on one company's careers site. Queue the second behind the first. Greenhouse, Lever and Ashby forms for different companies can run at the same time.
- **If they get in each other's way** (two subagents report failing screenshots, clicks that didn't take, or a missing tab), let the running ones finish, then fill the rest one at a time.
- **If the tab group disappears**, each running subagent stops with `stopped: tab group lost`. Wait for the rest, make the group again, and send each the filling prompt with the third kind of `Tab:` line. Never fill from the start.

## Tailoring prompt

Fill in the `<...>` parts and send only this.

```
You're tailoring one internship application in a batch run by the internship-application skill.
Read <skill>/SKILL.md, then <skill>/references/tailoring.md (and references/overleaf.md if the master is .tex),
with your file-reading tool, not cat. Read each file once.
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

Log a `skip` as `Skipped` with its reason (in auto mode) or show it at the checkpoint. Give `--check-template` only to the first tailoring subagent.

## Filling prompt

```
You're filling one internship application in a batch run by the internship-application skill.
Read <skill>/references/filling.md (and references/submitting.md unless the mode is Review) with your
file-reading tool, not cat. Read each file once. You don't need SKILL.md.
Mode: <Review | Fill all | Submit>. Never click Submit in any mode: in Submit mode, fill as in Fill all,
then run "The check before Submit" from submitting.md on the review page and report the result.
The user <saw | didn't see (auto)> the drafted answers.
For this application only: fill the form in the user's browser up to the review page or the first thing
that needs the user, add each page's fields to application-record.md as you go, and log the tracker row
(filling.md, "Logging the tracker row"; run scripts from <skill>). Don't start subagents of your own.
Fill everything you can. Before you list a question, check profile.json (every field and savedAnswers, by meaning):
list only what nothing there, in the master resume or in the posting answers. Don't edit profile.json; put new
answers under To save.
- Job folder: <folder>  Application link: <url>  Resume: <PDF path>  Answers: <drafts file, or none>
- Profile: <folder>/profile.json  Tracker: <folder>/tracker.xlsx
- Tab: <open a new tab of your own | continue in tab <id>: the user has since <what they did>, and answered: <answers>
  | open a new tab of your own and continue from application-record.md: the tab group was lost>
The browser tools (claude-in-chrome) may be deferred: load them with your tool search first. Only if none
exist after that, stop and reply only "NO BROWSER".
Other subagents may be filling forms in other tabs of this browser. Pass your tab's id on every browser action,
and never switch to, close or use any other tab. If your tab is gone but the group is still there, open a new
tab and continue from application-record.md. If the group itself is gone ("This session's tab group no longer
exists"), don't make a new one: stop and reply with Status: stopped: tab group lost.
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

Do the same run here: tailor everything first (steps 1 to 3 for each posting), one combined checkpoint, fill each application in its own tab up to where it needs the user, one hand-off for the batch, continue each form when the user is done, record and log each, and report once.
