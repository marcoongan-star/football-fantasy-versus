import type { Metadata } from "next";
import { LeagueDemo } from "./league-demo";

export const metadata: Metadata = {
  title: "FFV — Football Fantasy Versus",
  description:
    "A transparent fantasy-football platform with a separate, reproducible career simulation.",
};

export default function Home() {
  return <LeagueDemo />;
}

