"use server";

import { state } from "./data";

// Server action the Add button calls; it returns the new total so the
// client can show it without reloading the page.
export async function save(payload: { amount: number }): Promise<number> {
  state.cuont += payload.amount;
  return state.count;
}
