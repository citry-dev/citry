// Server-side data for the page. Server components and the server action
// read it; client components import only its types.

export type Owner = { name: string };

// The page draws a featured project's card with the accent border.
export type Project = { title: string; count: number; featured?: boolean };

export const owner: Owner = { name: "Ada" };

export const projects: Project[] = [
  { title: "Alpha", count: 3, featured: true },
  { title: "Beta", count: 5 },
  { title: "Gamma", count: 8 },
];

// The saved total lives in server memory, so the dev server shows the stored
// total on a reload.
export const state = { count: 0 };

// Read from .env and held here only so the value exists on the server. Its
// name has no NEXT_PUBLIC_ prefix, so Next.js leaves it out of the browser's
// JavaScript; it must still never be passed to or read in a client component.
export const secretToken = process.env.SECRET_TOKEN;
