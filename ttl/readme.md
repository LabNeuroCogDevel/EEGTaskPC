## Cron
Scheduled automatic notifications are delivered through slack using `foranw@rhea`'s `cron`
```
8 0 * * * lpt_timing.py newest|column -ts$'\t' | sed '1s/^/```/;$s/$/```/' | slack-msg eeg-notifications
```
