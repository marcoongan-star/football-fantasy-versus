import type { Metadata } from "next";
import { FfvApp } from "../ffv-app";

export const metadata: Metadata = {
  title: "Draft Room — FFV",
  description: "A server-authoritative FFV snake-draft room with reconnect-safe state.",
  openGraph: { title: "Draft Room — FFV", description: "Snake order, accepted picks, and reconnect-safe state.", images: [] },
  twitter: { card: "summary", title: "Draft Room — FFV", description: "Snake order, accepted picks, and reconnect-safe state.", images: [] },
};

export default function DraftPage() {
  return <FfvApp initialView="draft" />;
}
