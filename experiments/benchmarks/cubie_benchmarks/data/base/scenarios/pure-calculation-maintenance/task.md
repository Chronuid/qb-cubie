# pure-calculation: maintenance

net_total(rows) returns integer net cents of enabled rows. Each row is (enabled:bool, cents:int, discount:int), with nonnegative cents and discounts. Ignore disabled rows. Discounts may now exceed cents; clamp each enabled row net amount to zero before summing. Each input has its own expected result; empty input returns 0 and integers beyond binary float precision must remain exact.

Public API: `net_amount.net_total(rows)`. Preserve the input material. Deliver production code, executable tests and a short README. Submit tests before implementation; demonstrate business red, then green, then refactor without weakening the frozen tests. Return types and the complete specified output tree are part of acceptance.
