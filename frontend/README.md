# FFV web

The recruiter-facing React and TypeScript interface for Football Fantasy Versus.

The current public route is a seeded, no-login demonstration. Private league commands belong to the FastAPI domain service; Google session verification is connected at the deployment milestone.

## Easy edit map

- Change page text and demo records in `app/league-demo.tsx`.
- Change the seeded draft managers and players at the top of `app/league-demo.tsx`.
- Change colors, type, spacing, and mobile layout in `app/globals.css`.
- Change the page title or sharing preview in `app/layout.tsx` and `public/og.jpg`.
- Keep private league rules in the backend rather than copying them into browser code.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm test
```
