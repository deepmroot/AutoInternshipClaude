# Batch runs: one subagent per posting

Read this when the user asks to work through jobs.txt or gives several links. Everything in SKILL.md still applies; this file says how to split the work.

## Why subagents

Every model call re-reads the whole conversation. Done in one conversation, a batch piles up: on 2026-11-04 a five-job Fill all run grew to about 476,000 tokens, five resumes plus every page of every form, and each click on the last form paid to re-read all of it (214 calls, $18.82). A subagent starts fresh and hands back only a short summary, so each posting costs about what it would alone, and this conversation stays small.

Use the subagent tool (Task or Agent, type `general-purpose`). Without one, run the batch yourself as in "Without subagents" at the end.

## The run

1. **Fetch the queue** in one call (SKILL.md, "Batch runs"). Skip postings the tracker already has, as in step 1. Order the rest by deadline, soonest first, then postings with no deadline, newest first, since many internships review applications as they arrive.
2. **Tailor**: one subagent per posting, with the tailoring prompt below. Postings the fetch got can be tailored by several subagents at once, since each touches only its own job folder. Ones it couldn't get are read in the browser, so run those one at a time. You don't read tailoring.md, overleaf.md or the master yourself; the subagents do.
3. **Checkpoint** (step 4), from the summaries, one short block per posting. Read a drafts file only to show its answers, and not at all in auto mode.
4. **Fill**: one subagent per application, **one at a time**, because they share the user's browser. Each fills its form up to the review page or the first thing that needs the user, writes application-record.md and the tracker row, and leaves its tab open. If the first one replies NO BROWSER, fill them all yourself in this conversation, as in "Without subagents".
5. **Hand-off**: one message for the whole batch, built from the summaries: one line per tab (company and role, and what's needed: "sign in to Workday", "attach C:\\...\\Maya_Chen_Resume_Northwind.pdf"), then the questions from every form, grouped so one answer covers every form that asks it. This way the user is interrupted once or twice for the whole batch, not once per application. In Submit mode without auto, also show the written answers the filling subagents drafted on the form (Workday's and most other sites' questions appear only there): read them from each record's "Written answers" section. The user must see them before anything is submitted, so send this message even when nothing else needs the user, and wait for their reply.
6. **Continue**: when the user says they're done, run the filling prompt again for each application, one at a time, with what the user did and their answers. Each picks up from its application-record.md in the same tab. Repeat once more if new steps came up. A summary that says the tab group closed gets the same: continue from the record in a new tab (filling.md, "If the tab group disappears"), never a fill from the start.
7. **Submit** (Submit mode only): do this yourself, never in a subagent, because the mode comes from the user's own words to you, and so does the rule of one click. For each application whose summary says the check passed (or failed only on check 3, the written answers, which the user has since seen in the hand-off and accepted), switch to its tab, make sure it's on the review page, and follow "Submitting" in submitting.md: click Submit once, wait for the confirmation, then update the record's status line and the tracker row.
8. **Report** once, one line per posting (step 8), and move processed links in jobs.txt below the `# done` line, editing the file in place. If the summaries list answers worth saving, offer once to save them to profile.json (`references/profile.md`).

If one posting hits a wall the user can't clear in the hand-off (a broken page, a closed posting, an assessment), its row is `Needs you`; move on.

## Tailoring prompt

Fill in the `<...>` parts and send only this; the subagent reads the rest from the skill.

```
You're tailoring one internship application in a batch run by the internship-application skill.
Read <skill>/SKILL.md, then <skill>/references/tailoring.md (and references/overleaf.md if the master is .tex),
with your file-reading tool, not cat (long command output gets cut off).
Do SKILL.md steps 1 to 3 for this posting only (the tracker check is already done): save job-posting.md, check eligibility, create the job folder,
tailor, check and save the resume, write changes.md, and draft any written answers into <scratch>/answers/<NN>.md.
Don't open the application form, don't change the tracker, and don't start subagents of your own.
- Posting: <fetched file> | <link: open it in a new tab of your own, read it, close the tab>
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
- Job folder: <folder>  Application link: <url>  Resume: <PDF path>  Answers: <drafts file, or none>
- Profile: <folder>/profile.json  Tracker: <folder>/tracker.xlsx
- Tab: <open a new tab of your own | continue in tab <id>: the user has since <what they did>, and answered: <answers>>
The browser tools (claude-in-chrome) may be deferred: load them with your tool search first. Only if none
exist after that, stop and reply only "NO BROWSER".
Reply with only these lines:
Status: review page | needs the user | stopped: <why>
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
