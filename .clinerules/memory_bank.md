# Memory Bank System Instructions

You operate with a persistent Memory Bank located in the `memory-bank/` directory. You must read these files at the beginning of every session to establish context, and update them at the end of every major task.

## The Memory Files
1. projectbrief.md: High-level overview, objectives, and scope.
2. productContext.md: User experience goals, product requirements, and system design.
3. activeContext.md: The current state of development, active task details, and recent changes.
4. progress.md: Complete checklist of feature sets (Done, In Progress, Future).

## Core Protocol
- **First Step**: Before performing any code edits or reading complex files, read all files in `memory-bank/` to align your technical context.
- **Continuous Tracking**: When a task changes the architecture, adds a major feature, or shifts the project status, update `activeContext.md` and `progress.md`.
- **Final Step**: Before completing a task, ensure the memory files accurately reflect the absolute state of the repository. Do not leave the session without logging progress.
