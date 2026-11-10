# Review: warehouse

warehouse.available(rows) returns integer available units of active inventory only: sum(units - reserved) for active rows. Inputs have 0 <= reserved <= units. Inactive stock must not contribute; empty input returns 0.

Review the current source without modifying it. Evaluate criterion `active_stock`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
