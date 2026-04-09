"use client";

import dynamic from "next/dynamic";

const BelowFold = dynamic(() => import("./below-fold"), {
  ssr: false,
  loading: () => <div className="min-h-screen" />,
});

export default function LazyBelowFold() {
  return <BelowFold />;
}
