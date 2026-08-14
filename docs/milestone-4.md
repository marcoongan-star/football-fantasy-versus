# Milestone 4 — interactive public draft preview

The no-login recruiter demo now includes a resettable snake-draft room using seeded players and four example managers.

- Each selection disappears from the available-player pool.
- The next manager is derived from the same alternating-round rule as the backend.
- Round two visibly reverses the seat order.
- The preview is device-local and resets on refresh; it never claims to be a live private league.
- The production draft remains protected by the transactional FastAPI state machine from Milestone 3.

The preview deliberately keeps its sample records beside the React component so the names, clubs, positions, and managers are easy for a new contributor to edit.
