---
description: 'Materialise no-tracking EF reads as arrays; List only when the collection is mutated'
globs: "**/*.cs"
paths:
  - "**/*.cs"
applyTo: '**/*.cs'
alwaysApply: false
---

# Read-only collections vs List

Updated: 2026-09-13

## Non-Negotiables

- **`AsNoTracking()` materialisation is an array.** Use `ToArrayAsync` / `ToArray`, typed as `T[]`. A `List<T>` signals the collection will grow; a no-tracking query does not.
- **`List<T>` only when you `Add` / `Remove` / mutate.** Building a result by appending is a list. A filtered projection of an already-loaded array is another array (`ToArray`), not `ToList`.
- **Do not declare `List<T>` for a value that is never mutated** even if it did not come from EF — prefer `T[]` or `IReadOnlyList<T>` so the type states the contract.

```csharp
// Yes — no-tracking read, never mutated
Item[] items = await db.Items
    .AsNoTracking()
    .ToArrayAsync(cancellationToken);

// Yes — this collection is appended to
var historical = new List<ExportBody>();
historical.Add(body);

// No — List on a frozen query result
List<Item> items = await db.Items
    .AsNoTracking()
    .ToListAsync(cancellationToken);
```

## Changelog

> AI loading note: Skip this section during routine task execution. Use it only when updating this rule file.

| Date | Change |
|:-----|:-------|
| 2026-09-13 | Copied from smooth-ai-product-context-memory; examples genericised. |
