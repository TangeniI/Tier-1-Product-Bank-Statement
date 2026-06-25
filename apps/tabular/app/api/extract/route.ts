import { NextRequest, NextResponse } from "next/server";
import { ENGINE_URL, engineHeaders } from "@/lib/engine";

// Proxy the upload to the FastAPI engine. Keeps the engine URL server-side and
// gives us one place to later enforce auth/usage limits before extraction.
export const runtime = "nodejs";
// Render's free engine cold-starts (~50s after idle); allow the proxy to wait.
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const file = form.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ detail: "No file uploaded." }, { status: 400 });
  }

  const upstream = new FormData();
  upstream.append("file", file, file.name || "statement.pdf");

  let res: Response;
  try {
    res = await fetch(`${ENGINE_URL}/extract`, {
      method: "POST",
      body: upstream,
      headers: engineHeaders(),
    });
  } catch {
    return NextResponse.json(
      { detail: "Extraction engine is unavailable. Is it running?" },
      { status: 502 },
    );
  }

  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "content-type": "application/json" },
  });
}
