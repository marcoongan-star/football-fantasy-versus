# Milestone 21: observable browser-to-API readiness

The browser uses development identity headers prefixed with `X-FFV-`. The API cross-origin policy now permits exactly those headers, so browser preflight and backend authentication agree on one contract.

FFV also separates two operational questions:

- `/health` answers whether the API process can serve a request.
- `/ready` performs a lightweight database query and answers whether the process can reach its source of truth.

A deployment should receive traffic only when readiness succeeds. The endpoint reveals connection state and auth mode, but never credentials or a database address.
