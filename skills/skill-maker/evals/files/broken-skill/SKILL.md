---
name: Weekly_Log_Summary
description: Summarizes <error logs> into a weekly report.
author: jordan
version: "0.1"
---

# Weekly Log Summary

Pull the week's error logs, group them by service, count the most frequent
errors, and write a short summary for the team.

## Steps

1. Collect the raw log lines for the last 7 days.
2. Group the lines by the originating service.
3. Count occurrences and keep the top 10 recurring errors.
4. Write a short plain-text summary: total error count, the top 10 with counts,
   and any service that spiked versus the prior week.
