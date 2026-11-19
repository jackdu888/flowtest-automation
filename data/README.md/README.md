# Physical hydrotest readings

After a real hydrostatic test, drop the gauge readings here as CSV:

```
data/hydrotest/<system>-<YYYY-MM-DD>.csv
component,measured_peak_bar,held_minutes,leak
cv-102,15.2,30,none
```

The next sweep diffs these against the simulated peaks, recalibrates the
safety factors, and notes the delta in the test pack.
