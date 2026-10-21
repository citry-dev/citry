"use client";

import { createContext, type ReactNode } from "react";

// The board's name, which every card reads without taking it as a prop.
export const BoardContext = createContext("");

// The page is a server component, which cannot provide a context itself, so
// it wraps the board in this client component, as Next.js's docs show.
export default function BoardProvider({ children }: { children: ReactNode }) {
  return <BoardContext.Provider value="Projects">{children}</BoardContext.Provider>;
}
