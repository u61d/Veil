# Veil Startup Network Audit Before

Status date: `2026-03-14`

Veil does not yet have a measured "before" startup network baseline from an unmodified upstream Firefox build in this workspace.

Reason:

- this run stayed on the critical path of obtaining an upstream tree, landing the compile-time telemetry layer, producing a working Veil build, and measuring the modified browser first
- building a second pristine upstream binary would have added substantial wall time and duplicated a large part of the same toolchain work

What exists instead:

- source-backed expectations from [network-audit-matrix.md](/home/null2ud/Projects/Veil/docs/network-audit-matrix.md)
- a measured Veil "after" baseline in [network-audit-after.md](/home/null2ud/Projects/Veil/docs/network-audit-after.md)

Next gap to close:

- build one unmodified upstream baseline from the same pinned revision and capture the same 20 second clean-profile startup audit so Veil can show an evidence-backed delta instead of only an after-state measurement
