import type { Metadata } from "next";
import { FfvApp } from "../ffv-app";

export const metadata: Metadata = {
  title: "Blind FAAB — FFV",
  description: "A private FFV blind-claim workspace with deterministic processing at 5 PM New York.",
  openGraph: { title: "Blind FAAB — FFV", description: "Private bids, finite balances, and deterministic waiver priority.", images: [] },
  twitter: { card: "summary", title: "Blind FAAB — FFV", description: "Private bids, finite balances, and deterministic waiver priority.", images: [] },
};

export default function LeaguePage() {
  return <FfvApp initialView="league" />;
}
