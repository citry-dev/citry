"use client";

import Form from "next/form";
import { useState } from "react";

export default function Search() {
  // The text typed so far, which the line under the field repeats.
  const [query, setQuery] = useState("");
  return (
    <Form action="/" role="search">
      <input type="search" name="q" value={query} onChange={(event) => setQuery(event.target.value)} />
      <button type="submit">Search</button>
      <p>Searching for: {query}</p>
    </Form>
  );
}
