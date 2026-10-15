import BoardClient from "./board-client.jsx";
import {browserSnapshot, csrfFor, ensure, snapshot} from "../scenario/node_model.mjs";

export const dynamic = "force-dynamic";

export default async function Page({searchParams}) {
  const params = await searchParams;
  const count = Number(params?.count || 14);
  const session = String(params?.session || "manual");
  ensure(session, count);
  return <BoardClient initialBoard={browserSnapshot(snapshot(session))}
    session={session} csrf={csrfFor(session)} />;
}
