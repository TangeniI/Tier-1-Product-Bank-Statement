import { NextRequest, NextResponse } from "next/server";
import { ENGINE_URL } from "@/lib/engine";

// Proxy (possibly user-edited) rows to the engine and stream back the file.
export const runtime = "nodejs";
// Render's free engine cold-starts (~50s after idle); allow the proxy to wait.
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const payload = await req.text();

  let res: Response;
  try {
    res = await fetch(`${ENGINE_URL}/export`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: payload,
    });
  } catch {
    return NextResponse.json(
      { detail: "Export engine is unavailable." },
      { status: 502 },
    );
  }

  if (!res.ok) {
    const text = await res.text();
    return new NextResponse(text, { status: res.status });
  }

  // Pass through the file bytes + download headers.
  const buf = await res.arrayBuffer();
  return new NextResponse(buf, {
    status: 200,
    headers: {
      "content-type":
        res.headers.get("content-type") ?? "application/octet-stream",
      "content-disposition":
        res.headers.get("content-disposition") ?? "attachment",
    },
  });
}

export async function GET() {
  // Surface available presets to the client (for the dropdown).
  try {
    const res = await fetch(`${ENGINE_URL}/presets`);
    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return NextResponse.json([], { status: 200 });
  }
}
