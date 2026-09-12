import type { Metadata } from "next";
import { FfvApp } from "./ffv-app";

export const metadata: Metadata = {
  title: "League Workspace — FFV",
  description: "A private FFV league workspace for drafts, transparent scoring, and reproducible career fixtures.",
  openGraph: { title: "League Workspace — FFV", description: "Private league operations and reproducible career mode.", images: [] },
  twitter: { card: "summary", title: "League Workspace — FFV", description: "Private league operations and reproducible career mode.", images: [] },
};

export default function AppPage() {
  return <FfvApp />;
}
