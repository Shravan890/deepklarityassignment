# Assessment

## Task

You are joining a team that owns this application. Users have reported the problems listed below, but nobody has tracked down why. The app builds and runs, and most of it works. Each problem only shows up under certain conditions.

Your job is to find the cause of each reported problem, fix it at the root, and prove each fix.

Work the way you would on a real team, using an AI coding assistant such as OpenCode, Codex or Claude Code. We care less about how many you fix than about how you get there: what you understand, what you ask, what you push back on, and how you confirm a fix really works.

## Reports from users

1. Finance says that on some days the revenue in the daily report is higher than what the payment provider paid out, and a few orders show more money received than their total.
2. Products show as sold out, or nearly, while the shelf is full. Staff say it gets worse on days when many customers abandon checkout.
3. Customers in taxed regions who used a coupon say the tax on their receipt is too high. Receipts without a coupon are right.
4. Our shop in India (UTC+5:30) says sales taken in the morning do not appear in that day's report and turn up under the day before.
5. Ever since we started running two server workers, we have sold more units of an item than we had, and its stock went negative.
6. Open question from support, no single right answer: sometimes a customer really does pay twice for one order (two separate payments, not a retry of the same one). Today the system records both and says nothing. Decide what should happen, build the smallest version of your decision, and explain what it costs in `NOTES.md`.

These reports are your scope. Like any real codebase, this one has other rough edges; if you notice one, write it down in `NOTES.md`. Fix it only if you have time left after the reports, and give it the same care: a cause, a fix and a test.

## What to do

1. **Unzip and run.** Unzip the folder we sent. It is already a git repository with one commit; keep working in it and keep its `.git` folder. Get the app running locally using the project's README.
2. **Reproduce.** For each report, find the conditions that trigger it before changing code.
3. **Fix the root cause.** Avoid band-aids such as swallowing errors, hardcoding values, or patching the symptom in the UI when the cause is elsewhere.
4. **Test.** Write an automated test for each fix that fails before your fix and passes after. Use the stack's usual test runner; add one if the project has none.
5. **Commit as you go.** One fix per commit, with its test, and a message that says what was wrong.
6. **Fill in `NOTES.md`.** It is already in the repo root, with one section per report and one for the open question. Replace every `TODO: fill in` with your own words: status, what you saw, the root cause, your fix and why, how you verified it, and the commits. If you did not fix something, mark it `not fixed` and write what you found; an honest `not fixed` counts for more than an empty section.
7. **Fill `session_logs/`.** The folder is already there with a `README.md`. Put the export of every AI session you used next to it, one file per session (see below).

## What to submit

**One zip file** of the whole project folder, sent back to us by email. Name it `<your-name>_submission.zip`. We sent you `example_submission.zip` alongside this assignment: a finished submission for a small made-up app, so you can see exactly what the folder, `NOTES.md` and `session_logs/` should look like. It is unrelated to this assignment and is an average submission, not a model answer; copy its shape, not its content.

```
<your-name>_submission.zip
└── (the project folder)
    ├── .git/             keep it: your commits are part of the submission
    ├── (the project)     your fixes and tests, committed
    ├── session_logs/     README.md + one export per AI session you used
    └── NOTES.md          every field filled in
```

- **We read `NOTES.md` first, and grading starts only if it is complete.** A `NOTES.md` with any placeholder left, or a `session_logs/` folder with no session log in it, is not graded, however good the code is. Most of the score is read from your logs.
- Include the hidden `.git` folder. On macOS, Finder's **Compress** keeps it; from a terminal, run `zip -r <your-name>_submission.zip <folder>` from the folder above the project.
- Leave out installed dependencies and build output (`node_modules/`, virtual environments, `__pycache__/`).
- Remove secrets, API keys and personal data from the logs before you zip. Remove nothing else: an edited or partial log counts as a missing one.
- Send the zip once, when you are finished.
- Work from your own investigation. We compare submissions and their session logs with each other, and a fix that appears in your code with no trace in your own logs will be asked about in the interview.

## How we evaluate

Your AI assistant can probably fix most of these problems on its own. We know, and that is fine. **We are grading you, not it.** Most of the score comes from what you type in your sessions: what you understood, what you asked, and what you did when the AI's answer needed a person.

Every submission is scored out of 100.

**Your thinking: 70 points, read from what you typed in your session logs**

| What we look for | Points | For example |
|---|---|---|
| Understanding, in your own words | 10 | You say what you think is going on, even as a guess: "so stock is taken when the order is created, not when its paid?" |
| Questions | 10 | You ask why, and what if: "what if the webhook comes 3 times" |
| Direction | 10 | You steer with decisions about this code: what to do first, what not to touch, how it should be solved |
| Response to the AI | 20 | When it asks you something, offers options, says "done", gets stuck or gets something wrong, you deal with it instead of typing "ok next" |
| Checking | 10 | You ask for proof or run it yourself: "show me the test failing on the old code first" |
| Decisions and tradeoffs | 10 | You make the calls that are yours and say why, including on the open question in the reports |

**The code you submit: 30 points**

| What we look for | Points |
|---|---|
| Fixes at the root cause. A patch that hides the symptom earns nothing for that problem and limits your overall result | 20 |
| A test per fix that fails on the original code and passes on yours | 10 |

Things worth knowing:

- **Type the way you think.** We do not score spelling, grammar, English, politeness or how long your prompts are. Short and messy is fine. A wrong guess you stated and then corrected counts for more than saying nothing.
- **Only what is about this code counts.** "Follow best practices and verify everything" earns nothing; it could be typed into any project. Pasting a prompt template earns nothing either.
- **Correct code with nothing of yours behind it does not pass.** If your logs show only "fix the bugs" and "ok", the result is held down however good the code is.
- **You do not need to fix everything.** Three problems you understood beat five the AI fixed while you watched.

We also score, your **attention** (did you follow this brief, does `NOTES.md` match the code) and **novelty** (an idea of your own that was better than the obvious one). Then we talk through your submission with you, using questions drawn from your own code and logs.

## Exporting AI session logs

Put every session you used into `session_logs/` at the repo root, from the first prompt to the last. Several files are fine. Prefer the tool's raw export (for example `.jsonl`) over a pasted summary: it shows the commands and checks you ran, which a summary loses. Menus and paths can differ between tool versions; if one below does not match yours, use your tool's own export and say which in `NOTES.md`.

| Tool | How |
|---|---|
| Claude Code | Raw (preferred): copy the `.jsonl` files from `~/.claude/projects/<your repo path with every / replaced by ->/` into `session_logs/`. Readable: type `/export session_logs/claude_session.md` in the session. |
| Codex CLI | Copy the raw `.jsonl` rollout file of each session from `~/.codex/sessions/YYYY/MM/DD/` (named `rollout-<date>-<id>.jsonl`, one per session; pick the days you worked) into `session_logs/`. |
| OpenCode | `opencode session list` to find the session ID, then `opencode session export <id> > session_logs/opencode_<id>.json`, once per session. |
| Cursor | Open the chat (history icon if it is closed), `...` menu, **Export Chat**, save into `session_logs/`. The export leaves out the agent's terminal commands and file edits, so list the commands you ran and what they showed in `NOTES.md`. |
| ChatGPT or other | Paste the full conversation into a markdown file |
| Antigravity | **Not supported.** It cannot reliably export a full session (its Export button is widely reported broken, and its own log files hold only part of a conversation). Use another tool for this assignment. |

**No paid AI plan?** OpenCode (opencode.ai) has free models: run `opencode models` and pick one whose name ends in `-free`. They are rate-limited and change from time to time; signing in with `opencode auth login` raises the limits.

NOTE: A submission would be incomplete without `session_logs/` and `NOTES.md`. We cannot grade it. Ensure those exist and are complete before you submit.
