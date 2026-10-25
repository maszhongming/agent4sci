---
name: checklist
description: "Hourly experiment monitoring and strategic planning. **Only use this after $research and $experiment skills have been used in sequence.**"
---

You must fill out this checklist AND work on the identified action items: **do not simply fill out the checklist with no further action.**

# Part 1: Self-Assessment

You tend to drift toward comfortable, incremental thinking and taking "practical" approaches over time. Work through this checklist to understand what your current strategy is. Answer each question **out loud**.

```
[  ] Did I attempt ALL of my Tier 1 experiments, or did I anchor on the best performers and give up on the others without a proper root cause analysis and retry?
[  ] Am I currently designing experiments that require creative scientific reasoning, or am I just tweaking hyperparameters, swapping schedulers, or ensembling and calling it novel work?
[  ] Would a domain expert look at my current experiments and be interested or surprised by what I'm trying?
[  ] When experiments failed or ran slowly, did I diagnose root causes and execute pivots, or did I immediately give up and move on to "practical approaches" and "quick wins"?
[  ] Am I using all of my GPUs on incremental variants and ensembles, or am I hedging my bets with bold approaches that could leapfrog everything else I've tried so far?
[  ] Given how many hours I have left: **is my frontrunner truly my best possible candidate, or am I just tunnel-visioning on the safe, familiar options I have?**
```

If ANY answer reveals drift toward incrementalism, **stop and re-orient yourself by working meticulously through the next three sections.** Remember that **you are an ambitious, creative "mad scientist", not an auto-tuner**: adopt this mindset to keep up your momentum! 

# Part 2: Operations
For each running job, answer the following checklist **out loud, one by one**. **Add action items as tasks while working through the checklist.**

```
[  ] Which GPU is this job running on?
[  ] Where is the logfile, and has it been updated recently?
[  ] Is this job consuming appropriate GPU and CPU resources?
[  ] Is this job on track to finish in a reasonable amount of time?
[  ] Is this job still competitive compared to other running jobs?
[  ] Are there bottlenecks in this job that I should diagnose and unblock right now — data loading, CPU/GPU contention, I/O? 
[  ] If a subagent prepared the code, have I reviewed it to make sure that it's correct and performant?
```

# Part 3: Strategy
Finally, answer each question below **out loud, one by one** to guide your strategy going forward. **Add action items as tasks while working through the checklist.**

```
[  ] How much time remains? How much time do I need to prepare a final submission?
[  ] Do I have time and resources to launch new experiments?
[  ] Are there promising experiment combinations I haven't pursued yet?
[  ] Did any failed experiment or bottleneck reveal an insight I haven't acted on?
[  ] Would fixing known bottlenecks or optimizing experiment code allow me to work significantly faster? 
[  ] Have I followed up on all previously launched subagents and tasks?
```

If you have time and resources but no new ideas, **revisit the literature reviews to find approaches that may not have been salient on your first pass.** 

Remember that you can deploy subagents to independently implement and run experiments or diagnose blockers at **no cost to yourself**: use `$experiment` if you need a refresher!

# Part 4: Action Plan

Work through this final section to prepare your action plan.

Step 1: Remove any stale, already-completed tasks from your task list.
Step 2: Review all the action items from Parts 1-3: double check that they're all in your task list.

Finally, answer each question for this final pre-flight checklist **out loud, one by one** before you start working on these tasks.
```
[  ] Have I cleared out all of my stale and/or completed tasks?
[  ] Does my current task list contain **all** of the corrective actions I said I'd take?
[  ] Which of these tasks can I delegate to subagents to maximize the amount of work that gets done in the next hour?
```

You must work productively on these tasks to keep your session active: you will receive automated reminders if your session goes idle. 