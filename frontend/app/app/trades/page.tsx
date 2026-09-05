import type { Metadata } from "next";

import { FfvApp } from "../ffv-app";

export const metadata: Metadata = {
  title: "Trade Room — FFV",
  description: "Walk through recipient consent, commissioner approval, and event-derived roster ownership.",
};

export default function TradeRoomPage() {
  return <FfvApp initialView="trades" />;
}
